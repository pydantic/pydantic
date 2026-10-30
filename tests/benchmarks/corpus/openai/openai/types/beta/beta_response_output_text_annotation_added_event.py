# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Union, Optional
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
Annotation: TypeAlias = Annotated[Union[AnnotationFileCitation, AnnotationURLCitation, AnnotationContainerFileCitation, AnnotationFilePath, None], PropertyInfo(discriminator='type')]

class Agent(BaseModel):
    """The agent that owns this multi-agent streaming event."""
    agent_name: str

class BetaResponseOutputTextAnnotationAddedEvent(BaseModel):
    """Emitted when an annotation is added to output text content."""
    annotation: Optional[Annotation] = None
    annotation_index: int
    content_index: int
    item_id: str
    output_index: int
    sequence_number: int
    type: Literal['response.output_text.annotation.added']
    agent: Optional[Agent] = None
