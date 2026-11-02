# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .response_computer_tool_call_output_screenshot import ResponseComputerToolCallOutputScreenshot

class AcknowledgedSafetyCheck(BaseModel):
    """A pending safety check for the computer call."""
    id: str
    code: Optional[str] = None
    message: Optional[str] = None

class ResponseComputerToolCallOutputItem(BaseModel):
    id: str
    call_id: str
    output: ResponseComputerToolCallOutputScreenshot
    status: Literal['completed', 'incomplete', 'failed', 'in_progress']
    type: Literal['computer_call_output']
    acknowledged_safety_checks: Optional[List[AcknowledgedSafetyCheck]] = None
    created_by: Optional[str] = None
