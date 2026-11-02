# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ...._models import BaseModel

class FilePath(BaseModel):
    file_id: Optional[str] = None

class FilePathDeltaAnnotation(BaseModel):
    """
    A URL for the file that's generated when the assistant used the `code_interpreter` tool to generate a file.
    """
    index: int
    type: Literal['file_path']
    end_index: Optional[int] = None
    file_path: Optional[FilePath] = None
    start_index: Optional[int] = None
    text: Optional[str] = None
