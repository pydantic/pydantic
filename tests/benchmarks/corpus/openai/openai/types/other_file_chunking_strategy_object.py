# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from .._models import BaseModel

class OtherFileChunkingStrategyObject(BaseModel):
    """This is returned when the chunking strategy is unknown.

    Typically, this is because the file was indexed before the `chunking_strategy` concept was introduced in the API.
    """
    type: Literal['other']
