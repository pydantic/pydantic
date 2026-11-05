# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Literal, TypeAlias
from .assistant_tool_choice import AssistantToolChoice
AssistantToolChoiceOption: TypeAlias = Union[Literal['none', 'auto', 'required'], AssistantToolChoice]
