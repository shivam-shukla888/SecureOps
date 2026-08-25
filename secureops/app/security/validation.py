from fastapi import Request, HTTPException, status
from app.config import settings


async def validate_request_payload_size(request: Request) -> bytes:
    # 1. Content-Type check
    content_type = request.headers.get("content-type", "")
    if "application/json" not in content_type.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Content-Type. Content-Type must be application/json."
        )

    # 2. Check Content-Length header if available
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            length = int(content_length)
            if length > settings.MAX_REQUEST_SIZE_BYTES:
                raise HTTPException(
                    status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                    detail=f"Payload size {length} bytes exceeds maximum allowed size of {settings.MAX_REQUEST_SIZE_BYTES} bytes."
                )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Content-Length header."
            )

    # 3. Read body bytes and verify size
    body_bytes = await request.body()
    if len(body_bytes) > settings.MAX_REQUEST_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"Payload size {len(body_bytes)} bytes exceeds maximum allowed size of {settings.MAX_REQUEST_SIZE_BYTES} bytes."
        )

    return body_bytes


def validate_request_text_length(request_text: str):
    if not request_text or not request_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request prompt cannot be empty or whitespace only."
        )
    
    if len(request_text) > settings.MAX_REQUEST_LENGTH_CHARS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Request text length ({len(request_text)} chars) exceeds maximum allowed limit of {settings.MAX_REQUEST_LENGTH_CHARS} characters."
        )
