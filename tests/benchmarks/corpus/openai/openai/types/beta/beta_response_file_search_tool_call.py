# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Dict, List, Union, Optional
from typing_extensions import Literal
from ..._models import BaseModel

class Agent(BaseModel):
    """The agent that produced this item."""
    agent_name: str

class Result(BaseModel):
    attributes: Optional[Dict[str, Union[str, float, bool]]] = None
    file_id: Optional[str] = None
    filename: Optional[str] = None
    score: Optional[float] = None
    text: Optional[str] = None

class BetaResponseFileSearchToolCall(BaseModel):
    """The results of a file search tool call.

    See the
    [file search guide](https://developers.openai.com/api/docs/guides/tools-file-search) for more information.
    """
    id: str
    queries: List[str]
    status: Literal['in_progress', 'searching', 'completed', 'incomplete', 'failed']
    type: Literal['file_search_call']
    agent: Optional[Agent] = None
    results: Optional[List[Result]] = None
