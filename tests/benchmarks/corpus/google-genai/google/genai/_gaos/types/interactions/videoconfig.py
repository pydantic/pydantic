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
from typing import Literal, Optional, Union
from typing_extensions import NotRequired, TypedDict
Task = Union[Literal['text_to_video', 'image_to_video', 'reference_to_video', 'edit', 'extend', 'upscale'], UnrecognizedStr]

class VideoConfigParam(TypedDict):
    """Configuration options for video generation."""
    task: NotRequired[Task]

class VideoConfig(BaseModel):
    """Configuration options for video generation."""
    task: Optional[Task] = None

    @model_serializer(mode='wrap')
    def serialize_model(self, handler):
        optional_fields = set(['task'])
        serialized = handler(self)
        m = {}
        for n, f in type(self).model_fields.items():
            k = f.alias or n
            val = serialized.get(k, serialized.get(n))
            if val != UNSET_SENTINEL:
                if val is not None or k not in optional_fields:
                    m[k] = val
        return m
