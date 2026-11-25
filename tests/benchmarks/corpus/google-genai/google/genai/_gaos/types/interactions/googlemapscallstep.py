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
from .. import Base64EncodedString, Base64FileInput, BaseModel, UNSET_SENTINEL
from ...utils import validate_const
from .googlemapscallarguments import GoogleMapsCallArguments, GoogleMapsCallArgumentsParam
import pydantic
from pydantic import model_serializer
from pydantic.functional_validators import AfterValidator
from typing import Literal, Optional, Union
from typing_extensions import Annotated, NotRequired, TypedDict

class GoogleMapsCallStepParam(TypedDict):
    """Google Maps call step."""
    id: str
    arguments: NotRequired[GoogleMapsCallArgumentsParam]
    signature: NotRequired[Union[str, Base64FileInput]]
    type: Literal['google_maps_call']

class GoogleMapsCallStep(BaseModel):
    """Google Maps call step."""
    id: str
    arguments: Optional[GoogleMapsCallArguments] = None
    signature: Optional[Base64EncodedString] = None
    type: Annotated[Annotated[Literal['google_maps_call'], AfterValidator(validate_const('google_maps_call'))], pydantic.Field(alias='type')] = 'google_maps_call'

    @model_serializer(mode='wrap')
    def serialize_model(self, handler):
        optional_fields = set(['arguments', 'signature'])
        serialized = handler(self)
        m = {}
        for n, f in type(self).model_fields.items():
            k = f.alias or n
            val = serialized.get(k, serialized.get(n))
            if val != UNSET_SENTINEL:
                if val is not None or k not in optional_fields:
                    m[k] = val
        return m
