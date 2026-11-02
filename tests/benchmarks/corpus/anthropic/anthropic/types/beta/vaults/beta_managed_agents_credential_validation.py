
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from datetime import datetime
from typing_extensions import Literal
from ...._models import BaseModel
from .beta_managed_agents_mcp_probe import BetaManagedAgentsMCPProbe
from .beta_managed_agents_refresh_object import BetaManagedAgentsRefreshObject
from .beta_managed_agents_credential_validation_status import BetaManagedAgentsCredentialValidationStatus

class BetaManagedAgentsCredentialValidation(BaseModel):
    """Result of live-probing a credential against its configured MCP server."""
    credential_id: str
    has_refresh_token: bool
    mcp_probe: Optional[BetaManagedAgentsMCPProbe] = None
    refresh: Optional[BetaManagedAgentsRefreshObject] = None
    status: BetaManagedAgentsCredentialValidationStatus
    type: Literal['vault_credential_validation']
    validated_at: datetime
    vault_id: str
