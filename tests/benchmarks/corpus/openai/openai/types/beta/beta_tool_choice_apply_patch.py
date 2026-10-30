# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaToolChoiceApplyPatch(BaseModel):
    """Forces the model to call the apply_patch tool when executing a tool call."""
    type: Literal['apply_patch']
