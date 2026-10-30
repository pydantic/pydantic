# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class DecisionCreateEvent(BaseModel):
    """
    Evaluate the configured questions using the current conversation and Decision inputs. Reusing an event_id is rejected for the lifetime of the session.
    """
    event_id: str
    type: Literal['decision.create']
