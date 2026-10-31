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
from .filter_ import Filter, FilterParam
from .hybridsearch import HybridSearch, HybridSearchParam
from .ranking import Ranking, RankingParam
import pydantic
from pydantic import model_serializer
from typing import Optional
from typing_extensions import Annotated, NotRequired, TypedDict

class RagRetrievalConfigParam(TypedDict):
    """Specifies the context retrieval config."""
    filter_: NotRequired[FilterParam]
    hybrid_search: NotRequired[HybridSearchParam]
    ranking: NotRequired[RankingParam]
    top_k: NotRequired[int]

class RagRetrievalConfig(BaseModel):
    """Specifies the context retrieval config."""
    filter_: Annotated[Optional[Filter], pydantic.Field(alias='filter')] = None
    hybrid_search: Optional[HybridSearch] = None
    ranking: Optional[Ranking] = None
    top_k: Optional[int] = None

    @model_serializer(mode='wrap')
    def serialize_model(self, handler):
        optional_fields = set(['filter', 'hybrid_search', 'ranking', 'top_k'])
        serialized = handler(self)
        m = {}
        for n, f in type(self).model_fields.items():
            k = f.alias or n
            val = serialized.get(k, serialized.get(n))
            if val != UNSET_SENTINEL:
                if val is not None or k not in optional_fields:
                    m[k] = val
        return m
