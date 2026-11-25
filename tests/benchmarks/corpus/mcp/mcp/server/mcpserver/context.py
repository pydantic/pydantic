# Frozen from MCP 2.3.0; see corpus README.md and LICENSE.
from __future__ import annotations
from typing import Generic, cast
from pydantic import BaseModel, model_validator
from typing_extensions import Self
from mcp.server.context import LifespanContextT, RequestT

class Context(BaseModel, Generic[LifespanContextT, RequestT]):
    _request_context: ServerRequestContext[LifespanContextT, RequestT] | None
    _mcp_server: MCPServer | None
    _input_params: InputResponseRequestParams | None
    _subscriptions: SubscriptionBus | None

    def __init__(self, *, request_context: ServerRequestContext[LifespanContextT, RequestT] | None=None, mcp_server: MCPServer | None=None, input_params: InputResponseRequestParams | None=None, subscriptions: SubscriptionBus | None=None, **kwargs: Any):
        super().__init__(**kwargs)
        self._request_context = request_context
        self._mcp_server = mcp_server
        self._input_params = input_params
        self._subscriptions = subscriptions

    @model_validator(mode='wrap')
    @classmethod
    def _keep_instance(cls, value: Any, handler: ModelWrapValidatorHandler[Self]) -> Self:
        return cast(Self, value) if isinstance(value, Context) else handler(value)
