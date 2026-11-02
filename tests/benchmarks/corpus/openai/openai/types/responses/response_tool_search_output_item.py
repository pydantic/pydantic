# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from .tool import Tool
from ..._models import BaseModel

class ResponseToolSearchOutputItem(BaseModel):
    id: str
    call_id: Optional[str] = None
    execution: Literal['server', 'client']
    status: Literal['in_progress', 'completed', 'incomplete']
    tools: List[Tool]
    type: Literal['tool_search_output']
    created_by: Optional[str] = None
