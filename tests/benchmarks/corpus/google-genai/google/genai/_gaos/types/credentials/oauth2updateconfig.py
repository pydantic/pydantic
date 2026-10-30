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
import pydantic
from pydantic import model_serializer
from pydantic.functional_validators import AfterValidator
from typing import List, Literal, Optional
from typing_extensions import Annotated, NotRequired, TypedDict

class OAuth2UpdateConfigParam(TypedDict):
    """Configuration for updating OAuth2 credentials."""
    client_id: NotRequired[str]
    client_secret: NotRequired[str]
    refresh_token: NotRequired[str]
    scopes: NotRequired[List[str]]
    token_url: NotRequired[str]
    type: Literal['oauth2']

class OAuth2UpdateConfig(BaseModel):
    """Configuration for updating OAuth2 credentials."""
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    refresh_token: Optional[str] = None
    scopes: Optional[List[str]] = None
    token_url: Optional[str] = None
    type: Annotated[Annotated[Literal['oauth2'], AfterValidator(validate_const('oauth2'))], pydantic.Field(alias='type')] = 'oauth2'

    @model_serializer(mode='wrap')
    def serialize_model(self, handler):
        optional_fields = set(['client_id', 'client_secret', 'refresh_token', 'scopes', 'token_url'])
        serialized = handler(self)
        m = {}
        for n, f in type(self).model_fields.items():
            k = f.alias or n
            val = serialized.get(k, serialized.get(n))
            if val != UNSET_SENTINEL:
                if val is not None or k not in optional_fields:
                    m[k] = val
        return m
