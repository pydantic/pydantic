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
from ..types import BaseModel, UNSET_SENTINEL
from ..types.credentials import credentialupdate as credentials_credentialupdate
from ..utils import FieldMetadata, PathParamMetadata, QueryParamMetadata, RequestMetadata
from pydantic import model_serializer
from typing import Optional
from typing_extensions import Annotated

class UpdateCredentialGlobals(BaseModel):
    api_version: Annotated[Optional[str], FieldMetadata(path=PathParamMetadata(style='simple', explode=False))] = None

    @model_serializer(mode='wrap')
    def serialize_model(self, handler):
        optional_fields = set(['api_version'])
        serialized = handler(self)
        m = {}
        for n, f in type(self).model_fields.items():
            k = f.alias or n
            val = serialized.get(k, serialized.get(n))
            if val != UNSET_SENTINEL:
                if val is not None or k not in optional_fields:
                    m[k] = val
        return m

class UpdateCredentialRequest(BaseModel):
    id: Annotated[str, FieldMetadata(path=PathParamMetadata(style='simple', explode=False))]
    body: Annotated[credentials_credentialupdate.CredentialUpdate, FieldMetadata(request=RequestMetadata(media_type='application/json'))]
    api_version: Annotated[Optional[str], FieldMetadata(path=PathParamMetadata(style='simple', explode=False))] = None
    update_mask: Annotated[Optional[str], FieldMetadata(query=QueryParamMetadata(style='form', explode=True))] = None

    @model_serializer(mode='wrap')
    def serialize_model(self, handler):
        optional_fields = set(['api_version', 'update_mask'])
        serialized = handler(self)
        m = {}
        for n, f in type(self).model_fields.items():
            k = f.alias or n
            val = serialized.get(k, serialized.get(n))
            if val != UNSET_SENTINEL:
                if val is not None or k not in optional_fields:
                    m[k] = val
        return m
