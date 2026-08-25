import re
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
from app.config import settings

PATH_TRAVERSAL_REGEX = re.compile(r"(\.\.[/\\]|[/\\]etc[/\\]|[cC]:[/\\][wW]indows)", re.IGNORECASE)
COMMAND_INJECTION_REGEX = re.compile(r"[\|;&$`\n\r]")


def sanitize_input_string(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        return value

    if len(value) > settings.MAX_TOOL_INPUT_SIZE:
        raise ValueError(
            f"Field '{field_name}' string length ({len(value)}) exceeds maximum allowed tool input limit of {settings.MAX_TOOL_INPUT_SIZE} characters."
        )

    if PATH_TRAVERSAL_REGEX.search(value):
        raise ValueError(
            f"Path traversal sequence detected in field '{field_name}'."
        )

    if COMMAND_INJECTION_REGEX.search(value):
        raise ValueError(
            f"Forbidden command injection characters detected in field '{field_name}'."
        )

    return value.strip()


class BaseToolInput(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SearchDocumentInput(BaseToolInput):
    query: str = Field(..., min_length=1)
    document_id: Optional[str] = Field(default=None)

    @field_validator("query", "document_id", mode="before")
    @classmethod
    def validate_fields(cls, v: Any, info) -> Any:
        if isinstance(v, str):
            return sanitize_input_string(v, info.field_name)
        return v


class ReadDataInput(BaseToolInput):
    target_resource: str = Field(..., min_length=1)
    limit: Optional[int] = Field(default=100, ge=1, le=1000)

    @field_validator("target_resource", mode="before")
    @classmethod
    def validate_resource(cls, v: Any, info) -> Any:
        if isinstance(v, str):
            return sanitize_input_string(v, info.field_name)
        return v


class UpdateDataInput(BaseToolInput):
    target_resource: str = Field(..., min_length=1)
    update_fields: Dict[str, str] = Field(..., min_length=1)

    @field_validator("target_resource", mode="before")
    @classmethod
    def validate_resource(cls, v: Any, info) -> Any:
        if isinstance(v, str):
            return sanitize_input_string(v, info.field_name)
        return v

    @field_validator("update_fields", mode="before")
    @classmethod
    def validate_dict_values(cls, v: Any, info) -> Any:
        if isinstance(v, dict):
            sanitized = {}
            for k, val in v.items():
                san_k = sanitize_input_string(str(k), "update_fields_key")
                san_v = sanitize_input_string(str(val), "update_fields_value")
                sanitized[san_k] = san_v
            return sanitized
        return v


class SendDocumentInput(BaseToolInput):
    document_id: str = Field(..., min_length=1)
    recipient_email: str = Field(..., min_length=3)
    destination_host: str = Field(..., min_length=1)

    @field_validator("document_id", "recipient_email", "destination_host", mode="before")
    @classmethod
    def validate_fields(cls, v: Any, info) -> Any:
        if isinstance(v, str):
            return sanitize_input_string(v, info.field_name)
        return v


class DeleteDataInput(BaseToolInput):
    target_resource: str = Field(..., min_length=1)
    confirm_token: str = Field(..., min_length=1)

    @field_validator("target_resource", "confirm_token", mode="before")
    @classmethod
    def validate_fields(cls, v: Any, info) -> Any:
        if isinstance(v, str):
            return sanitize_input_string(v, info.field_name)
        return v
