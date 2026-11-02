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
from ..interactions import antigravityagentconfig as interactions_antigravityagentconfig, environment as interactions_environment
from .agenttool import AgentTool, AgentToolParam
from pydantic import model_serializer
from typing import List, Optional, Union
from typing_extensions import NotRequired, TypeAliasType, TypedDict
AgentConfigParam = interactions_antigravityagentconfig.AntigravityAgentConfigParam
AgentConfig = interactions_antigravityagentconfig.AntigravityAgentConfig
BaseEnvironmentParam = TypeAliasType('BaseEnvironmentParam', Union[interactions_environment.EnvironmentParam, str])
BaseEnvironment = TypeAliasType('BaseEnvironment', Union[interactions_environment.Environment, str])

class AgentParam(TypedDict):
    """An agent definition for the CreateAgent API.
    This message is the target for annotation-parser-based JSON parsing.
    New format:
    {
    \\"id\\": \\"customer-sentinel\\",
    \\"base_agent\\": \\"\\",
    \\"system_instruction\\": \\"...\\",
    \\"base_environment\\": { \\"type\\": \\"remote\\", \\"sources\\": [...] },
    \\"tools\\": [ {\\"type\\": \\"code_execution\\"} ]
    }
    """
    agent_config: NotRequired[AgentConfigParam]
    base_agent: NotRequired[str]
    base_environment: NotRequired[BaseEnvironmentParam]
    description: NotRequired[str]
    id: NotRequired[str]
    system_instruction: NotRequired[str]
    tools: NotRequired[List[AgentToolParam]]

class Agent(BaseModel):
    """An agent definition for the CreateAgent API.
    This message is the target for annotation-parser-based JSON parsing.
    New format:
    {
    \\"id\\": \\"customer-sentinel\\",
    \\"base_agent\\": \\"\\",
    \\"system_instruction\\": \\"...\\",
    \\"base_environment\\": { \\"type\\": \\"remote\\", \\"sources\\": [...] },
    \\"tools\\": [ {\\"type\\": \\"code_execution\\"} ]
    }
    """
    agent_config: Optional[AgentConfig] = None
    base_agent: Optional[str] = None
    base_environment: Optional[BaseEnvironment] = None
    description: Optional[str] = None
    id: Optional[str] = None
    system_instruction: Optional[str] = None
    tools: Optional[List[AgentTool]] = None

    @model_serializer(mode='wrap')
    def serialize_model(self, handler):
        optional_fields = set(['agent_config', 'base_agent', 'base_environment', 'description', 'id', 'system_instruction', 'tools'])
        serialized = handler(self)
        m = {}
        for n, f in type(self).model_fields.items():
            k = f.alias or n
            val = serialized.get(k, serialized.get(n))
            if val != UNSET_SENTINEL:
                if val is not None or k not in optional_fields:
                    m[k] = val
        return m
