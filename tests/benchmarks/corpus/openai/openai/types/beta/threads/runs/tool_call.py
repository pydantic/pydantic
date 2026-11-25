# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Annotated, TypeAlias
from ....._utils import PropertyInfo
from .function_tool_call import FunctionToolCall
from .file_search_tool_call import FileSearchToolCall
from .code_interpreter_tool_call import CodeInterpreterToolCall
ToolCall: TypeAlias = Annotated[Union[CodeInterpreterToolCall, FileSearchToolCall, FunctionToolCall], PropertyInfo(discriminator='type')]
