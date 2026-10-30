# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from .response_function_tool_call import ResponseFunctionToolCall

class ResponseFunctionToolCallItem(ResponseFunctionToolCall):
    """A tool call to run a function.

    See the
    [function calling guide](https://developers.openai.com/api/docs/guides/function-calling) for more information.
    """
    id: str
    status: Literal['in_progress', 'completed', 'incomplete']
    created_by: Optional[str] = None
