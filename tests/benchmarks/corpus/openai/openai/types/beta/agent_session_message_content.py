# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Literal, Annotated, TypeAlias
from ..._utils import PropertyInfo
from ..._models import BaseModel

class MessageContentResourceInputText(BaseModel):
    """Text supplied by the user."""
    text: str
    type: Literal['input_text']

class MessageContentResourceInputImage(BaseModel):
    """An image supplied by the user."""
    image_url: str
    type: Literal['input_image']

class MessageContentResourceOutputText(BaseModel):
    """Text produced by the assistant."""
    text: str
    type: Literal['output_text']
AgentSessionMessageContent: TypeAlias = Annotated[Union[MessageContentResourceInputText, MessageContentResourceInputImage, MessageContentResourceOutputText], PropertyInfo(discriminator='type')]
