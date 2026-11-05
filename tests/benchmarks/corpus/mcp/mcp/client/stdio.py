# Frozen from MCP 2.3.0; see corpus README.md and LICENSE.
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, Field

class StdioServerParameters(BaseModel):
    command: str
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] | None = None
    cwd: str | Path | None = None
    encoding: str = 'utf-8'
    encoding_error_handler: Literal['strict', 'ignore', 'replace'] = 'strict'
