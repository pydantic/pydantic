# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class InstructionsAppendEvent(BaseModel):
    """
    Append developer instructions to the Live conversation while it is running, optionally associating them with an existing client delegation. Rejected while an audio fixture is active. These instructions remain in conversation history through compaction and are included in future backend delegations. For external audio, describe content already delivered so the assistant does not repeat it.
    """
    content: str
    delegation_id: Optional[str] = None
    type: Literal['session.instructions.append']
    event_id: Optional[str] = None
