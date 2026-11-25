# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class Notice(BaseModel):
    type: Literal['warning', 'deactivation']

class SafetyCase(BaseModel):
    id: str
    created_at: int
    entity_identifier: str
    notice: Notice
    object: Literal['safety.case']
    reason: Optional[str] = None
