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
from .. import BaseModel, UNSET_SENTINEL
from ...utils import validate_const
from .functionresultsubcontent import FunctionResultSubcontent, FunctionResultSubcontentParam
import pydantic
from pydantic import model_serializer
from pydantic.functional_validators import AfterValidator
from typing import List, Literal, Optional, Union
from typing_extensions import Annotated, NotRequired, TypeAliasType, TypedDict

class MCPServerToolResultStepResultParam(TypedDict):
    pass

class MCPServerToolResultStepResult(BaseModel):
    pass
MCPServerToolResultStepResultUnionParam = TypeAliasType('MCPServerToolResultStepResultUnionParam', Union[MCPServerToolResultStepResultParam, List[FunctionResultSubcontentParam], str])
MCPServerToolResultStepResultUnion = TypeAliasType('MCPServerToolResultStepResultUnion', Union[MCPServerToolResultStepResult, List[FunctionResultSubcontent], str])

class MCPServerToolResultStepParam(TypedDict):
    """MCPServer tool result step."""
    call_id: str
    result: MCPServerToolResultStepResultUnionParam
    name: NotRequired[str]
    server_name: NotRequired[str]
    type: Literal['mcp_server_tool_result']

class MCPServerToolResultStep(BaseModel):
    """MCPServer tool result step."""
    call_id: str
    result: MCPServerToolResultStepResultUnion
    name: Optional[str] = None
    server_name: Optional[str] = None
    type: Annotated[Annotated[Literal['mcp_server_tool_result'], AfterValidator(validate_const('mcp_server_tool_result'))], pydantic.Field(alias='type')] = 'mcp_server_tool_result'

    @model_serializer(mode='wrap')
    def serialize_model(self, handler):
        optional_fields = set(['name', 'server_name'])
        serialized = handler(self)
        m = {}
        for n, f in type(self).model_fields.items():
            k = f.alias or n
            val = serialized.get(k, serialized.get(n))
            if val != UNSET_SENTINEL:
                if val is not None or k not in optional_fields:
                    m[k] = val
        return m
