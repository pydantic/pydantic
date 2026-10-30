
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_managed_agents_custom_tool_input_schema import BetaManagedAgentsCustomToolInputSchema

class BetaManagedAgentsCustomTool(BaseModel):
    """A custom tool as returned in API responses."""
    description: str
    input_schema: BetaManagedAgentsCustomToolInputSchema
    name: str
    type: Literal['custom']
