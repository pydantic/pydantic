# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# pyformat: disable
# pylint: skip-file

# Frozen model corpus; modified from google-genai 2.34.0; see README.md and LICENSE.
from __future__ import annotations
from .. import BaseModel
from ...utils.unions import parse_open_union
from .codeexecution import CodeExecution, CodeExecutionParam
from .computeruse import ComputerUse, ComputerUseParam
from .filesearch import FileSearch, FileSearchParam
from .function import Function, FunctionParam
from .googlemaps import GoogleMaps, GoogleMapsParam
from .googlesearch import GoogleSearch, GoogleSearchParam
from .mcpserver import MCPServer, MCPServerParam
from .retrieval import Retrieval, RetrievalParam
from .urlcontext import URLContext, URLContextParam
from functools import partial
from pydantic import ConfigDict
from pydantic.functional_validators import BeforeValidator
from typing import Any, Literal, Union
from typing_extensions import Annotated, TypeAliasType
ToolParam = TypeAliasType('ToolParam', Union[CodeExecutionParam, URLContextParam, GoogleSearchParam, FileSearchParam, FunctionParam, GoogleMapsParam, ComputerUseParam, MCPServerParam, RetrievalParam])

class UnknownTool(BaseModel):
    """A Tool variant the SDK doesn't recognize. Preserves the raw payload."""
    type: Literal['UNKNOWN'] = 'UNKNOWN'
    raw: Any
    is_unknown: Literal[True] = True
    model_config = ConfigDict(frozen=True)
_TOOL_VARIANTS: dict[str, Any] = {'code_execution': CodeExecution, 'computer_use': ComputerUse, 'file_search': FileSearch, 'function': Function, 'google_maps': GoogleMaps, 'google_search': GoogleSearch, 'mcp_server': MCPServer, 'retrieval': Retrieval, 'url_context': URLContext}
Tool = Annotated[Union[CodeExecution, ComputerUse, FileSearch, Function, GoogleMaps, GoogleSearch, MCPServer, Retrieval, URLContext, UnknownTool], BeforeValidator(partial(parse_open_union, disc_key='type', variants=_TOOL_VARIANTS, unknown_cls=UnknownTool, union_name='Tool', lenient=True))]
