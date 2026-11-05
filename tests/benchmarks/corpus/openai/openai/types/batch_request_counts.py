# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from .._models import BaseModel

class BatchRequestCounts(BaseModel):
    """The request counts for different statuses within the batch."""
    completed: int
    failed: int
    total: int
