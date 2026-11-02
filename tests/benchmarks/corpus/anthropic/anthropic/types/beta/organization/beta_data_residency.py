
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List, Union
from typing_extensions import Literal
from ...._models import BaseModel
from .beta_allowed_inference_geo import BetaAllowedInferenceGeo

class BetaDataResidency(BaseModel):
    allowed_inference_geos: Union[List[BetaAllowedInferenceGeo], Literal['unrestricted']]
    default_inference_geo: Literal['global', 'us']
    workspace_geo: Literal['us']
