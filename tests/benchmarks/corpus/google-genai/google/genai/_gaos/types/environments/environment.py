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
from ...utils import serialize_int, validate_int
from ..interactions import environmentnetworkegressallowlist as interactions_environmentnetworkegressallowlist, source as interactions_source
from pydantic import model_serializer
from pydantic.functional_serializers import PlainSerializer
from pydantic.functional_validators import BeforeValidator
from typing import List, Literal, Optional, Union
from typing_extensions import Annotated, TypeAliasType
EnvironmentNetworkEnum = Union[Literal['disabled',], UnrecognizedStr]
EnvironmentNetworkUnion = TypeAliasType('EnvironmentNetworkUnion', Union[interactions_environmentnetworkegressallowlist.EnvironmentNetworkEgressAllowlist, EnvironmentNetworkEnum])
Status = Union[Literal['active', 'expired'], UnrecognizedStr]

class Environment(BaseModel):
    """An execution environment for an agent."""
    id: str
    created: Optional[str] = None
    file_count: Annotated[Optional[int], BeforeValidator(validate_int), PlainSerializer(serialize_int(True))] = None
    last_accessed: Optional[str] = None
    network: Optional[EnvironmentNetworkUnion] = None
    size_bytes: Annotated[Optional[int], BeforeValidator(validate_int), PlainSerializer(serialize_int(True))] = None
    sources: Optional[List[interactions_source.Source]] = None
    status: Optional[Status] = None
    updated: Optional[str] = None

    @model_serializer(mode='wrap')
    def serialize_model(self, handler):
        optional_fields = set(['created', 'file_count', 'last_accessed', 'network', 'size_bytes', 'sources', 'status', 'updated'])
        serialized = handler(self)
        m = {}
        for n, f in type(self).model_fields.items():
            k = f.alias or n
            val = serialized.get(k, serialized.get(n))
            if val != UNSET_SENTINEL:
                if val is not None or k not in optional_fields:
                    m[k] = val
        return m
