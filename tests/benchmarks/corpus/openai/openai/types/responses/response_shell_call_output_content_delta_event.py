# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class Delta(BaseModel):
    """The stdout/stderr delta that was emitted."""
    stderr: Optional[str] = None
    stdout: Optional[str] = None

class ResponseShellCallOutputContentDeltaEvent(BaseModel):
    """A streaming event that indicated shell call output was incrementally added."""
    command_index: int
    delta: Delta
    item_id: str
    output_index: int
    sequence_number: int
    type: Literal['response.shell_call_output_content.delta']
