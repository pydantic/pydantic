# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from ..._models import BaseModel
from .dpo_hyperparameters import DpoHyperparameters

class DpoMethod(BaseModel):
    """Configuration for the DPO fine-tuning method."""
    hyperparameters: Optional[DpoHyperparameters] = None
