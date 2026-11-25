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
from pydantic import model_serializer
from typing import Dict, List, Optional, Union
from typing_extensions import NotRequired, TypeAliasType, TypedDict
TransformParam = TypeAliasType('TransformParam', Union[List[Dict[str, str]], Dict[str, str]])
Transform = TypeAliasType('Transform', Union[List[Dict[str, str]], Dict[str, str]])

class AllowlistEntryParam(TypedDict):
    """A single domain allowlist rule with optional header injection."""
    domain: str
    credential: NotRequired[str]
    transform: NotRequired[TransformParam]

class AllowlistEntry(BaseModel):
    """A single domain allowlist rule with optional header injection."""
    domain: str
    credential: Optional[str] = None
    transform: Optional[Transform] = None

    @model_serializer(mode='wrap')
    def serialize_model(self, handler):
        optional_fields = set(['credential', 'transform'])
        serialized = handler(self)
        m = {}
        for n, f in type(self).model_fields.items():
            k = f.alias or n
            val = serialized.get(k, serialized.get(n))
            if val != UNSET_SENTINEL:
                if val is not None or k not in optional_fields:
                    m[k] = val
        return m
