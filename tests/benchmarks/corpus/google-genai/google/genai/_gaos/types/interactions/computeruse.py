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
from typing import List, Literal, Optional, Union
from typing_extensions import Annotated, NotRequired, TypedDict
DisabledSafetyPolicy = Union[Literal['financial_transactions', 'sensitive_data_modification', 'communication_tool', 'account_creation', 'data_modification', 'user_consent_management', 'legal_terms_and_agreements'], UnrecognizedStr]
EnvironmentEnum = Union[Literal['browser', 'mobile', 'desktop'], UnrecognizedStr]

class ComputerUseParam(TypedDict):
    """A tool that can be used by the model to interact with the computer."""
    disabled_safety_policies: NotRequired[List[DisabledSafetyPolicy]]
    enable_prompt_injection_detection: NotRequired[bool]
    environment: NotRequired[EnvironmentEnum]
    excluded_predefined_functions: NotRequired[List[str]]
    type: Literal['computer_use']

class ComputerUse(BaseModel):
    """A tool that can be used by the model to interact with the computer."""
    disabled_safety_policies: Optional[List[DisabledSafetyPolicy]] = None
    enable_prompt_injection_detection: Optional[bool] = None
    environment: Optional[EnvironmentEnum] = None
    excluded_predefined_functions: Optional[List[str]] = None
    type: Annotated[Annotated[Literal['computer_use'], AfterValidator(validate_const('computer_use'))], pydantic.Field(alias='type')] = 'computer_use'

    @model_serializer(mode='wrap')
    def serialize_model(self, handler):
        optional_fields = set(['disabled_safety_policies', 'enable_prompt_injection_detection', 'environment', 'excluded_predefined_functions'])
        serialized = handler(self)
        m = {}
        for n, f in type(self).model_fields.items():
            k = f.alias or n
            val = serialized.get(k, serialized.get(n))
            if val != UNSET_SENTINEL:
                if val is not None or k not in optional_fields:
                    m[k] = val
        return m
