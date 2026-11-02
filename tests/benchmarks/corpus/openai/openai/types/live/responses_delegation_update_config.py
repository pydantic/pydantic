# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ..._utils import PropertyInfo
from ..._models import BaseModel
from .function_tool import FunctionTool

class Reasoning(BaseModel):
    """Reasoning settings passed to each delegated Responses request."""
    effort: Optional[Literal['none', 'minimal', 'low', 'medium', 'high', 'xhigh']] = None
    summary: Optional[Literal['concise', 'detailed', 'auto']] = None

class Text(BaseModel):
    """Text generation settings passed to each delegated Responses request."""
    verbosity: Optional[Literal['low', 'medium', 'high']] = None

class ToolChoiceLiveFunctionToolChoiceParam(BaseModel):
    name: str
    type: Literal['function']

class ToolChoiceLiveMCPToolChoiceParam(BaseModel):
    name: str
    server_label: str
    type: Literal['mcp']
ToolChoice: TypeAlias = Union[Literal['auto', 'none', 'required'], ToolChoiceLiveFunctionToolChoiceParam, ToolChoiceLiveMCPToolChoiceParam]

class ToolWebSearch(BaseModel):
    """A web search tool available to the Live session’s Responses backend."""
    type: Literal['web_search']
Tool: TypeAlias = Annotated[Union[FunctionTool, ToolWebSearch], PropertyInfo(discriminator='type')]

class ResponsesDelegationUpdateConfig(BaseModel):
    """Updates to the Responses backend of an existing Live session.

    Omitted settings retain their current values.
    """
    instructions: Optional[str] = None
    max_output_tokens: Optional[int] = None
    model: Optional[str] = None
    parallel_tool_calls: Optional[bool] = None
    reasoning: Optional[Reasoning] = None
    service_tier: Optional[Literal['auto', 'default', 'fast_tier_temp_pilot', 'flex', 'priority', 'ultrafast']] = None
    text: Optional[Text] = None
    tool_choice: Optional[ToolChoice] = None
    tools: Optional[List[Tool]] = None
