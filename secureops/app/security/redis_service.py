import logging
from typing import Optional, List, Any
import httpx
from app.config import settings

logger = logging.getLogger(__name__)


class RedisService:
    """
    Centralized, thread-safe, reusable Redis service for SecureOps Gateway.
    Supports Upstash Redis REST API (via HTTPX connection pool) and standard Redis URL fallback.
    """

    def __init__(
        self,
        rest_url: Optional[str] = None,
        rest_token: Optional[str] = None,
        redis_url: Optional[str] = None,
    ):
        if redis_url is not None:
            self._rest_url = (rest_url or "").strip()
            self._rest_token = (rest_token or "").strip()
            self._redis_url = redis_url.strip()
        else:
            self._rest_url = (rest_url if rest_url is not None else settings.UPSTASH_REDIS_REST_URL).strip()
            self._rest_token = (rest_token if rest_token is not None else settings.UPSTASH_REDIS_REST_TOKEN).strip()
            self._redis_url = (redis_url if redis_url is not None else settings.REDIS_URL).strip()
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
        pipeline_url = f"{self._rest_url.rstrip('/')}/pipeline"
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
    def is_configured(self) -> bool:
        has_upstash = bool(self._rest_url and self._rest_token)
        has_redis_py = bool(self._redis_url and self._redis_url != "redis://localhost:6379/0")
        return has_upstash or has_redis_py

    async def ping(self) -> bool:
        """Executes PING and returns True if Redis responds with PONG."""
        try:
            if self._rest_url and self._rest_token:
                res = await self._execute_upstash_cmd(["PING"])
                return str(res).upper() == "PONG"
            else:
                r = await self._get_redis_py()
                return bool(await r.ping())
        except Exception as exc:
            logger.warning(f"Redis ping check failed ({type(exc).__name__})")
            return False

    async def get(self, key: str) -> Optional[str]:
        """Retrieves key value from Redis."""
        try:
            if self._rest_url and self._rest_token:
                res = await self._execute_upstash_cmd(["GET", key])
                return str(res) if res is not None else None
            else:
                r = await self._get_redis_py()
                val = await r.get(key)
                return val.decode("utf-8") if isinstance(val, bytes) else val
        except Exception as exc:
            logger.warning(f"Redis GET failed for key '{key}': {exc}")
            return None

    async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """Sets key value in Redis with optional expiration in seconds."""
        try:
            cmd = ["SET", key, value]
            if ex and ex > 0:
                cmd.extend(["EX", str(ex)])
            if self._rest_url and self._rest_token:
                res = await self._execute_upstash_cmd(cmd)
                return str(res).upper() == "OK"
            else:
                r = await self._get_redis_py()
                return bool(await r.set(key, value, ex=ex))
        except Exception as exc:
            logger.warning(f"Redis SET failed for key '{key}': {exc}")
            return False

    async def delete(self, key: str) -> bool:
        """Deletes key from Redis."""
        try:
            if self._rest_url and self._rest_token:
                res = await self._execute_upstash_cmd(["DEL", key])
                return int(res or 0) > 0
            else:
                r = await self._get_redis_py()
                return bool(await r.delete(key))
        except Exception as exc:
            logger.warning(f"Redis DEL failed for key '{key}': {exc}")
            return False

    async def exists(self, key: str) -> bool:
        """Checks if key exists in Redis."""
        try:
            if self._rest_url and self._rest_token:
                res = await self._execute_upstash_cmd(["EXISTS", key])
                return int(res or 0) > 0
            else:
                r = await self._get_redis_py()
                return bool(await r.exists(key))
        except Exception as exc:
            logger.warning(f"Redis EXISTS failed for key '{key}': {exc}")
            return False

    async def incr(self, key: str, amount: int = 1) -> int:
        """Atomically increments integer key value by amount."""
        try:
            if self._rest_url and self._rest_token:
                cmd = ["INCRBY", key, str(amount)] if amount != 1 else ["INCR", key]
                res = await self._execute_upstash_cmd(cmd)
                return int(res)
            else:
                r = await self._get_redis_py()
                return int(await r.incrby(key, amount))
        except Exception as exc:
            logger.warning(f"Redis INCR failed for key '{key}': {exc}")
            raise exc

    async def expire(self, key: str, seconds: int) -> bool:
        """Sets TTL expiration in seconds on key."""
        try:
            if self._rest_url and self._rest_token:
                res = await self._execute_upstash_cmd(["EXPIRE", key, str(seconds)])
                return int(res or 0) > 0
            else:
                r = await self._get_redis_py()
                return bool(await r.expire(key, seconds))
        except Exception as exc:
            logger.warning(f"Redis EXPIRE failed for key '{key}': {exc}")
            return False

    async def pipeline_execute(self, commands: List[List[Any]]) -> List[Any]:
        """Executes a batch pipeline of Redis commands atomically."""
        if not commands:
            return []
        try:
            if self._rest_url and self._rest_token:
                return await self._execute_upstash_pipeline(commands)
            else:
                r = await self._get_redis_py()
                pipe = r.pipeline()
                for cmd in commands:
                    name = str(cmd[0]).lower()
                    args = cmd[1:]
                    method = getattr(pipe, name)
                    method(*args)
                return await pipe.execute()
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
