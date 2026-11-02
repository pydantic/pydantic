# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Dict, List, Union, Optional
from typing_extensions import Literal
from .._models import BaseModel

class Content(BaseModel):
    text: str
    type: Literal['text']

class VectorStoreSearchResponse(BaseModel):
    attributes: Optional[Dict[str, Union[str, float, bool]]] = None
    content: List[Content]
    file_id: str
    filename: str
    score: float
