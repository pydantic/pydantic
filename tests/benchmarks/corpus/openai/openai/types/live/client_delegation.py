# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class ClientDelegation(BaseModel):
    """Delegate tasks to your application.

    The Live session emits delegation events that your backend handles.
    """
    type: Literal['client']
    acknowledgement_delay_ms: Optional[int] = None
