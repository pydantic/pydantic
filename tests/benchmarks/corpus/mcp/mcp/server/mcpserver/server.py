# Frozen from MCP 2.3.0; see corpus README.md and LICENSE.
from __future__ import annotations
from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from typing import Generic, Literal
from pydantic import BaseModel
from mcp.server.auth.settings import AuthSettings
from mcp.server.lowlevel.server import LifespanResultT

class Settings(BaseModel, Generic[LifespanResultT]):
    debug: bool
    log_level: Literal['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    warn_on_duplicate_resources: bool
    warn_on_duplicate_tools: bool
    warn_on_duplicate_prompts: bool
    dependencies: list[str]
    lifespan: Callable[[MCPServer[LifespanResultT]], AbstractAsyncContextManager[LifespanResultT]] | None
    auth: AuthSettings | None

class MCPServer(Generic[LifespanResultT]):
    pass
