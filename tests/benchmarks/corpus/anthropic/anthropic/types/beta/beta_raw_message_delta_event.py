
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_container import BetaContainer
from .beta_stop_reason import BetaStopReason
from .beta_message_delta_usage import BetaMessageDeltaUsage
from .beta_input_transformation import BetaInputTransformation
from .beta_refusal_stop_details import BetaRefusalStopDetails
from .beta_context_management_response import BetaContextManagementResponse

class Delta(BaseModel):
    container: Optional[BetaContainer] = None
    stop_details: Optional[BetaRefusalStopDetails] = None
    stop_reason: Optional[BetaStopReason] = None
    stop_sequence: Optional[str] = None

class BetaRawMessageDeltaEvent(BaseModel):
    context_management: Optional[BetaContextManagementResponse] = None
    delta: Delta
    type: Literal['message_delta']
    usage: BetaMessageDeltaUsage
    input_transformations: Optional[List[BetaInputTransformation]] = None
