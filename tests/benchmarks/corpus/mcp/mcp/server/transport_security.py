# Frozen from MCP 2.3.0; see corpus README.md and LICENSE.
from pydantic import BaseModel, Field

class TransportSecuritySettings(BaseModel):
    enable_dns_rebinding_protection: bool = True
    allowed_hosts: list[str] = Field(default_factory=list)
    allowed_origins: list[str] = Field(default_factory=list)
