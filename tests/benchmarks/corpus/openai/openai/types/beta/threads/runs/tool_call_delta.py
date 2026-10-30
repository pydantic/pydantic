# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Annotated, TypeAlias
from ....._utils import PropertyInfo
from .function_tool_call_delta import FunctionToolCallDelta
from .file_search_tool_call_delta import FileSearchToolCallDelta
from .code_interpreter_tool_call_delta import CodeInterpreterToolCallDelta
ToolCallDelta: TypeAlias = Annotated[Union[CodeInterpreterToolCallDelta, FileSearchToolCallDelta, FunctionToolCallDelta], PropertyInfo(discriminator='type')]
