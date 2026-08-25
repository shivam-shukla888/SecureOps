import json
import logging
import asyncio
from abc import ABC, abstractmethod
from typing import List, Optional
import httpx

from app.audit.security_events import SecurityEvent
from app.audit.logger import redact_sensitive_data

logger = logging.getLogger(__name__)


class SIEMExporter(ABC):
    @abstractmethod
    async def export_event(self, event: SecurityEvent) -> None:
        pass


class ConsoleSIEMExporter(SIEMExporter):
    async def export_event(self, event: SecurityEvent) -> None:
        payload = redact_sensitive_data(event.to_dict())
        log_json = json.dumps({"event_category": "SIEM_SECURITY_EVENT", **payload})
        logger.info(f"SIEM Console Export: {log_json}")


class WebhookSIEMExporter(SIEMExporter):
    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url

    async def export_event(self, event: SecurityEvent) -> None:
        if not self.webhook_url:
            return
        payload = redact_sensitive_data(event.to_dict())
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                await client.post(self.webhook_url, json=payload)
        except Exception as exc:
            logger.warning(f"Failed to export SIEM event to webhook: {exc}")


class SIEMManager:
    def __init__(self, exporters: Optional[List[SIEMExporter]] = None):
        self.exporters = exporters or [ConsoleSIEMExporter()]
        self.event_history: List[SecurityEvent] = []

    def register_exporter(self, exporter: SIEMExporter):
        self.exporters.append(exporter)

    async def record_security_event(self, event: SecurityEvent):
        self.event_history.append(event)
        for exporter in self.exporters:
            try:
                # Dispatch without blocking main request pipeline
                asyncio.create_task(exporter.export_event(event))
            except Exception as exc:
                logger.error(f"Error invoking SIEM exporter: {exc}")

    def list_tenant_security_events(self, tenant_id: str, limit: int = 50) -> List[dict]:
        results = [e.to_dict() for e in self.event_history if e.tenant_id == tenant_id]
        return results[-limit:]


siem_manager = SIEMManager()
