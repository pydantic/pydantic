
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Dict, Optional
from datetime import datetime
from typing_extensions import Literal
from ...._models import BaseModel

class BetaManagedAgentsAgentCustomToolUseEvent(BaseModel):
    """Event emitted when the agent calls a custom tool.

    The session goes idle until the client sends a `user.custom_tool_result` event with the result. The client can send it as soon as this event arrives, without waiting for `session.status_idle`.
    """
    id: str
    input: Dict[str, object]
    name: str
    processed_at: datetime
    type: Literal['agent.custom_tool_use']
    session_thread_id: Optional[str] = None
