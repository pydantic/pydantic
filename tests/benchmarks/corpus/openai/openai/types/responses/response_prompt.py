# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Dict, Union, Optional
from typing_extensions import TypeAlias
from ..._models import BaseModel
from .response_input_file import ResponseInputFile
from .response_input_text import ResponseInputText
from .response_input_image import ResponseInputImage
Variables: TypeAlias = Union[str, ResponseInputText, ResponseInputImage, ResponseInputFile]

class ResponsePrompt(BaseModel):
    """
    Reference to a prompt template and its variables.
    [Learn more](https://developers.openai.com/api/docs/guides/text?api-mode=responses#version-prompts-in-code).
    """
    id: str
    variables: Optional[Dict[str, Variables]] = None
    version: Optional[str] = None
