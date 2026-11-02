
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List
from typing_extensions import Literal
from .._models import BaseModel
from .code_execution_output_block import CodeExecutionOutputBlock

class EncryptedCodeExecutionResultBlock(BaseModel):
    """
    The output and exit code of Python code that Claude ran with the code execution tool, with standard output in encrypted form.

    The API returns this block in place of `code_execution_result` when the code called the web search tool.

    See the [programmatic tool calling guide](https://platform.claude.com/docs/en/agents-and-tools/tool-use/programmatic-tool-calling) to learn more about programmatic tool calling.
    """
    content: List[CodeExecutionOutputBlock]
    encrypted_stdout: str
    return_code: int
    stderr: str
    type: Literal['encrypted_code_execution_result']
