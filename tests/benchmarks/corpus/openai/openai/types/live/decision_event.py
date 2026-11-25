# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Union, Optional
from typing_extensions import Literal
from ..._models import BaseModel
from ..decision import Decision

class Event(BaseModel):
    decision: Decision
    type: Literal['decision.completed']

class DecisionEvent(BaseModel):
    """A Decision API event for a Live delegation or transcript trigger.

    For a trigger, source_event_id identifies the transcript delta that caused this evaluation.
    """
    delegation_id: Optional[str] = None
    event: Event
    event_id: str
    source_event_id: Optional[str] = None
    source_event_type: Union[Literal['session.input_transcript.delta', 'session.output_transcript.delta'], None] = None
    trigger_id: Optional[str] = None
    type: Literal['decision.event']
