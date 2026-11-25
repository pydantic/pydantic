# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ...._models import BaseModel

class ImageFile(BaseModel):
    file_id: str
    detail: Optional[Literal['auto', 'low', 'high']] = None
