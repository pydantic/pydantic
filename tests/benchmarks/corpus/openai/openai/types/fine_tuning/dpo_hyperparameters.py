# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Literal
from ..._models import BaseModel

class DpoHyperparameters(BaseModel):
    """The hyperparameters used for the DPO fine-tuning job."""
    batch_size: Union[Literal['auto'], int, None] = None
    beta: Union[Literal['auto'], float, None] = None
    learning_rate_multiplier: Union[Literal['auto'], float, None] = None
    n_epochs: Union[Literal['auto'], int, None] = None
