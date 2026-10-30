
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal, TypeAlias
TextEditorCodeExecutionToolResultErrorCode: TypeAlias = Literal['invalid_tool_input', 'unavailable', 'too_many_requests', 'execution_time_exceeded', 'file_not_found']
