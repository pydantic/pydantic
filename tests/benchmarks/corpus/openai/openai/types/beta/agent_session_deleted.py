# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class AgentSessionDeleted(BaseModel):
    """A Managed Agents session removed from the public API.

    Physical cleanup may continue asynchronously.
    """
    id: str
    deleted: bool
    object: Literal['agent.session.deleted']
