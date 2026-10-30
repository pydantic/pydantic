# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Union, Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .dpo_method import DpoMethod
from ..shared.metadata import Metadata
from .supervised_method import SupervisedMethod
from .reinforcement_method import ReinforcementMethod
from .fine_tuning_job_wandb_integration_object import FineTuningJobWandbIntegrationObject

class Error(BaseModel):
    """
    For fine-tuning jobs that have `failed`, this will contain more information on the cause of the failure.
    """
    code: str
    message: str
    param: Optional[str] = None

class Hyperparameters(BaseModel):
    """The hyperparameters used for the fine-tuning job.

    This value will only be returned when running `supervised` jobs.
    """
    batch_size: Union[Literal['auto'], int, None] = None
    learning_rate_multiplier: Union[Literal['auto'], float, None] = None
    n_epochs: Union[Literal['auto'], int, None] = None

class Method(BaseModel):
    """The method used for fine-tuning."""
    type: Literal['supervised', 'dpo', 'reinforcement']
    dpo: Optional[DpoMethod] = None
    reinforcement: Optional[ReinforcementMethod] = None
    supervised: Optional[SupervisedMethod] = None

class FineTuningJob(BaseModel):
    """
    The `fine_tuning.job` object represents a fine-tuning job that has been created through the API.
    """
    id: str
    created_at: int
    error: Optional[Error] = None
    fine_tuned_model: Optional[str] = None
    finished_at: Optional[int] = None
    hyperparameters: Hyperparameters
    model: str
    object: Literal['fine_tuning.job']
    organization_id: str
    result_files: List[str]
    seed: int
    status: Literal['validating_files', 'queued', 'running', 'succeeded', 'failed', 'cancelled']
    trained_tokens: Optional[int] = None
    training_file: str
    validation_file: Optional[str] = None
    estimated_finish: Optional[int] = None
    integrations: Optional[List[FineTuningJobWandbIntegrationObject]] = None
    metadata: Optional[Metadata] = None
    method: Optional[Method] = None
