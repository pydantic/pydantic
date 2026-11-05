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
from .mediaprocessing import MediaProcessing, MediaProcessingParam
from .mediaresolution import MediaResolution
import pydantic
from pydantic import model_serializer
from pydantic.functional_validators import AfterValidator
from typing import Literal, Optional, Union
from typing_extensions import Annotated, NotRequired, TypeAliasType, TypedDict
VideoContentMimeType = Union[Literal['video/mp4', 'video/mpeg', 'video/mpg', 'video/mov', 'video/avi', 'video/x-flv', 'video/webm', 'video/wmv', 'video/3gpp'], UnrecognizedStr]
ProcessingEnum = Union[Literal['static', 'agentic'], UnrecognizedStr]
ProcessingParam = TypeAliasType('ProcessingParam', Union[MediaProcessingParam, ProcessingEnum])
Processing = TypeAliasType('Processing', Union[MediaProcessing, ProcessingEnum])

class VideoContentParam(TypedDict):
    """A video content block."""
    data: NotRequired[Union[str, Base64FileInput]]
    mime_type: NotRequired[VideoContentMimeType]
    name: NotRequired[str]
    processing: NotRequired[ProcessingParam]
    resolution: NotRequired[MediaResolution]
    type: Literal['video']
    uri: NotRequired[str]

class VideoContent(BaseModel):
    """A video content block."""
    data: Optional[Base64EncodedString] = None
    mime_type: Optional[VideoContentMimeType] = None
    name: Optional[str] = None
    processing: Optional[Processing] = None
    resolution: Optional[MediaResolution] = None
    type: Annotated[Annotated[Literal['video'], AfterValidator(validate_const('video'))], pydantic.Field(alias='type')] = 'video'
    uri: Optional[str] = None

    @model_serializer(mode='wrap')
    def serialize_model(self, handler):
        optional_fields = set(['data', 'mime_type', 'name', 'processing', 'resolution', 'uri'])
        serialized = handler(self)
        m = {}
        for n, f in type(self).model_fields.items():
            k = f.alias or n
            val = serialized.get(k, serialized.get(n))
            if val != UNSET_SENTINEL:
                if val is not None or k not in optional_fields:
                    m[k] = val
        return m
