
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_cache_control_ephemeral import BetaCacheControlEphemeral

class BetaCodeExecutionTool20260120(BaseModel):
    """A `tools` entry for the code execution tool, version `code_execution_20260120`.

    It adds REPL state persistence to version `code_execution_20250825`.

    REPL state persistence applies with programmatic tool calling. With it, the Python interpreter state, such as variable bindings, persists across requests that reuse the container.

    See the [code execution tool guide](https://platform.claude.com/docs/en/agents-and-tools/tool-use/code-execution-tool#tool-versions) to learn what each tool version adds.
    """
    name: Literal['code_execution']
    type: Literal['code_execution_20260120']
    allowed_callers: Optional[List[Literal['direct', 'code_execution_20250825', 'code_execution_20260120', 'code_execution_20260521']]] = None
    cache_control: Optional[BetaCacheControlEphemeral] = None
    defer_loading: Optional[bool] = None
    strict: Optional[bool] = None
