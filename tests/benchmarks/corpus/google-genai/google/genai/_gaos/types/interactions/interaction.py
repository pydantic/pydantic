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
from ...utils.unions import parse_open_union
from .agentoption import AgentOption
from .antigravityagentconfig import AntigravityAgentConfig
from .audiocontent import AudioContent
from .codemenderagentconfig import CodeMenderAgentConfig
from .deepresearchagentconfig import DeepResearchAgentConfig
from .dynamicagentconfig import DynamicAgentConfig
from .environment import Environment
from .error import Error
from .generationconfig import GenerationConfig
from .imagecontent import ImageContent
from .interactionsinput import InteractionsInput
from .model import Model
from .responseformat import ResponseFormat
from .responsemodality import ResponseModality
from .safetysetting import SafetySetting
from .servicetier import ServiceTier
from .step import Step
from .tool import Tool
from .usage import Usage
from .videocontent import VideoContent
from .webhookconfig import WebhookConfig
from functools import partial
import pydantic
from pydantic import ConfigDict, model_serializer
from pydantic.functional_validators import BeforeValidator
from typing import Any, Dict, List, Literal, Optional, Union
from typing_extensions import Annotated, TypeAliasType

class UnknownInteractionAgentConfig(BaseModel):
    """A InteractionAgentConfig variant the SDK doesn't recognize. Preserves the raw payload."""
    type: Literal['UNKNOWN'] = 'UNKNOWN'
    raw: Any
    is_unknown: Literal[True] = True
    model_config = ConfigDict(frozen=True)
_INTERACTION_AGENT_CONFIG_VARIANTS: dict[str, Any] = {'antigravity': AntigravityAgentConfig, 'code-mender': CodeMenderAgentConfig, 'deep-research': DeepResearchAgentConfig, 'dynamic': DynamicAgentConfig}
InteractionAgentConfig = Annotated[Union[AntigravityAgentConfig, CodeMenderAgentConfig, DeepResearchAgentConfig, DynamicAgentConfig, UnknownInteractionAgentConfig], BeforeValidator(partial(parse_open_union, disc_key='type', variants=_INTERACTION_AGENT_CONFIG_VARIANTS, unknown_cls=UnknownInteractionAgentConfig, union_name='InteractionAgentConfig', lenient=True))]
InteractionEnvironment = TypeAliasType('InteractionEnvironment', Union[Environment, str])
InteractionResponseFormat = TypeAliasType('InteractionResponseFormat', Union[ResponseFormat, List[ResponseFormat]])
InteractionStatus = Union[Literal['in_progress', 'requires_action', 'completed', 'failed', 'cancelled', 'incomplete', 'budget_exceeded', 'queued', 'requires_continuation'], UnrecognizedStr]

class Interaction(BaseModel):
    """The Interaction resource."""
    status: InteractionStatus
    agent: Optional[AgentOption] = None
    agent_config: Optional[InteractionAgentConfig] = None
    cached_content: Annotated[Optional[str], pydantic.Field(deprecated='warning: ** DEPRECATED ** - This will be removed in a future release, please migrate away from it as soon as possible.')] = None
    continuation_ids: Optional[List[str]] = None
    continuation_token: Optional[str] = None
    created: Optional[str] = None
    environment: Optional[InteractionEnvironment] = None
    environment_id: Optional[str] = None
    errors: Optional[List[Error]] = None
    generation_config: Optional[GenerationConfig] = None
    id: Optional[str] = ''
    input: Optional[InteractionsInput] = None
    labels: Optional[Dict[str, str]] = None
    model: Optional[Model] = None
    output_audio: Optional[AudioContent] = None
    output_image: Optional[ImageContent] = None
    output_text: Optional[str] = None
    output_video: Optional[VideoContent] = None
    previous_interaction_id: Optional[str] = None
    response_format: Optional[InteractionResponseFormat] = None
    response_mime_type: Annotated[Optional[str], pydantic.Field(deprecated='warning: ** DEPRECATED ** - This will be removed in a future release, please migrate away from it as soon as possible.')] = None
    response_modalities: Annotated[Optional[List[ResponseModality]], pydantic.Field(deprecated='warning: ** DEPRECATED ** - This will be removed in a future release, please migrate away from it as soon as possible.')] = None
    safety_settings: Optional[List[SafetySetting]] = None
    service_tier: Optional[ServiceTier] = None
    steps: Optional[List[Step]] = None
    system_instruction: Optional[str] = None
    tools: Optional[List[Tool]] = None
    updated: Optional[str] = None
    usage: Optional[Usage] = None
    webhook_config: Optional[WebhookConfig] = None

    @model_serializer(mode='wrap')
    def _serialize_model(self, handler):
        optional_fields = set(['agent', 'agent_config', 'cached_content', 'continuation_ids', 'continuation_token', 'created', 'environment', 'environment_id', 'errors', 'generation_config', 'id', 'input', 'labels', 'model', 'output_audio', 'output_image', 'output_text', 'output_video', 'previous_interaction_id', 'response_format', 'response_mime_type', 'response_modalities', 'safety_settings', 'service_tier', 'steps', 'system_instruction', 'tools', 'updated', 'usage', 'webhook_config'])
        serialized = handler(self)
        m = {}
        for n, f in type(self).model_fields.items():
            k = f.alias or n
            val = serialized.get(k, serialized.get(n))
            if val != UNSET_SENTINEL:
                if val is not None or k not in optional_fields:
                    m[k] = val
        return m

    @classmethod
    def _maybe_coerce_outputs(cls, data: Any) -> Any:
        legacy_lyria_models = ('lyria-3-pro-preview', 'lyria-3-clip-preview')
        if not isinstance(data, dict):
            return data
        if not isinstance(data.get('model'), str) or data['model'] not in legacy_lyria_models:
            return data
        if 'steps' in data:
            return data
        if 'outputs' not in data:
            return {**data, 'steps': []}
        outputs = data['outputs']
        if not isinstance(outputs, list):
            return {**data, 'steps': []}
        coerced = {**data}
        coerced.pop('outputs')
        coerced['steps'] = [{'type': 'model_output', 'content': outputs}]
        return coerced

    @pydantic.model_validator(mode='before')
    @classmethod
    def _coerce_outputs_to_steps(cls, data: Any) -> Any:
        return cls._maybe_coerce_outputs(data)

    @pydantic.model_validator(mode='after')
    def _populate_output_helpers(self):
        steps = self.steps if isinstance(self.steps, list) else []
        text_parts: List[str] = []
        collecting = False
        for step in reversed(steps):
            step_type = getattr(step, 'type', None)
            if step_type == 'user_input':
                break
            if step_type == 'thought':
                continue
            if step_type != 'model_output':
                if collecting:
                    break
                continue
            content = getattr(step, 'content', None)
            if not isinstance(content, list):
                continue
            should_stop = False
            for item in reversed(content):
                if getattr(item, 'type', None) == 'text':
                    collecting = True
                    text = getattr(item, 'text', None)
                    text_parts.append(text if isinstance(text, str) else '')
                elif collecting:
                    should_stop = True
                    break
            if should_stop:
                break
        self.output_text = ''.join(reversed(text_parts))
        output_image = None
        output_audio = None
        output_video = None
        for step in reversed(steps):
            step_type = getattr(step, 'type', None)
            if step_type == 'user_input':
                break
            if step_type != 'model_output':
                continue
            content = getattr(step, 'content', None)
            if not isinstance(content, list):
                continue
            for item in reversed(content):
                content_type = getattr(item, 'type', None)
                if content_type == 'image' and output_image is None:
                    output_image = item
                if content_type == 'audio' and output_audio is None:
                    output_audio = item
                if content_type == 'video' and output_video is None:
                    output_video = item
        if output_image is not None and self.output_image is None:
            self.output_image = output_image
        if output_audio is not None and self.output_audio is None:
            self.output_audio = output_audio
        if output_video is not None and self.output_video is None:
            self.output_video = output_video
        return self
