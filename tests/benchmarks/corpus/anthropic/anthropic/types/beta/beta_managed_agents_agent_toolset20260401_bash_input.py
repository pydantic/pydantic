
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from ..._models import BaseModel

class BetaManagedAgentsAgentToolset20260401BashInput(BaseModel):
    """Input payload for the `bash` tool of the
    `agent_toolset_20260401` toolset.

    All fields are optional;
    a normal invocation supplies `command`, while `restart=true`
    (with no `command`) reboots the runner-side bash session.
    """
    command: Optional[str] = None
    restart: Optional[bool] = None
    timeout_ms: Optional[int] = None
