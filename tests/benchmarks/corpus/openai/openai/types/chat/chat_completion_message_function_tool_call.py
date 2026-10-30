# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class Function(BaseModel):
    """The function that the model called."""
    arguments: str
    name: str

class ChatCompletionMessageFunctionToolCall(BaseModel):
    """A call to a function tool created by the model."""
    id: str
    function: Function
    type: Literal['function']
