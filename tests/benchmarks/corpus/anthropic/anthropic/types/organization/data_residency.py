
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List, Union
from typing_extensions import Literal
from ..._models import BaseModel
from .allowed_inference_geo import AllowedInferenceGeo

class DataResidency(BaseModel):
    allowed_inference_geos: Union[List[AllowedInferenceGeo], Literal['unrestricted']]
    default_inference_geo: Literal['global', 'us']
    workspace_geo: Literal['us']
