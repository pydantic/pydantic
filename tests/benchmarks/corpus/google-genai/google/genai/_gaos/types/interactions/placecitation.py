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
from .reviewsnippet import ReviewSnippet, ReviewSnippetParam
import pydantic
from pydantic import model_serializer
from pydantic.functional_validators import AfterValidator
from typing import List, Literal, Optional
from typing_extensions import Annotated, NotRequired, TypedDict

class PlaceCitationParam(TypedDict):
    """A place citation annotation."""
    end_index: NotRequired[int]
    name: NotRequired[str]
    place_id: NotRequired[str]
    review_snippets: NotRequired[List[ReviewSnippetParam]]
    start_index: NotRequired[int]
    type: Literal['place_citation']
    url: NotRequired[str]

class PlaceCitation(BaseModel):
    """A place citation annotation."""
    end_index: Optional[int] = None
    name: Optional[str] = None
    place_id: Optional[str] = None
    review_snippets: Optional[List[ReviewSnippet]] = None
    start_index: Optional[int] = None
    type: Annotated[Annotated[Literal['place_citation'], AfterValidator(validate_const('place_citation'))], pydantic.Field(alias='type')] = 'place_citation'
    url: Optional[str] = None

    @model_serializer(mode='wrap')
    def serialize_model(self, handler):
        optional_fields = set(['end_index', 'name', 'place_id', 'review_snippets', 'start_index', 'url'])
        serialized = handler(self)
        m = {}
        for n, f in type(self).model_fields.items():
            k = f.alias or n
            val = serialized.get(k, serialized.get(n))
            if val != UNSET_SENTINEL:
                if val is not None or k not in optional_fields:
                    m[k] = val
        return m
