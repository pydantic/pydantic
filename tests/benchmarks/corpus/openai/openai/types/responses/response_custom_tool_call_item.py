# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from .response_custom_tool_call import ResponseCustomToolCall

class ResponseCustomToolCallItem(ResponseCustomToolCall):
    """A call to a custom tool created by the model."""
    id: str
    status: Literal['in_progress', 'completed', 'incomplete']
    created_by: Optional[str] = None
