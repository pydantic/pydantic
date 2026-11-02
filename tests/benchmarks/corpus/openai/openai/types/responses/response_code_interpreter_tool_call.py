# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ..._utils import PropertyInfo
from ..._models import BaseModel

class OutputLogs(BaseModel):
    """The logs output from the code interpreter."""
    logs: str
    type: Literal['logs']

class OutputImage(BaseModel):
    """The image output from the code interpreter."""
    type: Literal['image']
    url: str
Output: TypeAlias = Annotated[Union[OutputLogs, OutputImage], PropertyInfo(discriminator='type')]

class ResponseCodeInterpreterToolCall(BaseModel):
    """A tool call to run code."""
    id: str
    code: Optional[str] = None
    container_id: str
    outputs: Optional[List[Output]] = None
    status: Literal['in_progress', 'completed', 'incomplete', 'interpreting', 'failed']
    type: Literal['code_interpreter_call']
