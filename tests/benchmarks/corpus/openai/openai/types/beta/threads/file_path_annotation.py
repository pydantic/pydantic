# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class FilePath(BaseModel):
    file_id: str

class FilePathAnnotation(BaseModel):
    """
    A URL for the file that's generated when the assistant used the `code_interpreter` tool to generate a file.
    """
    end_index: int
    file_path: FilePath
    start_index: int
    text: str
    type: Literal['file_path']
