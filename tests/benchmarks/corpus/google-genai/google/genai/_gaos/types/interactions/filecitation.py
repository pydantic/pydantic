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
from typing import Any, Dict, Literal, Optional
from typing_extensions import Annotated, NotRequired, TypedDict

class FileCitationParam(TypedDict):
    """A file citation annotation."""
    custom_metadata: NotRequired[Dict[str, Any]]
    document_uri: NotRequired[str]
    end_index: NotRequired[int]
    file_name: NotRequired[str]
    media_id: NotRequired[str]
    page_number: NotRequired[int]
    source: NotRequired[str]
    start_index: NotRequired[int]
    type: Literal['file_citation']

class FileCitation(BaseModel):
    """A file citation annotation."""
    custom_metadata: Optional[Dict[str, Any]] = None
    document_uri: Optional[str] = None
    end_index: Optional[int] = None
    file_name: Optional[str] = None
    media_id: Optional[str] = None
    page_number: Optional[int] = None
    source: Optional[str] = None
    start_index: Optional[int] = None
    type: Annotated[Annotated[Literal['file_citation'], AfterValidator(validate_const('file_citation'))], pydantic.Field(alias='type')] = 'file_citation'

    @model_serializer(mode='wrap')
    def serialize_model(self, handler):
        optional_fields = set(['custom_metadata', 'document_uri', 'end_index', 'file_name', 'media_id', 'page_number', 'source', 'start_index'])
        serialized = handler(self)
        m = {}
        for n, f in type(self).model_fields.items():
            k = f.alias or n
            val = serialized.get(k, serialized.get(n))
            if val != UNSET_SENTINEL:
                if val is not None or k not in optional_fields:
                    m[k] = val
        return m
