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
from ..interactions import createagentinteraction as interactions_createagentinteraction
from pydantic import model_serializer
from typing import Optional
from typing_extensions import NotRequired, TypedDict

class TriggerCreateParamsParam(TypedDict):
    """Parameters for creating a trigger."""
    interaction: interactions_createagentinteraction.CreateAgentInteractionParam
    schedule: str
    time_zone: str
    display_name: NotRequired[str]
    environment_id: NotRequired[str]
    execution_timeout_seconds: NotRequired[int]
    max_consecutive_failures: NotRequired[int]

class TriggerCreateParams(BaseModel):
    """Parameters for creating a trigger."""
    interaction: interactions_createagentinteraction.CreateAgentInteraction
    schedule: str
    time_zone: str
    display_name: Optional[str] = None
    environment_id: Optional[str] = None
    execution_timeout_seconds: Optional[int] = None
    max_consecutive_failures: Optional[int] = None

    @model_serializer(mode='wrap')
    def serialize_model(self, handler):
        optional_fields = set(['display_name', 'environment_id', 'execution_timeout_seconds', 'max_consecutive_failures'])
        serialized = handler(self)
        m = {}
        for n, f in type(self).model_fields.items():
            k = f.alias or n
            val = serialized.get(k, serialized.get(n))
            if val != UNSET_SENTINEL:
                if val is not None or k not in optional_fields:
                    m[k] = val
        return m
