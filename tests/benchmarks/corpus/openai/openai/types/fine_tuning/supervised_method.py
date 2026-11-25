# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from ..._models import BaseModel
from .supervised_hyperparameters import SupervisedHyperparameters

class SupervisedMethod(BaseModel):
    """Configuration for the supervised fine-tuning method."""
    hyperparameters: Optional[SupervisedHyperparameters] = None
