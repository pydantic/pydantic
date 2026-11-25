# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ..._utils import PropertyInfo
from ..._models import BaseModel

class AnnotationFileCitation(BaseModel):
    """A citation to a file."""
    file_id: str
    filename: str
    index: int
    type: Literal['file_citation']

class AnnotationURLCitation(BaseModel):
    """A citation for a web resource used to generate a model response."""
    end_index: int
    start_index: int
    title: str
    type: Literal['url_citation']
    url: str

class AnnotationContainerFileCitation(BaseModel):
    """A citation for a container file used to generate a model response."""
    container_id: str
    end_index: int
    file_id: str
    filename: str
    start_index: int
    type: Literal['container_file_citation']

class AnnotationFilePath(BaseModel):
    """A path to a file."""
    file_id: str
    index: int
    type: Literal['file_path']
Annotation: TypeAlias = Annotated[Union[AnnotationFileCitation, AnnotationURLCitation, AnnotationContainerFileCitation, AnnotationFilePath], PropertyInfo(discriminator='type')]

class LogprobTopLogprob(BaseModel):
    """The top log probability of a token."""
    token: str
    bytes: List[int]
    logprob: float

class Logprob(BaseModel):
    """The log probability of a token."""
    token: str
    bytes: List[int]
    logprob: float
    top_logprobs: List[LogprobTopLogprob]

class BetaResponseOutputText(BaseModel):
    """A text output from the model."""
    annotations: List[Annotation]
    text: str
    type: Literal['output_text']
    logprobs: Optional[List[Logprob]] = None
