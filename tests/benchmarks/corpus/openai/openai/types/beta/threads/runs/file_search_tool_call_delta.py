# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ....._models import BaseModel

class FileSearchToolCallDelta(BaseModel):
    file_search: object
    index: int
    type: Literal['file_search']
    id: Optional[str] = None
