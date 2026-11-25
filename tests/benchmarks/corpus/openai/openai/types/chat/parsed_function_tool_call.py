
# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from .chat_completion_message_function_tool_call import Function, ChatCompletionMessageFunctionToolCall

class ParsedFunction(Function):
    parsed_arguments: Optional[object] = None

class ParsedFunctionToolCall(ChatCompletionMessageFunctionToolCall):
    function: ParsedFunction
