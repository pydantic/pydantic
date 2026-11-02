# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class HostedEnvironmentFileID(BaseModel):
    """A file copied from the OpenAI Files API."""
    id: str
    file_id: str
    path: str
    size_bytes: int
    type: Literal['file_id']
