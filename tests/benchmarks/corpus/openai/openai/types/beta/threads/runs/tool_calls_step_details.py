# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List
from typing_extensions import Literal
from .tool_call import ToolCall
from ....._models import BaseModel

class ToolCallsStepDetails(BaseModel):
    """Details of the tool call."""
    tool_calls: List[ToolCall]
    type: Literal['tool_calls']
