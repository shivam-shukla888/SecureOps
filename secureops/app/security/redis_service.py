import logging
from typing import Optional, List, Any
import httpx
from app.config import settings

logger = logging.getLogger(__name__)


class RedisService:
    """
    Centralized, thread-safe, reusable Redis service for SecureOps Gateway.
    Supports Upstash Redis REST API (via HTTPX connection pool) and standard remote Redis URL.
    Never exposes credentials or tokens in logs.
    """

    def __init__(
        self,
        rest_url: Optional[str] = None,
        rest_token: Optional[str] = None,
        redis_url: Optional[str] = None,
    ):
        if redis_url is not None and rest_url is None:
            raw_rest_url = ""
            raw_rest_token = ""
            raw_redis_url = redis_url
        else:
            raw_rest_url = rest_url if rest_url is not None else settings.UPSTASH_REDIS_REST_URL
            raw_rest_token = rest_token if rest_token is not None else settings.UPSTASH_REDIS_REST_TOKEN
            raw_redis_url = redis_url if redis_url is not None else settings.REDIS_URL

        self._rest_url = (raw_rest_url or "").strip("\"' \t\r\n").rstrip("/")
        self._rest_token = (raw_rest_token or "").strip("\"' \t\r\n")
        self._redis_url = (raw_redis_url or "").strip("\"' \t\r\n")
        self._http_client: Optional[httpx.AsyncClient] = None
        self._redis_py_client = None

    def _get_http_client(self) -> httpx.AsyncClient:
        if self._http_client is None or self._http_client.is_closed:
            headers = {
                "Authorization": f"Bearer {self._rest_token}",
                "Content-Type": "application/json",
            }
            self._http_client = httpx.AsyncClient(
                headers=headers,
                timeout=5.0,
            )
        return self._http_client

    async def _execute_upstash_cmd(self, cmd: List[Any]) -> Any:
        client = self._get_http_client()
        response = await client.post(self._rest_url, json=cmd)
        response.raise_for_status()
        data = response.json()
        if "error" in data and data["error"]:
            raise RuntimeError(f"Upstash Redis Error: {data['error']}")
        return data.get("result")

    async def _execute_upstash_pipeline(self, commands: List[List[Any]]) -> List[Any]:
        client = self._get_http_client()
        pipeline_url = f"{self._rest_url}/pipeline"
        response = await client.post(pipeline_url, json=commands)
        response.raise_for_status()
        results_data = response.json()

        results = []
        for item in results_data:
            if isinstance(item, dict) and "error" in item and item["error"]:
                raise RuntimeError(f"Upstash Redis Pipeline Error: {item['error']}")
            elif isinstance(item, dict) and "result" in item:
                results.append(item["result"])
            else:
                results.append(item)
        return results

    async def _get_redis_py(self):
        if self._redis_py_client is None:
            import redis.asyncio as redis
            self._redis_py_client = redis.from_url(self._redis_url, socket_timeout=3.0)
        return self._redis_py_client

    @property
    def is_upstash(self) -> bool:
        return bool(self._rest_url and self._rest_token)

    @property
    def is_configured(self) -> bool:
        if self.is_upstash:
            return True
        is_remote = bool(self._redis_url and self._redis_url != "redis://localhost:6379/0")
        if is_remote:
            return True
        # In development only, allow localhost default for local debugging
        if str(getattr(settings, "ENVIRONMENT", "development")).lower() != "production":
            return bool(self._redis_url)
        return False

    async def ping(self) -> bool:
        """Executes PING and returns True if Redis responds with PONG."""
        try:
            if self.is_upstash:
                res = await self._execute_upstash_cmd(["PING"])
                return str(res).upper() == "PONG"
            elif self.is_configured:
                r = await self._get_redis_py()
                return bool(await r.ping())
            else:
                return False
        except Exception as exc:
            logger.warning(f"Redis ping check failed ({type(exc).__name__})")
            return False

    async def get(self, key: str) -> Optional[str]:
        """Retrieves key value from Redis."""
        try:
            if self.is_upstash:
                res = await self._execute_upstash_cmd(["GET", key])
                return str(res) if res is not None else None
            elif self.is_configured:
                r = await self._get_redis_py()
                val = await r.get(key)
                return val.decode("utf-8") if isinstance(val, bytes) else val
            return None
        except Exception as exc:
            logger.warning(f"Redis GET failed for key '{key}': {exc}")
            return None

    async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """Sets key value in Redis with optional expiration in seconds."""
        try:
            cmd = ["SET", key, value]
            if ex and ex > 0:
                cmd.extend(["EX", str(ex)])
            if self.is_upstash:
                res = await self._execute_upstash_cmd(cmd)
                return str(res).upper() == "OK"
            elif self.is_configured:
                r = await self._get_redis_py()
                return bool(await r.set(key, value, ex=ex))
            return False
        except Exception as exc:
            logger.warning(f"Redis SET failed for key '{key}': {exc}")
            return False

    async def delete(self, key: str) -> bool:
        """Deletes key from Redis."""
        try:
            if self.is_upstash:
                res = await self._execute_upstash_cmd(["DEL", key])
                return int(res or 0) > 0
            elif self.is_configured:
                r = await self._get_redis_py()
                return bool(await r.delete(key))
            return False
        except Exception as exc:
            logger.warning(f"Redis DEL failed for key '{key}': {exc}")
            return False

    async def exists(self, key: str) -> bool:
        """Checks if key exists in Redis."""
        try:
            if self.is_upstash:
                res = await self._execute_upstash_cmd(["EXISTS", key])
                return int(res or 0) > 0
            elif self.is_configured:
                r = await self._get_redis_py()
                return bool(await r.exists(key))
            return False
        except Exception as exc:
            logger.warning(f"Redis EXISTS failed for key '{key}': {exc}")
            return False

    async def incr(self, key: str, amount: int = 1) -> int:
        """Atomically increments integer key value by amount."""
        try:
            if self.is_upstash:
                cmd = ["INCRBY", key, str(amount)] if amount != 1 else ["INCR", key]
                res = await self._execute_upstash_cmd(cmd)
                return int(res)
            elif self.is_configured:
                r = await self._get_redis_py()
                return int(await r.incrby(key, amount))
            raise RuntimeError("Redis is not configured.")
        except Exception as exc:
            logger.warning(f"Redis INCR failed for key '{key}': {exc}")
            raise exc

    async def expire(self, key: str, seconds: int) -> bool:
        """Sets TTL expiration in seconds on key."""
        try:
            if self.is_upstash:
                res = await self._execute_upstash_cmd(["EXPIRE", key, str(seconds)])
                return int(res or 0) > 0
            elif self.is_configured:
                r = await self._get_redis_py()
                return bool(await r.expire(key, seconds))
            return False
        except Exception as exc:
            logger.warning(f"Redis EXPIRE failed for key '{key}': {exc}")
            return False

    async def pipeline_execute(self, commands: List[List[Any]]) -> List[Any]:
        """Executes a batch pipeline of Redis commands atomically."""
        if not commands:
            return []
        try:
            if self.is_upstash:
                return await self._execute_upstash_pipeline(commands)
            elif self.is_configured:
                r = await self._get_redis_py()
                pipe = r.pipeline()
                for cmd in commands:
                    name = str(cmd[0]).lower()
                    args = cmd[1:]
                    method = getattr(pipe, name)
                    method(*args)
                return await pipe.execute()
            raise RuntimeError("Redis is not configured.")
        except Exception as exc:
            logger.warning(f"Redis pipeline execution failed: {exc}")
            raise exc

    async def close(self):
        """Closes active HTTP and Redis client connections."""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
            self._http_client = None
        if self._redis_py_client:
            await self._redis_py_client.close()
            self._redis_py_client = None


redis_service = RedisService()
