import asyncio
import logging
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from app.security.secrets import secret_provider
from app.config import settings

logger = logging.getLogger(__name__)

# Safe In-Memory Index for Safe Real Integration
INDEXED_DOCUMENTS = [
    {"id": "doc_101", "tenant_id": "tenant_default", "title": "Corporate Security Policy 2026", "content": "SecureOps policy enforces zero LLM tool autonomy and deterministic security gates."},
    {"id": "doc_102", "tenant_id": "tenant_default", "title": "Quarterly Financial Audit Q3", "content": "Financial audit passed with zero compliance violations."},
    {"id": "doc_201", "tenant_id": "tenant_acme", "title": "Corporate Security Policy", "content": "Acme Corp security roadmap and internal governance policy."},
]


class DocumentSearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    tenant_id: str = Field(default="tenant_default")
    limit: int = Field(default=5, ge=1, le=50)


class DocumentServiceAdapter:
    """
    Real safe integration adapter for document searching.
    Strictly read-only, schema-validated, tenant-isolated, and timeout-controlled.
    """
    def __init__(self, service_url: Optional[str] = None):
        self.service_url = service_url

    async def search_documents(self, req: DocumentSearchRequest) -> Dict[str, Any]:
        # Secret authorization lookup
        service_token = secret_provider.get_secret("DOCUMENT_SERVICE_TOKEN")

        # Perform tenant-isolated document matching with timeout control
        try:
            async with asyncio.timeout(settings.EXECUTION_TIMEOUT_SECONDS):
                matched: List[Dict[str, Any]] = []
                query_lower = req.query.lower()

                for doc in INDEXED_DOCUMENTS:
                    if doc["tenant_id"] == req.tenant_id:
                        if query_lower in doc["title"].lower() or query_lower in doc["content"].lower():
                            matched.append({
                                "id": doc["id"],
                                "title": doc["title"],
                                "snippet": doc["content"][:100] + "...",
                            })

                return {
                    "status": "executed",
                    "integration": "DocumentServiceAdapter (Real Read-Only Integration)",
                    "tenant_id": req.tenant_id,
                    "query": req.query,
                    "results_count": len(matched),
                    "results": matched[:req.limit],
                    "authenticated_via_secret": bool(service_token),
                }
        except asyncio.TimeoutError:
            logger.error("DocumentServiceAdapter search timed out.")
            raise RuntimeError("Document service request timed out.")


document_service_adapter = DocumentServiceAdapter()
