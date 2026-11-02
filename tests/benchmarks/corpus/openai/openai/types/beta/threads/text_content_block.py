# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from .text import Text
from ...._models import BaseModel

class TextContentBlock(BaseModel):
    """The text content that is part of a message."""
    text: Text
    type: Literal['text']
