# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ....._utils import PropertyInfo
from ....._models import BaseModel
from .code_interpreter_logs import CodeInterpreterLogs
from .code_interpreter_output_image import CodeInterpreterOutputImage
CodeInterpreterOutput: TypeAlias = Annotated[Union[CodeInterpreterLogs, CodeInterpreterOutputImage], PropertyInfo(discriminator='type')]

class CodeInterpreter(BaseModel):
    """The Code Interpreter tool call definition."""
    input: Optional[str] = None
    outputs: Optional[List[CodeInterpreterOutput]] = None

class CodeInterpreterToolCallDelta(BaseModel):
    """Details of the Code Interpreter tool call the run step was involved in."""
    index: int
    type: Literal['code_interpreter']
    id: Optional[str] = None
    code_interpreter: Optional[CodeInterpreter] = None
