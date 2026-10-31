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
from .exaaisearchconfig import ExaAISearchConfig, ExaAISearchConfigParam
from .parallelaisearchconfig import ParallelAISearchConfig, ParallelAISearchConfigParam
from .ragstoreconfig import RagStoreConfig, RagStoreConfigParam
from .vertexaisearchconfig import VertexAISearchConfig, VertexAISearchConfigParam
import pydantic
from pydantic import model_serializer
from pydantic.functional_validators import AfterValidator
from typing import List, Literal, Optional, Union
from typing_extensions import Annotated, NotRequired, TypedDict
RetrievalRetrievalType = Union[Literal['vertex_ai_search', 'rag_store', 'exa_ai_search', 'parallel_ai_search'], UnrecognizedStr]

class RetrievalParam(TypedDict):
    """A tool that can be used by the model to retrieve files."""
    exa_ai_search_config: NotRequired[ExaAISearchConfigParam]
    parallel_ai_search_config: NotRequired[ParallelAISearchConfigParam]
    rag_store_config: NotRequired[RagStoreConfigParam]
    retrieval_types: NotRequired[List[RetrievalRetrievalType]]
    type: Literal['retrieval']
    vertex_ai_search_config: NotRequired[VertexAISearchConfigParam]

class Retrieval(BaseModel):
    """A tool that can be used by the model to retrieve files."""
    exa_ai_search_config: Optional[ExaAISearchConfig] = None
    parallel_ai_search_config: Optional[ParallelAISearchConfig] = None
    rag_store_config: Optional[RagStoreConfig] = None
    retrieval_types: Optional[List[RetrievalRetrievalType]] = None
    type: Annotated[Annotated[Literal['retrieval'], AfterValidator(validate_const('retrieval'))], pydantic.Field(alias='type')] = 'retrieval'
    vertex_ai_search_config: Optional[VertexAISearchConfig] = None

    @model_serializer(mode='wrap')
    def serialize_model(self, handler):
        optional_fields = set(['exa_ai_search_config', 'parallel_ai_search_config', 'rag_store_config', 'retrieval_types', 'vertex_ai_search_config'])
        serialized = handler(self)
        m = {}
        for n, f in type(self).model_fields.items():
            k = f.alias or n
            val = serialized.get(k, serialized.get(n))
            if val != UNSET_SENTINEL:
                if val is not None or k not in optional_fields:
                    m[k] = val
        return m
