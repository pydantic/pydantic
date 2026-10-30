# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Optional
from ..._models import BaseModel

class FineTuningJobWandbIntegration(BaseModel):
    """The settings for your integration with Weights and Biases.

    This payload specifies the project that
    metrics will be sent to. Optionally, you can set an explicit display name for your run, add tags
    to your run, and set a default entity (team, username, etc) to be associated with your run.
    """
    project: str
    entity: Optional[str] = None
    name: Optional[str] = None
    tags: Optional[List[str]] = None
