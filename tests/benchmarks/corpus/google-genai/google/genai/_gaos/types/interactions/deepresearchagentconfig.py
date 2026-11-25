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
from .thinkingsummaries import ThinkingSummaries
import pydantic
from pydantic import model_serializer
from pydantic.functional_validators import AfterValidator
from typing import Literal, Optional, Union
from typing_extensions import Annotated, NotRequired, TypedDict
Visualization = Union[Literal['off', 'auto'], UnrecognizedStr]

class DeepResearchAgentConfigParam(TypedDict):
    """Configuration for the Deep Research agent."""
    collaborative_planning: NotRequired[bool]
    enable_bigquery_tool: NotRequired[bool]
    thinking_summaries: NotRequired[ThinkingSummaries]
    type: Literal['deep-research']
    visualization: NotRequired[Visualization]

class DeepResearchAgentConfig(BaseModel):
    """Configuration for the Deep Research agent."""
    collaborative_planning: Optional[bool] = None
    enable_bigquery_tool: Optional[bool] = None
    thinking_summaries: Optional[ThinkingSummaries] = None
    type: Annotated[Annotated[Literal['deep-research'], AfterValidator(validate_const('deep-research'))], pydantic.Field(alias='type')] = 'deep-research'
    visualization: Optional[Visualization] = None

    @model_serializer(mode='wrap')
    def serialize_model(self, handler):
        optional_fields = set(['collaborative_planning', 'enable_bigquery_tool', 'thinking_summaries', 'visualization'])
        serialized = handler(self)
        m = {}
        for n, f in type(self).model_fields.items():
            k = f.alias or n
            val = serialized.get(k, serialized.get(n))
            if val != UNSET_SENTINEL:
                if val is not None or k not in optional_fields:
                    m[k] = val
        return m
