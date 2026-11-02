# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class Agent(BaseModel):
    """The agent that owns this multi-agent streaming event."""
    agent_name: str

class BetaResponseShellCallCommandAddedEvent(BaseModel):
    """A streaming event that indicated a shell command was added to a tool call."""
    command: str
    command_index: int
    output_index: int
    sequence_number: int
    type: Literal['response.shell_call_command.added']
    agent: Optional[Agent] = None
