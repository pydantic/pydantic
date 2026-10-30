# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaComputerUsePreviewTool(BaseModel):
    """A tool that controls a virtual computer.

    Learn more about the [computer tool](https://developers.openai.com/api/docs/guides/tools-computer-use).
    """
    display_height: int
    display_width: int
    environment: Literal['windows', 'mac', 'linux', 'ubuntu', 'browser']
    type: Literal['computer_use_preview']
