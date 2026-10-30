
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class ExternalKeyValidateResponse(BaseModel):
    """Result of a validation roundtrip against the customer's KMS.

    HTTP 200 for both outcomes — the operation completed; `status` says
    whether the key works.
    """
    error: Optional[str] = None
    status: Literal['failure', 'success']
    type: Literal['external_key_validation']
