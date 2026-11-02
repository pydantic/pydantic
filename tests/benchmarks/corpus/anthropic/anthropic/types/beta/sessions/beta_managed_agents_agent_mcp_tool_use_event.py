
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Dict, Optional
from datetime import datetime
from typing_extensions import Literal
from ...._models import BaseModel
from .beta_managed_agents_agent_tool_evaluation import BetaManagedAgentsAgentToolEvaluation
from .beta_managed_agents_agent_evaluated_permission import BetaManagedAgentsAgentEvaluatedPermission

class BetaManagedAgentsAgentMCPToolUseEvent(BaseModel):
    """Event emitted when the agent invokes a tool provided by an MCP server."""
    id: str
    input: Dict[str, object]
    mcp_server_name: str
    name: str
    processed_at: datetime
    type: Literal['agent.mcp_tool_use']
    evaluated_permission: Optional[BetaManagedAgentsAgentEvaluatedPermission] = None
    evaluation: Optional[BetaManagedAgentsAgentToolEvaluation] = None
    session_thread_id: Optional[str] = None
