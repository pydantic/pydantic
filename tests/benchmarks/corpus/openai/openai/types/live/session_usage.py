# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from ..._models import BaseModel

class SessionUsage(BaseModel):
    """Cumulative audio duration for a Live session.

    Values are totals for the session, not increments to sum across usage events.
    """
    seconds: float
