# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ..._utils import PropertyInfo
from ..._models import BaseModel
from .response_input_file import ResponseInputFile
from .response_input_text import ResponseInputText
from .response_input_image import ResponseInputImage
OutputOutputContentList: TypeAlias = Annotated[Union[ResponseInputText, ResponseInputImage, ResponseInputFile], PropertyInfo(discriminator='type')]

class CallerDirect(BaseModel):
    type: Literal['direct']

class CallerProgram(BaseModel):
    caller_id: str
    type: Literal['program']
Caller: TypeAlias = Annotated[Union[CallerDirect, CallerProgram, None], PropertyInfo(discriminator='type')]

class ResponseFunctionToolCallOutputItem(BaseModel):
    id: str
    output: Union[str, List[OutputOutputContentList]]
    status: Literal['in_progress', 'completed', 'incomplete']
    type: Literal['function_call_output']
    call_id: Optional[str] = None
    caller: Optional[Caller] = None
    created_by: Optional[str] = None
    name: Optional[str] = None
    namespace: Optional[str] = None
