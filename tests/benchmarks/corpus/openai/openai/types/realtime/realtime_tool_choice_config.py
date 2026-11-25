# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import TypeAlias
from ..responses.tool_choice_mcp import ToolChoiceMcp
from ..responses.tool_choice_options import ToolChoiceOptions
from ..responses.tool_choice_function import ToolChoiceFunction
RealtimeToolChoiceConfig: TypeAlias = Union[ToolChoiceOptions, ToolChoiceFunction, ToolChoiceMcp]
