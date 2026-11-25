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
from pydantic import model_serializer
from typing import List, Literal, Optional, Union
from typing_extensions import NotRequired, TypedDict
WebhookUpdateState = Literal['enabled', 'disabled', 'disabled_due_to_failed_deliveries']
WebhookUpdateSubscribedEvent = Union[Literal['batch.succeeded', 'batch.expired', 'batch.failed', 'interaction.requires_action', 'interaction.completed', 'interaction.failed', 'video.generated'], UnrecognizedStr]

class WebhookUpdateParam(TypedDict):
    name: NotRequired[str]
    state: NotRequired[WebhookUpdateState]
    subscribed_events: NotRequired[List[WebhookUpdateSubscribedEvent]]
    uri: NotRequired[str]

class WebhookUpdate(BaseModel):
    name: Optional[str] = None
    state: Optional[WebhookUpdateState] = None
    subscribed_events: Optional[List[WebhookUpdateSubscribedEvent]] = None
    uri: Optional[str] = None

    @model_serializer(mode='wrap')
    def serialize_model(self, handler):
        optional_fields = set(['name', 'state', 'subscribed_events', 'uri'])
        serialized = handler(self)
        m = {}
        for n, f in type(self).model_fields.items():
            k = f.alias or n
            val = serialized.get(k, serialized.get(n))
            if val != UNSET_SENTINEL:
                if val is not None or k not in optional_fields:
                    m[k] = val
        return m
