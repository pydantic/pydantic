# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from ..._models import BaseModel
from ..shared.metadata import Metadata

class ToolResourcesCodeInterpreter(BaseModel):
    file_ids: Optional[List[str]] = None

class ToolResourcesFileSearch(BaseModel):
    vector_store_ids: Optional[List[str]] = None

class ToolResources(BaseModel):
    """
    A set of resources that are made available to the assistant's tools in this thread. The resources are specific to the type of tool. For example, the `code_interpreter` tool requires a list of file IDs, while the `file_search` tool requires a list of vector store IDs.
    """
    code_interpreter: Optional[ToolResourcesCodeInterpreter] = None
    file_search: Optional[ToolResourcesFileSearch] = None

class Thread(BaseModel):
    """
    Represents a thread that contains [messages](https://developers.openai.com/api/docs/assistants/migration).
    """
    id: str
    created_at: int
    metadata: Optional[Metadata] = None
    object: Literal['thread']
    tool_resources: Optional[ToolResources] = None
