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
from .agentoption import AgentOption
from .antigravityagentconfig import AntigravityAgentConfig, AntigravityAgentConfigParam
from .codemenderagentconfig import CodeMenderAgentConfig, CodeMenderAgentConfigParam
from .deepresearchagentconfig import DeepResearchAgentConfig, DeepResearchAgentConfigParam
from .dynamicagentconfig import DynamicAgentConfig, DynamicAgentConfigParam
from .environment import Environment, EnvironmentParam
from .interactionsinput import InteractionsInput, InteractionsInputParam
from .responseformat import ResponseFormat, ResponseFormatParam
from .responsemodality import ResponseModality
from .safetysetting import SafetySetting, SafetySettingParam
from .servicetier import ServiceTier
from .tool import Tool, ToolParam
from .webhookconfig import WebhookConfig, WebhookConfigParam
import pydantic
from pydantic import Field, model_serializer
from typing import Dict, List, Optional, Union
from typing_extensions import Annotated, NotRequired, TypeAliasType, TypedDict
CreateAgentInteractionAgentConfigParam = TypeAliasType('CreateAgentInteractionAgentConfigParam', Union[DynamicAgentConfigParam, AntigravityAgentConfigParam, DeepResearchAgentConfigParam, CodeMenderAgentConfigParam])
CreateAgentInteractionAgentConfig = Annotated[Union[AntigravityAgentConfig, CodeMenderAgentConfig, DeepResearchAgentConfig, DynamicAgentConfig], Field(discriminator='type')]
CreateAgentInteractionEnvironmentParam = TypeAliasType('CreateAgentInteractionEnvironmentParam', Union[EnvironmentParam, str])
CreateAgentInteractionEnvironment = TypeAliasType('CreateAgentInteractionEnvironment', Union[Environment, str])
CreateAgentInteractionResponseFormatParam = TypeAliasType('CreateAgentInteractionResponseFormatParam', Union[ResponseFormatParam, List[ResponseFormatParam]])
CreateAgentInteractionResponseFormat = TypeAliasType('CreateAgentInteractionResponseFormat', Union[ResponseFormat, List[ResponseFormat]])

class CreateAgentInteractionParam(TypedDict):
    """Interaction for generating the completion using agents."""
    agent: AgentOption
    agent_config: NotRequired[CreateAgentInteractionAgentConfigParam]
    background: NotRequired[bool]
    continuation_token: NotRequired[str]
    environment: NotRequired[CreateAgentInteractionEnvironmentParam]
    input: NotRequired[InteractionsInputParam]
    labels: NotRequired[Dict[str, str]]
    previous_interaction_id: NotRequired[str]
    response_format: NotRequired[CreateAgentInteractionResponseFormatParam]
    response_mime_type: NotRequired[str]
    response_modalities: NotRequired[List[ResponseModality]]
    safety_settings: NotRequired[List[SafetySettingParam]]
    service_tier: NotRequired[ServiceTier]
    store: NotRequired[bool]
    stream: NotRequired[bool]
    system_instruction: NotRequired[str]
    tools: NotRequired[List[ToolParam]]
    webhook_config: NotRequired[WebhookConfigParam]

class CreateAgentInteraction(BaseModel):
    """Interaction for generating the completion using agents."""
    agent: AgentOption
    agent_config: Optional[CreateAgentInteractionAgentConfig] = None
    background: Optional[bool] = None
    continuation_token: Optional[str] = None
    environment: Optional[CreateAgentInteractionEnvironment] = None
    input: Optional[InteractionsInput] = None
    labels: Optional[Dict[str, str]] = None
    previous_interaction_id: Optional[str] = None
    response_format: Optional[CreateAgentInteractionResponseFormat] = None
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
    def serialize_model(self, handler):
        optional_fields = set(['agent_config', 'background', 'continuation_token', 'environment', 'input', 'labels', 'previous_interaction_id', 'response_format', 'response_mime_type', 'response_modalities', 'safety_settings', 'service_tier', 'store', 'stream', 'system_instruction', 'tools', 'webhook_config'])
        serialized = handler(self)
        m = {}
        for n, f in type(self).model_fields.items():
            k = f.alias or n
            val = serialized.get(k, serialized.get(n))
            if val != UNSET_SENTINEL:
                if val is not None or k not in optional_fields:
                    m[k] = val
        return m
