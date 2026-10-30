
# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Generic, TypeVar, Optional
from ..._models import GenericModel
from .chat_completion import Choice, ChatCompletion
from .chat_completion_message import ChatCompletionMessage
from .parsed_function_tool_call import ParsedFunctionToolCall
ContentType = TypeVar('ContentType')

class ParsedChatCompletionMessage(ChatCompletionMessage, GenericModel, Generic[ContentType]):
    parsed: Optional[ContentType] = None
    tool_calls: Optional[List[ParsedFunctionToolCall]] = None

class ParsedChoice(Choice, GenericModel, Generic[ContentType]):
    message: ParsedChatCompletionMessage[ContentType]

class ParsedChatCompletion(ChatCompletion, GenericModel, Generic[ContentType]):
    choices: List[ParsedChoice[ContentType]]
