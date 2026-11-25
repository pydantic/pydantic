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
from pydantic import ConfigDict, model_serializer
from pydantic import BaseModel as PydanticBaseModel
from pydantic_core import core_schema
from typing import Any

class BaseModel(PydanticBaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True, protected_namespaces=(), extra='allow')

class Unset(BaseModel):

    @model_serializer(mode='plain')
    def serialize_model(self):
        return UNSET_SENTINEL
UNSET_SENTINEL = '~?~unset~?~sentinel~?~'

class UnrecognizedStr(str):

    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type: Any, _handler: Any) -> core_schema.CoreSchema:

        def validate_lax(v: Any) -> 'UnrecognizedStr':
            if isinstance(v, cls):
                return v
            return cls(str(v))
        return core_schema.lax_or_strict_schema(lax_schema=core_schema.chain_schema([core_schema.str_schema(), core_schema.no_info_plain_validator_function(validate_lax)]), strict_schema=core_schema.none_schema(), serialization=core_schema.plain_serializer_function_ser_schema(str))
