# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ..._utils import PropertyInfo
from ..._models import BaseModel

class ContentPartOutputText(BaseModel):
    text: str
    type: Literal['output_text']

class ContentPartRefusal(BaseModel):
    refusal: str
    type: Literal['refusal']
ContentPart: TypeAlias = Annotated[Union[ContentPartOutputText, ContentPartRefusal], PropertyInfo(discriminator='type')]

class DecisionStoredAssistantMessage(BaseModel):
    id: str
    content: Union[str, List[ContentPart]]
    role: Literal['assistant']
    phase: Optional[Literal['commentary', 'final_answer']] = None
    type: Optional[Literal['message']] = None
