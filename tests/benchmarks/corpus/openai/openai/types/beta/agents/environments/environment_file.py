# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ....._models import BaseModel

class EnvironmentFile(BaseModel):
    """A live file in an execution environment."""
    environment_id: str
    object: Literal['agent.environment.file']
    path: str
    size_bytes: int
