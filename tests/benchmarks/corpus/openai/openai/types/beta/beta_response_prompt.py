# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Dict, Union, Optional
from typing_extensions import TypeAlias
from ..._models import BaseModel
from .beta_response_input_file import BetaResponseInputFile
from .beta_response_input_text import BetaResponseInputText
from .beta_response_input_image import BetaResponseInputImage
Variables: TypeAlias = Union[str, BetaResponseInputText, BetaResponseInputImage, BetaResponseInputFile]

class BetaResponsePrompt(BaseModel):
    """
    Reference to a prompt template and its variables.
    [Learn more](https://developers.openai.com/api/docs/guides/text?api-mode=responses#version-prompts-in-code).
    """
    id: str
    variables: Optional[Dict[str, Variables]] = None
    version: Optional[str] = None
