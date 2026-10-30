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
from .transcriptionmode import TranscriptionMode, TranscriptionModeParam
import pydantic
from pydantic import model_serializer
from typing import List, Literal, Optional, Union
from typing_extensions import Annotated, NotRequired, TypeAliasType, TypedDict
TranscriptionConfigModeEnum = Union[Literal['verbatim', 'smart'], UnrecognizedStr]
TranscriptionConfigModeParam = TypeAliasType('TranscriptionConfigModeParam', Union[TranscriptionModeParam, TranscriptionConfigModeEnum])
TranscriptionConfigMode = TypeAliasType('TranscriptionConfigMode', Union[TranscriptionMode, TranscriptionConfigModeEnum])

class TranscriptionConfigParam(TypedDict):
    """Configuration for speech recognition (transcription)."""
    adaptation_phrases: NotRequired[List[str]]
    custom_vocabulary: NotRequired[List[str]]
    diarization_mode: NotRequired[str]
    language_codes: NotRequired[List[str]]
    language_hints: NotRequired[List[str]]
    mode: NotRequired[TranscriptionConfigModeParam]
    timestamp_granularities: NotRequired[List[str]]

class TranscriptionConfig(BaseModel):
    """Configuration for speech recognition (transcription)."""
    adaptation_phrases: Annotated[Optional[List[str]], pydantic.Field(deprecated='warning: ** DEPRECATED ** - This will be removed in a future release, please migrate away from it as soon as possible.')] = None
    custom_vocabulary: Optional[List[str]] = None
    diarization_mode: Annotated[Optional[str], pydantic.Field(deprecated='warning: ** DEPRECATED ** - This will be removed in a future release, please migrate away from it as soon as possible.')] = None
    language_codes: Optional[List[str]] = None
    language_hints: Annotated[Optional[List[str]], pydantic.Field(deprecated='warning: ** DEPRECATED ** - This will be removed in a future release, please migrate away from it as soon as possible.')] = None
    mode: Optional[TranscriptionConfigMode] = None
    timestamp_granularities: Annotated[Optional[List[str]], pydantic.Field(deprecated='warning: ** DEPRECATED ** - This will be removed in a future release, please migrate away from it as soon as possible.')] = None

    @model_serializer(mode='wrap')
    def serialize_model(self, handler):
        optional_fields = set(['adaptation_phrases', 'custom_vocabulary', 'diarization_mode', 'language_codes', 'language_hints', 'mode', 'timestamp_granularities'])
        serialized = handler(self)
        m = {}
        for n, f in type(self).model_fields.items():
            k = f.alias or n
            val = serialized.get(k, serialized.get(n))
            if val != UNSET_SENTINEL:
                if val is not None or k not in optional_fields:
                    m[k] = val
        return m
