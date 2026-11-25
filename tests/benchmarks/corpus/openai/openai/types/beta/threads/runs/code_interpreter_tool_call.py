# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Union
from typing_extensions import Literal, Annotated, TypeAlias
from ....._utils import PropertyInfo
from ....._models import BaseModel

class CodeInterpreterOutputLogs(BaseModel):
    """Text output from the Code Interpreter tool call as part of a run step."""
    logs: str
    type: Literal['logs']

class CodeInterpreterOutputImageImage(BaseModel):
    file_id: str

class CodeInterpreterOutputImage(BaseModel):
    image: CodeInterpreterOutputImageImage
    type: Literal['image']
CodeInterpreterOutput: TypeAlias = Annotated[Union[CodeInterpreterOutputLogs, CodeInterpreterOutputImage], PropertyInfo(discriminator='type')]

class CodeInterpreter(BaseModel):
    """The Code Interpreter tool call definition."""
    input: str
    outputs: List[CodeInterpreterOutput]

class CodeInterpreterToolCall(BaseModel):
    """Details of the Code Interpreter tool call the run step was involved in."""
    id: str
    code_interpreter: CodeInterpreter
    type: Literal['code_interpreter']
