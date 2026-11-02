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
from .groundingtoolcount import GroundingToolCount, GroundingToolCountTypedDict
from .modalitytokens import ModalityTokens, ModalityTokensTypedDict
from pydantic import model_serializer
from typing import List, Optional
from typing_extensions import NotRequired, TypedDict

class UsageTypedDict(TypedDict):
    """Statistics on the interaction request's token usage."""
    cached_tokens_by_modality: NotRequired[List[ModalityTokensTypedDict]]
    grounding_tool_count: NotRequired[List[GroundingToolCountTypedDict]]
    initial_input_tokens: NotRequired[int]
    input_tokens_by_modality: NotRequired[List[ModalityTokensTypedDict]]
    output_tokens_by_modality: NotRequired[List[ModalityTokensTypedDict]]
    tool_use_tokens_by_modality: NotRequired[List[ModalityTokensTypedDict]]
    total_cached_tokens: NotRequired[int]
    total_input_tokens: NotRequired[int]
    total_output_tokens: NotRequired[int]
    total_thought_tokens: NotRequired[int]
    total_tokens: NotRequired[int]
    total_tool_use_tokens: NotRequired[int]

class Usage(BaseModel):
    """Statistics on the interaction request's token usage."""
    cached_tokens_by_modality: Optional[List[ModalityTokens]] = None
    grounding_tool_count: Optional[List[GroundingToolCount]] = None
    initial_input_tokens: Optional[int] = None
    input_tokens_by_modality: Optional[List[ModalityTokens]] = None
    output_tokens_by_modality: Optional[List[ModalityTokens]] = None
    tool_use_tokens_by_modality: Optional[List[ModalityTokens]] = None
    total_cached_tokens: Optional[int] = None
    total_input_tokens: Optional[int] = None
    total_output_tokens: Optional[int] = None
    total_thought_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    total_tool_use_tokens: Optional[int] = None

    @model_serializer(mode='wrap')
    def serialize_model(self, handler):
        optional_fields = set(['cached_tokens_by_modality', 'grounding_tool_count', 'initial_input_tokens', 'input_tokens_by_modality', 'output_tokens_by_modality', 'tool_use_tokens_by_modality', 'total_cached_tokens', 'total_input_tokens', 'total_output_tokens', 'total_thought_tokens', 'total_tokens', 'total_tool_use_tokens'])
        serialized = handler(self)
        m = {}
        for n, f in type(self).model_fields.items():
            k = f.alias or n
            val = serialized.get(k, serialized.get(n))
            if val != UNSET_SENTINEL:
                if val is not None or k not in optional_fields:
                    m[k] = val
        return m
