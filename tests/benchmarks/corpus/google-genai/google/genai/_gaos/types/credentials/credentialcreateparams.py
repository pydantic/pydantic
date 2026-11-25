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
from .environmentvariableconfig import EnvironmentVariableConfig, EnvironmentVariableConfigParam
from .httpbearerconfig import HTTPBearerConfig, HTTPBearerConfigParam
from .oauth2config import OAuth2Config, OAuth2ConfigParam
from pydantic import Field
from typing import Union
from typing_extensions import Annotated, TypeAliasType
CredentialCreateParamsParam = TypeAliasType('CredentialCreateParamsParam', Union[EnvironmentVariableConfigParam, HTTPBearerConfigParam, OAuth2ConfigParam])
CredentialCreateParams = Annotated[Union[EnvironmentVariableConfig, HTTPBearerConfig, OAuth2Config], Field(discriminator='type')]
