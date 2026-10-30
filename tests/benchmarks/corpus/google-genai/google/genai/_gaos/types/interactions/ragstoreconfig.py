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
from .ragresource import RagResource, RagResourceParam
from .ragretrievalconfig import RagRetrievalConfig, RagRetrievalConfigParam
import pydantic
from pydantic import model_serializer
from typing import List, Optional
from typing_extensions import Annotated, NotRequired, TypedDict

class RagStoreConfigParam(TypedDict):
    """Use to specify configuration for RAG Store."""
    rag_resources: NotRequired[List[RagResourceParam]]
    rag_retrieval_config: NotRequired[RagRetrievalConfigParam]
    similarity_top_k: NotRequired[int]
    vector_distance_threshold: NotRequired[float]

class RagStoreConfig(BaseModel):
    """Use to specify configuration for RAG Store."""
    rag_resources: Optional[List[RagResource]] = None
    rag_retrieval_config: Optional[RagRetrievalConfig] = None
    similarity_top_k: Annotated[Optional[int], pydantic.Field(deprecated='warning: ** DEPRECATED ** - This will be removed in a future release, please migrate away from it as soon as possible.')] = None
    vector_distance_threshold: Annotated[Optional[float], pydantic.Field(deprecated='warning: ** DEPRECATED ** - This will be removed in a future release, please migrate away from it as soon as possible.')] = None

    @model_serializer(mode='wrap')
    def serialize_model(self, handler):
        optional_fields = set(['rag_resources', 'rag_retrieval_config', 'similarity_top_k', 'vector_distance_threshold'])
        serialized = handler(self)
        m = {}
        for n, f in type(self).model_fields.items():
            k = f.alias or n
            val = serialized.get(k, serialized.get(n))
            if val != UNSET_SENTINEL:
                if val is not None or k not in optional_fields:
                    m[k] = val
        return m
