# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class ResponseComputerToolCallOutputScreenshot(BaseModel):
    """A computer screenshot image used with the computer use tool."""
    type: Literal['computer_screenshot']
    file_id: Optional[str] = None
    image_url: Optional[str] = None
