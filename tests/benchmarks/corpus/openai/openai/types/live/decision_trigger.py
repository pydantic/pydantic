# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List
from typing_extensions import Literal
from ..._models import BaseModel
from .decision_question import DecisionQuestion

class Decisions(BaseModel):
    """
    Questions evaluated using the current transcript and the session's shared Decision items.
    """
    questions: List[DecisionQuestion]

class DecisionTrigger(BaseModel):
    decisions: Decisions
    event_type: Literal['session.input_transcript.delta', 'session.output_transcript.delta']
    type: Literal['decisions']
