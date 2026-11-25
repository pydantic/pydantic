# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from ....._models import BaseModel
from .tool_call_delta import ToolCallDelta

class ToolCallDeltaObject(BaseModel):
    """Details of the tool call."""
    type: Literal['tool_calls']
    tool_calls: Optional[List[ToolCallDelta]] = None
