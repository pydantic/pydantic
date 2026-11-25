# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Union
from typing_extensions import Literal, Annotated, TypeAlias
from ...._utils import PropertyInfo
from ...._models import BaseModel

class AnnotationFileSource(BaseModel):
    """File attachment referenced by the annotation."""
    filename: str
    type: Literal['file']

class AnnotationFile(BaseModel):
    """Annotation that references an uploaded file."""
    source: AnnotationFileSource
    type: Literal['file']

class AnnotationURLSource(BaseModel):
    """URL referenced by the annotation."""
    type: Literal['url']
    url: str

class AnnotationURL(BaseModel):
    """Annotation that references a URL."""
    source: AnnotationURLSource
    type: Literal['url']
Annotation: TypeAlias = Annotated[Union[AnnotationFile, AnnotationURL], PropertyInfo(discriminator='type')]

class ChatKitResponseOutputText(BaseModel):
    """Assistant response text accompanied by optional annotations."""
    annotations: List[Annotation]
    text: str
    type: Literal['output_text']
