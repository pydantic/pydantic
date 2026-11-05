# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ....._models import BaseModel

class CodeInterpreterLogs(BaseModel):
    """Text output from the Code Interpreter tool call as part of a run step."""
    index: int
    type: Literal['logs']
    logs: Optional[str] = None
