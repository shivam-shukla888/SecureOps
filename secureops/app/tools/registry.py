import logging
from typing import Dict, Optional, Any

from app.schemas.decision import IntentEnum, RiskEnum
from app.tools.base import ToolDefinition
from app.tools.schemas import (
    SearchDocumentInput,
    ReadDataInput,
    UpdateDataInput,
    SendDocumentInput,
    DeleteDataInput,
)
from app.security.secrets import secret_provider
from app.security.network import ssrf_protector

logger = logging.getLogger(__name__)


# Safe Mock Tool Handlers
async def handle_search_document(inputs: SearchDocumentInput) -> Dict[str, Any]:
    token = secret_provider.get_secret("DOCUMENT_SERVICE_TOKEN")
    return {
        "status": "executed",
        "tool": "search_document",
        "query": inputs.query,
        "document_id": inputs.document_id,
        "results": [
            {"id": "doc_101", "title": f"Result for '{inputs.query}'", "snippet": "Sample secure document content..."}
        ],
        "authenticated_via_secret": bool(token),
    }


async def handle_read_data(inputs: ReadDataInput) -> Dict[str, Any]:
    return {
        "status": "executed",
        "tool": "read_data",
        "target_resource": inputs.target_resource,
        "records_read": inputs.limit,
        "data": [{"id": 1, "resource": inputs.target_resource, "value": "sample_record_data"}],
    }


async def handle_update_data(inputs: UpdateDataInput) -> Dict[str, Any]:
    return {
        "status": "executed",
        "tool": "update_data",
        "target_resource": inputs.target_resource,
        "updated_fields": inputs.update_fields,
        "message": f"Successfully updated resource '{inputs.target_resource}'.",
    }


async def handle_send_document(inputs: SendDocumentInput) -> Dict[str, Any]:
    # SSRF Protection Check
    validated_host = ssrf_protector.validate_outbound_destination(inputs.destination_host)
    return {
        "status": "executed",
        "tool": "send_document",
        "document_id": inputs.document_id,
        "recipient_email": inputs.recipient_email,
        "destination_host": validated_host,
        "message": f"Document '{inputs.document_id}' sent securely to '{inputs.recipient_email}' via '{validated_host}'.",
    }


async def handle_delete_data(inputs: DeleteDataInput) -> Dict[str, Any]:
    return {
        "status": "executed",
        "tool": "delete_data",
        "target_resource": inputs.target_resource,
        "confirm_token": inputs.confirm_token,
        "message": f"Simulated deletion of resource '{inputs.target_resource}' completed.",
    }


# Tool Definitions
TOOLS: Dict[IntentEnum, ToolDefinition] = {
    IntentEnum.SEARCH_DOCUMENT: ToolDefinition(
        name="search_document",
        description="Safely searches document indexes",
        required_intent=IntentEnum.SEARCH_DOCUMENT,
        minimum_risk=RiskEnum.LOW,
        requires_approval=False,
        input_schema=SearchDocumentInput,
        handler=handle_search_document,
    ),
    IntentEnum.READ_DATA: ToolDefinition(
        name="read_data",
        description="Reads non-sensitive database records",
        required_intent=IntentEnum.READ_DATA,
        minimum_risk=RiskEnum.LOW,
        requires_approval=False,
        input_schema=ReadDataInput,
        handler=handle_read_data,
    ),
    IntentEnum.UPDATE_DATA: ToolDefinition(
        name="update_data",
        description="Updates existing records (requires approval)",
        required_intent=IntentEnum.UPDATE_DATA,
        minimum_risk=RiskEnum.MEDIUM,
        requires_approval=True,
        input_schema=UpdateDataInput,
        handler=handle_update_data,
    ),
    IntentEnum.SEND_DOCUMENT: ToolDefinition(
        name="send_document",
        description="Transmits documents externally (requires approval)",
        required_intent=IntentEnum.SEND_DOCUMENT,
        minimum_risk=RiskEnum.HIGH,
        requires_approval=True,
        input_schema=SendDocumentInput,
        handler=handle_send_document,
    ),
    IntentEnum.DELETE_DATA: ToolDefinition(
        name="delete_data",
        description="Purges or deletes data records (requires approval)",
        required_intent=IntentEnum.DELETE_DATA,
        minimum_risk=RiskEnum.HIGH,
        requires_approval=True,
        input_schema=DeleteDataInput,
        handler=handle_delete_data,
    ),
}


class ToolRegistry:
    @staticmethod
    def get_tool_for_intent(intent: IntentEnum) -> Optional[ToolDefinition]:
        return TOOLS.get(intent)

    @staticmethod
    def get_tool_by_name(name: str) -> Optional[ToolDefinition]:
        for tool in TOOLS.values():
            if tool.name.lower() == name.lower():
                return tool
        return None
