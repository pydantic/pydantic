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
from ..interactions import createagentinteraction as interactions_createagentinteraction
from datetime import datetime
from pydantic import model_serializer
from typing import Literal, Optional, Union
TriggerStatus = Union[Literal['active', 'paused', 'error'], UnrecognizedStr]

class Trigger(BaseModel):
    """A trigger configuration that is scheduled to run an agent."""
    id: str
    interaction: interactions_createagentinteraction.CreateAgentInteraction
    schedule: str
    time_zone: str
    consecutive_failure_count: Optional[int] = None
    create_time: Optional[datetime] = None
    display_name: Optional[str] = None
    environment_id: Optional[str] = None
    execution_timeout_seconds: Optional[int] = None
    last_pause_time: Optional[datetime] = None
    last_resume_time: Optional[datetime] = None
    last_run_time: Optional[datetime] = None
    max_consecutive_failures: Optional[int] = None
    next_run_time: Optional[datetime] = None
    previous_interaction_id: Optional[str] = None
    status: Optional[TriggerStatus] = None
    update_time: Optional[datetime] = None

    @model_serializer(mode='wrap')
    def serialize_model(self, handler):
        optional_fields = set(['consecutive_failure_count', 'create_time', 'display_name', 'environment_id', 'execution_timeout_seconds', 'last_pause_time', 'last_resume_time', 'last_run_time', 'max_consecutive_failures', 'next_run_time', 'previous_interaction_id', 'status', 'update_time'])
        serialized = handler(self)
        m = {}
        for n, f in type(self).model_fields.items():
            k = f.alias or n
            val = serialized.get(k, serialized.get(n))
            if val != UNSET_SENTINEL:
                if val is not None or k not in optional_fields:
                    m[k] = val
        return m
