# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class FileCitation(BaseModel):
    file_id: str

class FileCitationAnnotation(BaseModel):
    """
    A citation within the message that points to a specific quote from a specific File associated with the assistant or the message. Generated when the assistant uses the "file_search" tool to search files.
    """
    end_index: int
    file_citation: FileCitation
    start_index: int
    text: str
    type: Literal['file_citation']
