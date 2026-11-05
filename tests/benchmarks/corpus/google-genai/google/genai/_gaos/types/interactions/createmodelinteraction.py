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
from .. import BaseModel, UNSET_SENTINEL
from .environment import Environment, EnvironmentParam
from .generationconfig import GenerationConfig, GenerationConfigParam
from .interactionsinput import InteractionsInput, InteractionsInputParam
from .model import Model
from .responseformat import ResponseFormat, ResponseFormatParam
from .responsemodality import ResponseModality
from .safetysetting import SafetySetting, SafetySettingParam
from .servicetier import ServiceTier
from .tool import Tool, ToolParam
from .webhookconfig import WebhookConfig, WebhookConfigParam
import pydantic
from pydantic import model_serializer
from typing import Dict, List, Optional, Union
from typing_extensions import Annotated, NotRequired, TypeAliasType, TypedDict
CreateModelInteractionEnvironmentParam = TypeAliasType('CreateModelInteractionEnvironmentParam', Union[EnvironmentParam, str])
CreateModelInteractionEnvironment = TypeAliasType('CreateModelInteractionEnvironment', Union[Environment, str])
CreateModelInteractionResponseFormatParam = TypeAliasType('CreateModelInteractionResponseFormatParam', Union[ResponseFormatParam, List[ResponseFormatParam]])
CreateModelInteractionResponseFormat = TypeAliasType('CreateModelInteractionResponseFormat', Union[ResponseFormat, List[ResponseFormat]])

class CreateModelInteractionParam(TypedDict):
    """Interaction for generating the completion using models."""
    model: Model
    background: NotRequired[bool]
    cached_content: NotRequired[str]
    continuation_token: NotRequired[str]
    environment: NotRequired[CreateModelInteractionEnvironmentParam]
    generation_config: NotRequired[GenerationConfigParam]
    input: NotRequired[InteractionsInputParam]
    labels: NotRequired[Dict[str, str]]
    previous_interaction_id: NotRequired[str]
    response_format: NotRequired[CreateModelInteractionResponseFormatParam]
    response_mime_type: NotRequired[str]
    response_modalities: NotRequired[List[ResponseModality]]
    safety_settings: NotRequired[List[SafetySettingParam]]
    service_tier: NotRequired[ServiceTier]
    store: NotRequired[bool]
    stream: NotRequired[bool]
    system_instruction: NotRequired[str]
    tools: NotRequired[List[ToolParam]]
    webhook_config: NotRequired[WebhookConfigParam]

class CreateModelInteraction(BaseModel):
    """Interaction for generating the completion using models."""
    model: Model
    background: Optional[bool] = None
    cached_content: Annotated[Optional[str], pydantic.Field(deprecated='warning: ** DEPRECATED ** - This will be removed in a future release, please migrate away from it as soon as possible.')] = None
    continuation_token: Optional[str] = None
    environment: Optional[CreateModelInteractionEnvironment] = None
    generation_config: Optional[GenerationConfig] = None
    input: Optional[InteractionsInput] = None
    labels: Optional[Dict[str, str]] = None
    previous_interaction_id: Optional[str] = None
    response_format: Optional[CreateModelInteractionResponseFormat] = None
    response_mime_type: Annotated[Optional[str], pydantic.Field(deprecated='warning: ** DEPRECATED ** - This will be removed in a future release, please migrate away from it as soon as possible.')] = None
    response_modalities: Annotated[Optional[List[ResponseModality]], pydantic.Field(deprecated='warning: ** DEPRECATED ** - This will be removed in a future release, please migrate away from it as soon as possible.')] = None
    safety_settings: Optional[List[SafetySetting]] = None
    service_tier: Optional[ServiceTier] = None
    store: Optional[bool] = None
    stream: Optional[bool] = None
    system_instruction: Optional[str] = None
    tools: Optional[List[Tool]] = None
    webhook_config: Optional[WebhookConfig] = None

    @model_serializer(mode='wrap')
    def _serialize_model(self, handler):
        optional_fields = set(['background', 'cached_content', 'continuation_token', 'environment', 'generation_config', 'input', 'labels', 'previous_interaction_id', 'response_format', 'response_mime_type', 'response_modalities', 'safety_settings', 'service_tier', 'store', 'stream', 'system_instruction', 'tools', 'webhook_config'])
        serialized = handler(self)
        m = {}
        for n, f in type(self).model_fields.items():
            k = f.alias or n
            val = serialized.get(k, serialized.get(n))
            if val != UNSET_SENTINEL:
                if val is not None or k not in optional_fields:
                    m[k] = val
        return m
