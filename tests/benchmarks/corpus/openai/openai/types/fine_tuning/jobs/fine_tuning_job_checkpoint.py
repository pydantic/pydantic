# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ...._models import BaseModel

class Metrics(BaseModel):
    """Metrics at the step number during the fine-tuning job."""
    full_valid_loss: Optional[float] = None
    full_valid_mean_token_accuracy: Optional[float] = None
    step: Optional[float] = None
    train_loss: Optional[float] = None
    train_mean_token_accuracy: Optional[float] = None
    valid_loss: Optional[float] = None
    valid_mean_token_accuracy: Optional[float] = None

class FineTuningJobCheckpoint(BaseModel):
    """
    The `fine_tuning.job.checkpoint` object represents a model checkpoint for a fine-tuning job that is ready to use.
    """
    id: str
    created_at: int
    fine_tuned_model_checkpoint: str
    fine_tuning_job_id: str
    metrics: Metrics
    object: Literal['fine_tuning.job.checkpoint']
    step_number: int
