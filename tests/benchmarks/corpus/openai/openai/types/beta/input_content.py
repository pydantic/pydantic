# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Literal, Annotated, TypeAlias
from ..._utils import PropertyInfo
from ..._models import BaseModel

class InputContentResourceInputText(BaseModel):
    """Text input recorded in a session item."""
    text: str
    type: Literal['input_text']

class InputContentResourceInputImage(BaseModel):
    """Image input recorded in a session item."""
    image_url: str
    type: Literal['input_image']
InputContent: TypeAlias = Annotated[Union[InputContentResourceInputText, InputContentResourceInputImage], PropertyInfo(discriminator='type')]
