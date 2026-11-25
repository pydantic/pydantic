# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Union, Optional
from typing_extensions import Literal, TypeAlias
from ..._models import BaseModel
from ..responses.response_input_text import ResponseInputText
from ..responses.response_input_audio import ResponseInputAudio

class GraderInputItemOutputText(BaseModel):
    """A text output from the model."""
    text: str
    type: Literal['output_text']

class GraderInputItemInputImage(BaseModel):
    """An image input block used within EvalItem content arrays."""
    image_url: str
    type: Literal['input_image']
    detail: Optional[str] = None
GraderInputItem: TypeAlias = Union[str, ResponseInputText, GraderInputItemOutputText, GraderInputItemInputImage, ResponseInputAudio]
GraderInputs: TypeAlias = List[GraderInputItem]
