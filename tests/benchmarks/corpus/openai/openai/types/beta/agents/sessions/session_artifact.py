# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ....._models import BaseModel

class SessionArtifact(BaseModel):
    """An immutable file published by a completed hosted session turn."""
    id: str
    created_at: int
    environment_id: str
    object: Literal['agent.session.artifact']
    path: str
    session_id: str
    size_bytes: int
    turn_id: str
