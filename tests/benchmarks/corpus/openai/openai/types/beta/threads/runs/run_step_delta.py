# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Union, Optional
from typing_extensions import Annotated, TypeAlias
from ....._utils import PropertyInfo
from ....._models import BaseModel
from .tool_call_delta_object import ToolCallDeltaObject
from .run_step_delta_message_delta import RunStepDeltaMessageDelta
StepDetails: TypeAlias = Annotated[Union[RunStepDeltaMessageDelta, ToolCallDeltaObject], PropertyInfo(discriminator='type')]

class RunStepDelta(BaseModel):
    """The delta containing the fields that have changed on the run step."""
    step_details: Optional[StepDetails] = None
