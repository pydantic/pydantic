# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Annotated, TypeAlias
from ..._utils import PropertyInfo
from .function_tool import FunctionTool
from .file_search_tool import FileSearchTool
from .code_interpreter_tool import CodeInterpreterTool
AssistantTool: TypeAlias = Annotated[Union[CodeInterpreterTool, FileSearchTool, FunctionTool], PropertyInfo(discriminator='type')]
