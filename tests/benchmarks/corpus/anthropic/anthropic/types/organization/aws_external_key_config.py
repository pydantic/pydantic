
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class AWSExternalKeyConfig(BaseModel):
    kms_arn: str
    type: Literal['aws']
    region: Optional[str] = None
