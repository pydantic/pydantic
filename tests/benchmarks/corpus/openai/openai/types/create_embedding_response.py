# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List
from typing_extensions import Literal
from .._models import BaseModel
from .embedding import Embedding

class Usage(BaseModel):
    """The usage information for the request."""
    prompt_tokens: int
    total_tokens: int

class CreateEmbeddingResponse(BaseModel):
    data: List[Embedding]
    model: str
    object: Literal['list']
    usage: Usage
