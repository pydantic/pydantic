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
from .findrequest import FindRequest, FindRequestParam
from .fixrequest import FixRequest, FixRequestParam
from .sessionconfig import SessionConfig, SessionConfigParam
import pydantic
from pydantic import model_serializer
from pydantic.functional_validators import AfterValidator
from typing import Literal, Optional
from typing_extensions import Annotated, NotRequired, TypedDict

class CodeMenderAgentConfigParam(TypedDict):
    """Configuration for the CodeMender agent."""
    find_request: NotRequired[FindRequestParam]
    fix_request: NotRequired[FixRequestParam]
    model: NotRequired[str]
    session_config: NotRequired[SessionConfigParam]
    session_id: NotRequired[str]
    type: Literal['code-mender']

class CodeMenderAgentConfig(BaseModel):
    """Configuration for the CodeMender agent."""
    find_request: Optional[FindRequest] = None
    fix_request: Optional[FixRequest] = None
    model: Optional[str] = None
    session_config: Optional[SessionConfig] = None
    session_id: Optional[str] = None
    type: Annotated[Annotated[Literal['code-mender'], AfterValidator(validate_const('code-mender'))], pydantic.Field(alias='type')] = 'code-mender'

    @model_serializer(mode='wrap')
    def serialize_model(self, handler):
        optional_fields = set(['find_request', 'fix_request', 'model', 'session_config', 'session_id'])
        serialized = handler(self)
        m = {}
        for n, f in type(self).model_fields.items():
            k = f.alias or n
            val = serialized.get(k, serialized.get(n))
            if val != UNSET_SENTINEL:
                if val is not None or k not in optional_fields:
                    m[k] = val
        return m
