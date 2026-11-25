# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
import builtins
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class FineTuningJobEvent(BaseModel):
    """Fine-tuning job event object"""
    id: str
    created_at: int
    level: Literal['info', 'warn', 'error']
    message: str
    object: Literal['fine_tuning.job.event']
    data: Optional[builtins.object] = None
    type: Optional[Literal['message', 'metrics']] = None
