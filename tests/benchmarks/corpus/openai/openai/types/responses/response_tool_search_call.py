# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class ResponseToolSearchCall(BaseModel):
    id: str
    arguments: object
    call_id: Optional[str] = None
    execution: Literal['server', 'client']
    status: Literal['in_progress', 'completed', 'incomplete']
    type: Literal['tool_search_call']
    created_by: Optional[str] = None
