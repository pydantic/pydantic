# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from .._models import BaseModel

class EvalDeleteResponse(BaseModel):
    deleted: bool
    eval_id: str
    object: str
