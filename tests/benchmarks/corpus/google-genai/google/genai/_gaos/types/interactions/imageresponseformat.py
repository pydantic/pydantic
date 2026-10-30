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
ImageResponseFormatAspectRatio = Union[Literal['1:1', '2:3', '3:2', '3:4', '4:3', '4:5', '5:4', '9:16', '16:9', '21:9', '1:8', '8:1', '1:4', '4:1'], UnrecognizedStr]
ImageResponseFormatDelivery = Union[Literal['inline', 'uri'], UnrecognizedStr]
ImageResponseFormatImageSize = Union[Literal['512', '1K', '2K', '4K'], UnrecognizedStr]
ImageResponseFormatMimeType = Union[Literal['image/jpeg',], UnrecognizedStr]

class ImageResponseFormatParam(TypedDict):
    """Configuration for image output format."""
    aspect_ratio: NotRequired[ImageResponseFormatAspectRatio]
    delivery: NotRequired[ImageResponseFormatDelivery]
    image_size: NotRequired[ImageResponseFormatImageSize]
    mime_type: NotRequired[ImageResponseFormatMimeType]
    type: Literal['image']

class ImageResponseFormat(BaseModel):
    """Configuration for image output format."""
    aspect_ratio: Optional[ImageResponseFormatAspectRatio] = None
    delivery: Optional[ImageResponseFormatDelivery] = None
    image_size: Optional[ImageResponseFormatImageSize] = None
    mime_type: Optional[ImageResponseFormatMimeType] = None
    type: Annotated[Annotated[Literal['image'], AfterValidator(validate_const('image'))], pydantic.Field(alias='type')] = 'image'

    @model_serializer(mode='wrap')
    def serialize_model(self, handler):
        optional_fields = set(['aspect_ratio', 'delivery', 'image_size', 'mime_type'])
        serialized = handler(self)
        m = {}
        for n, f in type(self).model_fields.items():
            k = f.alias or n
            val = serialized.get(k, serialized.get(n))
            if val != UNSET_SENTINEL:
                if val is not None or k not in optional_fields:
                    m[k] = val
        return m
