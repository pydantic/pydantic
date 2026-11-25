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
from ..utils import FieldMetadata, HeaderMetadata, PathParamMetadata, QueryParamMetadata, validate_const
import pydantic
from pydantic import model_serializer
from pydantic.functional_validators import AfterValidator
from typing import Dict, List, Literal, Optional
from typing_extensions import Annotated

class StartEnvironmentFileUploadGlobals(BaseModel):
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

class StartEnvironmentFileUploadRequest(BaseModel):
    environment: Annotated[str, FieldMetadata(path=PathParamMetadata(style='simple', explode=False))]
    path: Annotated[str, FieldMetadata(path=PathParamMetadata(style='simple', explode=False))]
    x_goog_upload_header_content_length: Annotated[int, pydantic.Field(alias='X-Goog-Upload-Header-Content-Length'), FieldMetadata(header=HeaderMetadata(style='simple', explode=False))]
    x_goog_upload_header_content_type: Annotated[str, pydantic.Field(alias='X-Goog-Upload-Header-Content-Type'), FieldMetadata(header=HeaderMetadata(style='simple', explode=False))]
    api_version: Annotated[Optional[str], FieldMetadata(path=PathParamMetadata(style='simple', explode=False))] = None
    extract: Annotated[Optional[bool], FieldMetadata(query=QueryParamMetadata(style='form', explode=True))] = None
    overwrite: Annotated[Optional[bool], FieldMetadata(query=QueryParamMetadata(style='form', explode=True))] = None
    x_goog_upload_command: Annotated[Annotated[Literal['start'], AfterValidator(validate_const('start'))], pydantic.Field(alias='X-Goog-Upload-Command'), FieldMetadata(header=HeaderMetadata(style='simple', explode=False))] = 'start'
    x_goog_upload_protocol: Annotated[Annotated[Literal['resumable'], AfterValidator(validate_const('resumable'))], pydantic.Field(alias='X-Goog-Upload-Protocol'), FieldMetadata(header=HeaderMetadata(style='simple', explode=False))] = 'resumable'

    @model_serializer(mode='wrap')
    def serialize_model(self, handler):
        optional_fields = set(['api_version', 'extract', 'overwrite'])
        serialized = handler(self)
        m = {}
        for n, f in type(self).model_fields.items():
            k = f.alias or n
            val = serialized.get(k, serialized.get(n))
            if val != UNSET_SENTINEL:
                if val is not None or k not in optional_fields:
                    m[k] = val
        return m

class StartEnvironmentFileUploadResponse(BaseModel):
    headers: Dict[str, List[str]]
