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

class FunctionResultStepResultParam(TypedDict):
    pass

class FunctionResultStepResult(BaseModel):
    pass
FunctionResultStepResultUnionParam = TypeAliasType('FunctionResultStepResultUnionParam', Union[FunctionResultStepResultParam, List[FunctionResultSubcontentParam], str])
FunctionResultStepResultUnion = TypeAliasType('FunctionResultStepResultUnion', Union[FunctionResultStepResult, List[FunctionResultSubcontent], str])

class FunctionResultStepParam(TypedDict):
    """Result of a function tool call."""
    call_id: str
    result: FunctionResultStepResultUnionParam
    is_error: NotRequired[bool]
    name: NotRequired[str]
    type: Literal['function_result']

class FunctionResultStep(BaseModel):
    """Result of a function tool call."""
    call_id: str
    result: FunctionResultStepResultUnion
    is_error: Optional[bool] = None
    name: Optional[str] = None
    type: Annotated[Annotated[Literal['function_result'], AfterValidator(validate_const('function_result'))], pydantic.Field(alias='type')] = 'function_result'

    @model_serializer(mode='wrap')
    def serialize_model(self, handler):
        optional_fields = set(['is_error', 'name'])
        serialized = handler(self)
        m = {}
        for n, f in type(self).model_fields.items():
            k = f.alias or n
            val = serialized.get(k, serialized.get(n))
            if val != UNSET_SENTINEL:
                if val is not None or k not in optional_fields:
                    m[k] = val
        return m
