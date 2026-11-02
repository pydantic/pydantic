# Frozen from MCP 2.3.0; see corpus README.md and LICENSE.
from __future__ import annotations
from typing import Annotated, Any, Final, Literal
from pydantic import BaseModel, Field, TypeAdapter
RequestId = Annotated[int, Field(strict=True)] | str
JSONRPC_VERSION: Final[Literal['2.0']] = '2.0'

class JSONRPCRequest(BaseModel):
    jsonrpc: Literal['2.0']
    id: RequestId
    method: str
    params: dict[str, Any] | None = None

class JSONRPCNotification(BaseModel):
    jsonrpc: Literal['2.0']
    method: str
    params: dict[str, Any] | None = None

class JSONRPCResponse(BaseModel):
    jsonrpc: Literal['2.0']
    id: RequestId
    result: dict[str, Any]
HEADER_MISMATCH = -32020
MISSING_REQUIRED_CLIENT_CAPABILITY = -32021
UNSUPPORTED_PROTOCOL_VERSION = -32022
URL_ELICITATION_REQUIRED = -32042
CONNECTION_CLOSED = -32000
REQUEST_TIMEOUT = -32001
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603

class ErrorData(BaseModel):
    code: int
    message: str
    data: Any = None

class JSONRPCError(BaseModel):
    jsonrpc: Literal['2.0']
    id: RequestId | None
    error: ErrorData
JSONRPCMessage = JSONRPCRequest | JSONRPCNotification | JSONRPCResponse | JSONRPCError
jsonrpc_message_adapter: TypeAdapter[JSONRPCMessage] = TypeAdapter(JSONRPCMessage)
