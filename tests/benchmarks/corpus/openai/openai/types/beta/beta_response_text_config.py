# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_response_format_text_config import BetaResponseFormatTextConfig

class BetaResponseTextConfig(BaseModel):
    """Configuration options for a text response from the model.

    Can be plain
    text or structured JSON data. Learn more:
    - [Text inputs and outputs](https://developers.openai.com/api/docs/guides/text)
    - [Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs)
    """
    format: Optional[BetaResponseFormatTextConfig] = None
    verbosity: Optional[Literal['low', 'medium', 'high']] = None
