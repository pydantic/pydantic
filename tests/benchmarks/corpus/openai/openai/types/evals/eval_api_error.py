# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from ..._models import BaseModel

class EvalAPIError(BaseModel):
    """An object representing an error response from the Eval API."""
    code: str
    message: str
