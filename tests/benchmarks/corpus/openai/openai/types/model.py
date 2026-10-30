# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from .._models import BaseModel

class Model(BaseModel):
    """Describes an OpenAI model offering that can be used with the API."""
    id: str
    created: int
    object: Literal['model']
    owned_by: str
    shutdown_date: Optional[str] = None
