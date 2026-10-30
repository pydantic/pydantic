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
from .retrievalcallarguments import RetrievalCallArguments
import pydantic
from pydantic import model_serializer
from pydantic.functional_validators import AfterValidator
from typing import Literal, Optional, Union
from typing_extensions import Annotated
RetrievalCallDeltaRetrievalType = Union[Literal['vertex_ai_search', 'rag_store', 'exa_ai_search', 'parallel_ai_search'], UnrecognizedStr]

class RetrievalCallDelta(BaseModel):
    """Used by Vertex Retrieval tools such as Parallel AI, Exa AI, Vertex AI Search,
    etc. RetrievalType decides which tool is used.
    """
    arguments: RetrievalCallArguments
    retrieval_type: Optional[RetrievalCallDeltaRetrievalType] = None
    signature: Optional[str] = None
    type: Annotated[Annotated[Literal['retrieval_call'], AfterValidator(validate_const('retrieval_call'))], pydantic.Field(alias='type')] = 'retrieval_call'

    @model_serializer(mode='wrap')
    def serialize_model(self, handler):
        optional_fields = set(['retrieval_type', 'signature'])
        serialized = handler(self)
        m = {}
        for n, f in type(self).model_fields.items():
            k = f.alias or n
            val = serialized.get(k, serialized.get(n))
            if val != UNSET_SENTINEL:
                if val is not None or k not in optional_fields:
                    m[k] = val
        return m
