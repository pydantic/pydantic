# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel
from ..shared.function_definition import FunctionDefinition

class ChatCompletionFunctionTool(BaseModel):
    """A function tool that can be used to generate a response."""
    function: FunctionDefinition
    type: Literal['function']
