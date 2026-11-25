# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ...._models import BaseModel

class FileCitation(BaseModel):
    file_id: Optional[str] = None
    quote: Optional[str] = None

class FileCitationDeltaAnnotation(BaseModel):
    """
    A citation within the message that points to a specific quote from a specific File associated with the assistant or the message. Generated when the assistant uses the "file_search" tool to search files.
    """
    index: int
    type: Literal['file_citation']
    end_index: Optional[int] = None
    file_citation: Optional[FileCitation] = None
    start_index: Optional[int] = None
    text: Optional[str] = None
