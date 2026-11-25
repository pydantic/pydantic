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
from .. import BaseModel
from ...utils import validate_const
import pydantic
from pydantic import ConfigDict
from pydantic.functional_validators import AfterValidator
from typing import Any, Dict, Literal
from typing_extensions import Annotated, TypedDict

class DynamicAgentConfigParam(TypedDict):
    """Configuration for dynamic agents."""
    type: Literal['dynamic']

class DynamicAgentConfig(BaseModel):
    """Configuration for dynamic agents."""
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True, extra='allow')
    __pydantic_extra__: Dict[str, Any] = pydantic.Field(init=False)
    type: Annotated[Annotated[Literal['dynamic'], AfterValidator(validate_const('dynamic'))], pydantic.Field(alias='type')] = 'dynamic'
