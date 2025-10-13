from typing import Any

from pydantic import BaseModel


class ProcessRequest(BaseModel):
    """Schema for processing request payload."""

    payload: dict[str, Any]


class ProcessResponse(BaseModel):
    """Schema for processing response payload."""

    request_id: str
    status: str
    result: dict[str, Any] | None = None
