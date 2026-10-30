# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Dict, List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from pydantic import Field as FieldInfo
from ..._utils import PropertyInfo
from ..._models import BaseModel
from .beta_custom_tool import BetaCustomTool

class ToolFunction(BaseModel):
    name: str
    type: Literal['function']
    allowed_callers: Optional[List[Literal['direct', 'programmatic']]] = None
    async_: Optional[bool] = FieldInfo(alias='async', default=None)
    defer_loading: Optional[bool] = None
    description: Optional[str] = None
    output_schema: Optional[Dict[str, object]] = None
    parameters: Optional[object] = None
    strict: Optional[bool] = None
Tool: TypeAlias = Annotated[Union[ToolFunction, BetaCustomTool], PropertyInfo(discriminator='type')]

class BetaNamespaceTool(BaseModel):
    """Groups function/custom tools under a shared namespace."""
    description: str
    name: str
    tools: List[Tool]
    type: Literal['namespace']
