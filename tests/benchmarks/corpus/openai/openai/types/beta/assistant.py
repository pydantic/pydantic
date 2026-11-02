# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .assistant_tool import AssistantTool
from ..shared.metadata import Metadata
from .assistant_response_format_option import AssistantResponseFormatOption

class ToolResourcesCodeInterpreter(BaseModel):
    file_ids: Optional[List[str]] = None

class ToolResourcesFileSearch(BaseModel):
    vector_store_ids: Optional[List[str]] = None

class ToolResources(BaseModel):
    """A set of resources that are used by the assistant's tools.

    The resources are specific to the type of tool. For example, the `code_interpreter` tool requires a list of file IDs, while the `file_search` tool requires a list of vector store IDs.
    """
    code_interpreter: Optional[ToolResourcesCodeInterpreter] = None
    file_search: Optional[ToolResourcesFileSearch] = None

class Assistant(BaseModel):
    """Represents an `assistant` that can call the model and use tools."""
    id: str
    created_at: int
    description: Optional[str] = None
    instructions: Optional[str] = None
    metadata: Optional[Metadata] = None
    model: str
    name: Optional[str] = None
    object: Literal['assistant']
    tools: List[AssistantTool]
    response_format: Optional[AssistantResponseFormatOption] = None
    temperature: Optional[float] = None
    tool_resources: Optional[ToolResources] = None
    top_p: Optional[float] = None
