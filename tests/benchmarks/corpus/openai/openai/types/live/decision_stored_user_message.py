# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ..._utils import PropertyInfo
from ..._models import BaseModel
from .decision_json_object import DecisionJSONObject

class ContentPartInputText(BaseModel):
    text: str
    type: Literal['input_text']

class ContentPartInputImage(BaseModel):
    image_url: str
    type: Literal['input_image']
    detail: Optional[Literal['low', 'high', 'auto', 'original']] = None

class ContentPartInputJSON(BaseModel):
    data: Union[List[DecisionJSONObject], DecisionJSONObject]
    type: Literal['input_json']
ContentPart: TypeAlias = Annotated[Union[ContentPartInputText, ContentPartInputImage, ContentPartInputJSON], PropertyInfo(discriminator='type')]

class DecisionStoredUserMessage(BaseModel):
    id: str
    content: Union[str, List[ContentPart]]
    role: Literal['user']
    type: Optional[Literal['message']] = None
