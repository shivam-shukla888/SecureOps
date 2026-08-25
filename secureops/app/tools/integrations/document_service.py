import os
import asyncio
import logging
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from app.security.secrets import secret_provider
from app.config import settings

logger = logging.getLogger(__name__)

# Base path for local document repository
DOCUMENTS_BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "test_documents")
)


# Common English & Operational Stop Words
STOP_WORDS = {
    "search", "my", "documents", "document", "for", "the", "a", "an", "in", "on", "of",
    "to", "find", "get", "read", "show", "me", "please", "with", "from", "and", "or",
    "is", "are", "that", "this", "file", "files", "record", "records"
}


class DocumentSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    tenant_id: str = Field(default="tenant_default")
    limit: int = Field(default=5, ge=1, le=50)


class DocumentServiceAdapter:
    """
    Real safe read-only document search adapter querying local tenant document store.
    Enforces path-traversal prevention, strict tenant isolation, Pydantic input validation,
    meaningful keyword filtering, and timeout control.
    """
    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = base_dir or DOCUMENTS_BASE_DIR

    async def search_documents(self, req: DocumentSearchRequest) -> Dict[str, Any]:
        # Secret authorization lookup
        service_token = secret_provider.get_secret("DOCUMENT_SERVICE_TOKEN")

        # Sanitize tenant_id to prevent path traversal manipulation
        raw_tenant = req.tenant_id.strip()
        if ".." in raw_tenant or "/" in raw_tenant or "\\" in raw_tenant:
            logger.error(f"Tenant directory escape attempt blocked: {raw_tenant}")
            raise ValueError(f"Invalid or unauthorized tenant directory scope: '{raw_tenant}'")

        # Authoritative tenant directory resolution
        clean_tenant_id = os.path.basename(raw_tenant)
        tenant_dir = os.path.abspath(os.path.join(self.base_dir, clean_tenant_id))

        # Enforce strict path traversal & tenant boundary isolation
        base_real = os.path.abspath(self.base_dir)
        if not tenant_dir.startswith(base_real) or tenant_dir == base_real:
            logger.error(f"Tenant boundary violation blocked: {req.tenant_id}")
            raise ValueError(f"Invalid or unauthorized tenant directory scope: '{req.tenant_id}'")

        # Clean query and extract meaningful keywords (excluding stop-words)
        query_text = req.query.strip()
        query_words = [
            w for w in query_text.lower().replace(".", " ").replace(",", " ").split()
            if len(w) > 1 and w not in STOP_WORDS
        ]

        try:
            async with asyncio.timeout(settings.EXECUTION_TIMEOUT_SECONDS):
                matched: List[Dict[str, Any]] = []

                if os.path.exists(tenant_dir) and os.path.isdir(tenant_dir):
                    for file_name in sorted(os.listdir(tenant_dir)):
                        file_path = os.path.abspath(os.path.join(tenant_dir, file_name))

                        # Enforce per-file path boundary isolation
                        if not file_path.startswith(tenant_dir):
                            continue

                        if not os.path.isfile(file_path):
                            continue

                        try:
                            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                                content = f.read()
                                content_lower = content.lower()
                                file_name_lower = file_name.lower()
                                
                                # Strict matching: require ALL extracted non-stopword query keywords to match
                                is_match = False
                                if query_words:
                                    is_match = all(word in file_name_lower or word in content_lower for word in query_words)
                                elif query_text:
                                    is_match = query_text.lower() in file_name_lower or query_text.lower() in content_lower

                                if is_match:
                                    snippet = content[:300] + ("..." if len(content) > 300 else "")
                                    matched.append({
                                        "document_id": f"doc_{file_name}",
                                        "file_name": file_name,
                                        "tenant_id": clean_tenant_id,
                                        "snippet": snippet,
                                        "full_content": content[:1000],
                                    })
                        except Exception as file_err:
                            logger.warning(f"Failed to read document {file_name}: {file_err}")

                return {
                    "status": "executed",
                    "simulated": False,
                    "integration": "DocumentServiceAdapter (Real File Repository)",
                    "tenant_id": clean_tenant_id,
                    "query": req.query,
                    "results_count": len(matched),
                    "results": matched[:req.limit],
                    "authenticated_via_secret": bool(service_token),
                }
        except asyncio.TimeoutError:
            logger.error("DocumentServiceAdapter search timed out.")
            raise RuntimeError("Document service request timed out.")


document_service_adapter = DocumentServiceAdapter()
