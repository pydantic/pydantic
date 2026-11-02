
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class ExternalKeyDeleteResponse(BaseModel):
    id: str
    type: Literal['external_key_deleted']
