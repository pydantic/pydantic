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
from .imageconfig import ImageConfig, ImageConfigParam
from .speakerconfig import SpeakerConfig, SpeakerConfigParam
from .speechconfig import SpeechConfig, SpeechConfigParam
from .thinkinglevel import ThinkingLevel
from .thinkingsummaries import ThinkingSummaries
from .toolchoiceconfig import ToolChoiceConfig, ToolChoiceConfigParam
from .toolchoicetype import ToolChoiceType
from .transcriptionconfig import TranscriptionConfig, TranscriptionConfigParam
from .videoconfig import VideoConfig, VideoConfigParam
import pydantic
from pydantic import model_serializer
from typing import List, Optional, Union
from typing_extensions import Annotated, NotRequired, TypeAliasType, TypedDict
SpeechConfigUnionParam = TypeAliasType('SpeechConfigUnionParam', Union[SpeakerConfigParam, List[SpeechConfigParam]])
SpeechConfigUnion = TypeAliasType('SpeechConfigUnion', Union[SpeakerConfig, List[SpeechConfig]])
ToolChoiceParam = TypeAliasType('ToolChoiceParam', Union[ToolChoiceConfigParam, ToolChoiceType])
ToolChoice = TypeAliasType('ToolChoice', Union[ToolChoiceConfig, ToolChoiceType])

class GenerationConfigParam(TypedDict):
    """Configuration parameters for model interactions."""
    image_config: NotRequired[ImageConfigParam]
    max_output_tokens: NotRequired[int]
    seed: NotRequired[int]
    speech_config: NotRequired[SpeechConfigUnionParam]
    stop_sequences: NotRequired[List[str]]
    temperature: NotRequired[float]
    thinking_level: NotRequired[ThinkingLevel]
    thinking_summaries: NotRequired[ThinkingSummaries]
    tool_choice: NotRequired[ToolChoiceParam]
    top_p: NotRequired[float]
    transcription_config: NotRequired[TranscriptionConfigParam]
    video_config: NotRequired[VideoConfigParam]

class GenerationConfig(BaseModel):
    """Configuration parameters for model interactions."""
    image_config: Annotated[Optional[ImageConfig], pydantic.Field(deprecated='warning: ** DEPRECATED ** - This will be removed in a future release, please migrate away from it as soon as possible.')] = None
    max_output_tokens: Optional[int] = None
    seed: Optional[int] = None
    speech_config: Optional[SpeechConfigUnion] = None
    stop_sequences: Optional[List[str]] = None
    temperature: Annotated[Optional[float], pydantic.Field(deprecated='warning: ** DEPRECATED ** - This will be removed in a future release, please migrate away from it as soon as possible.')] = None
    thinking_level: Optional[ThinkingLevel] = None
    thinking_summaries: Optional[ThinkingSummaries] = None
    tool_choice: Optional[ToolChoice] = None
    top_p: Annotated[Optional[float], pydantic.Field(deprecated='warning: ** DEPRECATED ** - This will be removed in a future release, please migrate away from it as soon as possible.')] = None
    transcription_config: Optional[TranscriptionConfig] = None
    video_config: Optional[VideoConfig] = None

    @model_serializer(mode='wrap')
    def serialize_model(self, handler):
        optional_fields = set(['image_config', 'max_output_tokens', 'seed', 'speech_config', 'stop_sequences', 'temperature', 'thinking_level', 'thinking_summaries', 'tool_choice', 'top_p', 'transcription_config', 'video_config'])
        serialized = handler(self)
        m = {}
        for n, f in type(self).model_fields.items():
            k = f.alias or n
            val = serialized.get(k, serialized.get(n))
            if val != UNSET_SENTINEL:
                if val is not None or k not in optional_fields:
                    m[k] = val
        return m
