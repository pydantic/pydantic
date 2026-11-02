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
from .. import Base64EncodedString, Base64FileInput, BaseModel, UNSET_SENTINEL, UnrecognizedStr
from ...utils import validate_const
import pydantic
from pydantic import model_serializer
from pydantic.functional_validators import AfterValidator
from typing import Literal, Optional, Union
from typing_extensions import Annotated, NotRequired, TypedDict
AudioContentMimeType = Union[Literal['audio/wav', 'audio/mp3', 'audio/aiff', 'audio/aac', 'audio/ogg', 'audio/flac', 'audio/mpeg', 'audio/m4a', 'audio/l16', 'audio/opus', 'audio/alaw', 'audio/mulaw', 'audio/webm'], UnrecognizedStr]

class AudioContentParam(TypedDict):
    """An audio content block."""
    channels: NotRequired[int]
    data: NotRequired[Union[str, Base64FileInput]]
    mime_type: NotRequired[AudioContentMimeType]
    sample_rate: NotRequired[int]
    type: Literal['audio']
    uri: NotRequired[str]

class AudioContent(BaseModel):
    """An audio content block."""
    channels: Optional[int] = None
    data: Optional[Base64EncodedString] = None
    mime_type: Optional[AudioContentMimeType] = None
    sample_rate: Optional[int] = None
    type: Annotated[Annotated[Literal['audio'], AfterValidator(validate_const('audio'))], pydantic.Field(alias='type')] = 'audio'
    uri: Optional[str] = None

    @model_serializer(mode='wrap')
    def serialize_model(self, handler):
        optional_fields = set(['channels', 'data', 'mime_type', 'sample_rate', 'uri'])
        serialized = handler(self)
        m = {}
        for n, f in type(self).model_fields.items():
            k = f.alias or n
            val = serialized.get(k, serialized.get(n))
            if val != UNSET_SENTINEL:
                if val is not None or k not in optional_fields:
                    m[k] = val
        return m
