
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from ..model import Model
from ..._models import BaseModel
from .beta_usage import BetaUsage
from .beta_container import BetaContainer
from .beta_diagnostics import BetaDiagnostics
from .beta_stop_reason import BetaStopReason
from .beta_content_block import BetaContentBlock, BetaContentBlock as BetaContentBlock
from .beta_input_transformation import BetaInputTransformation
from .beta_refusal_stop_details import BetaRefusalStopDetails
from .beta_context_management_response import BetaContextManagementResponse

class BetaMessage(BaseModel):
    id: str
    container: Optional[BetaContainer] = None
    content: List[BetaContentBlock]
    context_management: Optional[BetaContextManagementResponse] = None
    diagnostics: Optional[BetaDiagnostics] = None
    model: Model
    role: Literal['assistant']
    stop_details: Optional[BetaRefusalStopDetails] = None
    stop_reason: Optional[BetaStopReason] = None
    stop_sequence: Optional[str] = None
    type: Literal['message']
    usage: BetaUsage
    input_transformations: Optional[List[BetaInputTransformation]] = None
