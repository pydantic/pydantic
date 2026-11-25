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
from ..interactions import usage as interactions_usage
from .audiodata import AudioData
from .pitch import Pitch
from .promptedvoice import PromptedVoice
from .voicetype import VoiceType
from datetime import datetime
from pydantic import model_serializer
from typing import Optional

class VoiceOutput(BaseModel):
    """A voice resource representing either a custom voice (created via
    `CreateVoice`) or a prebuilt system voice (returned by `ListVoices`).
    """
    type: VoiceType
    accent: Optional[str] = None
    context: Optional[str] = None
    description: Optional[str] = None
    display_name: Optional[str] = None
    expire_time: Optional[datetime] = None
    gender: Optional[str] = None
    id: Optional[str] = None
    key: Optional[str] = None
    language_code: Optional[str] = None
    model: Optional[str] = None
    persona: Optional[str] = None
    pitch: Optional[Pitch] = None
    prompted: Optional[PromptedVoice] = None
    region_code: Optional[str] = None
    sample_audio: Optional[AudioData] = None
    usage: Optional[interactions_usage.Usage] = None

    @model_serializer(mode='wrap')
    def serialize_model(self, handler):
        optional_fields = set(['accent', 'context', 'description', 'display_name', 'expire_time', 'gender', 'id', 'key', 'language_code', 'model', 'persona', 'pitch', 'prompted', 'region_code', 'sample_audio', 'usage'])
        serialized = handler(self)
        m = {}
        for n, f in type(self).model_fields.items():
            k = f.alias or n
            val = serialized.get(k, serialized.get(n))
            if val != UNSET_SENTINEL:
                if val is not None or k not in optional_fields:
                    m[k] = val
        return m
