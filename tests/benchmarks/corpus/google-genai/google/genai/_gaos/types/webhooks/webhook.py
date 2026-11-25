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
from .signingsecret import SigningSecret, SigningSecretTypedDict
from datetime import datetime
from pydantic import model_serializer
from typing import List, Literal, Optional, Union
from typing_extensions import NotRequired, TypedDict
WebhookState = Union[Literal['enabled', 'disabled', 'disabled_due_to_failed_deliveries'], UnrecognizedStr]
WebhookSubscribedEvent = Union[Literal['batch.succeeded', 'batch.expired', 'batch.failed', 'interaction.requires_action', 'interaction.completed', 'interaction.failed', 'video.generated'], UnrecognizedStr]

class WebhookTypedDict(TypedDict):
    """A Webhook resource."""
    subscribed_events: List[WebhookSubscribedEvent]
    uri: str
    create_time: NotRequired[datetime]
    id: NotRequired[str]
    name: NotRequired[str]
    new_signing_secret: NotRequired[str]
    signing_secrets: NotRequired[List[SigningSecretTypedDict]]
    state: NotRequired[WebhookState]
    update_time: NotRequired[datetime]

class Webhook(BaseModel):
    """A Webhook resource."""
    subscribed_events: List[WebhookSubscribedEvent]
    uri: str
    create_time: Optional[datetime] = None
    id: Optional[str] = None
    name: Optional[str] = None
    new_signing_secret: Optional[str] = None
    signing_secrets: Optional[List[SigningSecret]] = None
    state: Optional[WebhookState] = None
    update_time: Optional[datetime] = None

    @model_serializer(mode='wrap')
    def serialize_model(self, handler):
        optional_fields = set(['create_time', 'id', 'name', 'new_signing_secret', 'signing_secrets', 'state', 'update_time'])
        serialized = handler(self)
        m = {}
        for n, f in type(self).model_fields.items():
            k = f.alias or n
            val = serialized.get(k, serialized.get(n))
            if val != UNSET_SENTINEL:
                if val is not None or k not in optional_fields:
                    m[k] = val
        return m

class WebhookInputParam(TypedDict):
    """A Webhook resource."""
    subscribed_events: List[WebhookSubscribedEvent]
    uri: str
    name: NotRequired[str]

class WebhookInput(BaseModel):
    """A Webhook resource."""
    subscribed_events: List[WebhookSubscribedEvent]
    uri: str
    name: Optional[str] = None

    @model_serializer(mode='wrap')
    def serialize_model(self, handler):
        optional_fields = set(['name'])
        serialized = handler(self)
        m = {}
        for n, f in type(self).model_fields.items():
            k = f.alias or n
            val = serialized.get(k, serialized.get(n))
            if val != UNSET_SENTINEL:
                if val is not None or k not in optional_fields:
                    m[k] = val
        return m
