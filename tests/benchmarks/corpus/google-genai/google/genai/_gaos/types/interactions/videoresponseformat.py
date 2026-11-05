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
import pydantic
from pydantic import model_serializer
from pydantic.functional_validators import AfterValidator
from typing import Literal, Optional, Union
from typing_extensions import Annotated, NotRequired, TypedDict
VideoResponseFormatAspectRatio = Union[Literal['16:9', '9:16'], UnrecognizedStr]
VideoResponseFormatDelivery = Union[Literal['inline', 'uri'], UnrecognizedStr]
Resolution = Union[Literal['360p', '720p', '1080p', '4k'], UnrecognizedStr]

class VideoResponseFormatParam(TypedDict):
    """Configuration for video output format."""
    aspect_ratio: NotRequired[VideoResponseFormatAspectRatio]
    delivery: NotRequired[VideoResponseFormatDelivery]
    duration: NotRequired[str]
    gcs_uri: NotRequired[str]
    resolution: NotRequired[Resolution]
    type: Literal['video']

class VideoResponseFormat(BaseModel):
    """Configuration for video output format."""
    aspect_ratio: Optional[VideoResponseFormatAspectRatio] = None
    delivery: Optional[VideoResponseFormatDelivery] = None
    duration: Optional[str] = None
    gcs_uri: Optional[str] = None
    resolution: Optional[Resolution] = None
    type: Annotated[Annotated[Literal['video'], AfterValidator(validate_const('video'))], pydantic.Field(alias='type')] = 'video'

    @model_serializer(mode='wrap')
    def serialize_model(self, handler):
        optional_fields = set(['aspect_ratio', 'delivery', 'duration', 'gcs_uri', 'resolution'])
        serialized = handler(self)
        m = {}
        for n, f in type(self).model_fields.items():
            k = f.alias or n
            val = serialized.get(k, serialized.get(n))
            if val != UNSET_SENTINEL:
                if val is not None or k not in optional_fields:
                    m[k] = val
        return m
