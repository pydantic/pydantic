# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Union, Optional
from typing_extensions import Literal
from ..._models import BaseModel

class ReinforcementHyperparameters(BaseModel):
    """The hyperparameters used for the reinforcement fine-tuning job."""
    batch_size: Union[Literal['auto'], int, None] = None
    compute_multiplier: Union[Literal['auto'], float, None] = None
    eval_interval: Union[Literal['auto'], int, None] = None
    eval_samples: Union[Literal['auto'], int, None] = None
    learning_rate_multiplier: Union[Literal['auto'], float, None] = None
    n_epochs: Union[Literal['auto'], int, None] = None
    reasoning_effort: Optional[Literal['default', 'low', 'medium', 'high']] = None
