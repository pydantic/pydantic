# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .assistant_tool_choice_function import AssistantToolChoiceFunction

class AssistantToolChoice(BaseModel):
    """Specifies a tool the model should use.

    Use to force the model to call a specific tool.
    """
    type: Literal['function', 'code_interpreter', 'file_search']
    function: Optional[AssistantToolChoiceFunction] = None
