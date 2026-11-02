# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ....._models import BaseModel
from .run_step_delta import RunStepDelta

class RunStepDeltaEvent(BaseModel):
    """Represents a run step delta i.e.

    any changed fields on a run step during streaming.
    """
    id: str
    delta: RunStepDelta
    object: Literal['thread.run.step.delta']
