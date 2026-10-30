# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Annotated, TypeAlias
from ..._utils import PropertyInfo
from .chat_completion_message_custom_tool_call import ChatCompletionMessageCustomToolCall
from .chat_completion_message_function_tool_call import ChatCompletionMessageFunctionToolCall
ChatCompletionMessageToolCallUnion: TypeAlias = Annotated[Union[ChatCompletionMessageFunctionToolCall, ChatCompletionMessageCustomToolCall], PropertyInfo(discriminator='type')]
