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
from .. import BaseModel, UNSET_SENTINEL, UnrecognizedStr
from ...utils import validate_const
from .environmentnetworkegressallowlist import EnvironmentNetworkEgressAllowlist, EnvironmentNetworkEgressAllowlistParam
from .envvar import EnvVar, EnvVarParam
from .source import Source, SourceParam
import pydantic
from pydantic import model_serializer
from pydantic.functional_validators import AfterValidator
from typing import Dict, List, Literal, Optional, Union
from typing_extensions import Annotated, NotRequired, TypeAliasType, TypedDict
EnvParam = TypeAliasType('EnvParam', Union[EnvVarParam, str])
Env = TypeAliasType('Env', Union[EnvVar, str])
NetworkEnum = Union[Literal['disabled',], UnrecognizedStr]
NetworkParam = TypeAliasType('NetworkParam', Union[EnvironmentNetworkEgressAllowlistParam, NetworkEnum])
Network = TypeAliasType('Network', Union[EnvironmentNetworkEgressAllowlist, NetworkEnum])

class EnvironmentParam(TypedDict):
    """Configuration for a custom environment."""
    env: NotRequired[Dict[str, EnvParam]]
    environment_id: NotRequired[str]
    network: NotRequired[NetworkParam]
    sources: NotRequired[List[SourceParam]]
    type: Literal['remote']

class Environment(BaseModel):
    """Configuration for a custom environment."""
    env: Optional[Dict[str, Env]] = None
    environment_id: Optional[str] = None
    network: Optional[Network] = None
    sources: Optional[List[Source]] = None
    type: Annotated[Annotated[Literal['remote'], AfterValidator(validate_const('remote'))], pydantic.Field(alias='type')] = 'remote'

    @model_serializer(mode='wrap')
    def serialize_model(self, handler):
        optional_fields = set(['env', 'environment_id', 'network', 'sources'])
        serialized = handler(self)
        m = {}
        for n, f in type(self).model_fields.items():
            k = f.alias or n
            val = serialized.get(k, serialized.get(n))
            if val != UNSET_SENTINEL:
                if val is not None or k not in optional_fields:
                    m[k] = val
        return m
