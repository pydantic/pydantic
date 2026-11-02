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
from datetime import datetime
from pydantic import model_serializer
from typing import Literal, Optional, Union
TriggerExecutionStatus = Union[Literal['in_progress', 'completed', 'failed', 'skipped', 'timed_out'], UnrecognizedStr]

class TriggerExecution(BaseModel):
    """An execution instance of a trigger."""
    id: str
    trigger_id: str
    end_time: Optional[datetime] = None
    environment_id: Optional[str] = None
    error: Optional[str] = None
    interaction_id: Optional[str] = None
    scheduled_time: Optional[datetime] = None
    start_time: Optional[datetime] = None
    status: Optional[TriggerExecutionStatus] = None

    @model_serializer(mode='wrap')
    def serialize_model(self, handler):
        optional_fields = set(['end_time', 'environment_id', 'error', 'interaction_id', 'scheduled_time', 'start_time', 'status'])
        serialized = handler(self)
        m = {}
        for n, f in type(self).model_fields.items():
            k = f.alias or n
            val = serialized.get(k, serialized.get(n))
            if val != UNSET_SENTINEL:
                if val is not None or k not in optional_fields:
                    m[k] = val
        return m
