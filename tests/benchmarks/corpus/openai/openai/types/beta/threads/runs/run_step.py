# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ....._utils import PropertyInfo
from ....._models import BaseModel
from ....shared.metadata import Metadata
from .tool_calls_step_details import ToolCallsStepDetails
from .message_creation_step_details import MessageCreationStepDetails

class LastError(BaseModel):
    """The last error associated with this run step.

    Will be `null` if there are no errors.
    """
    code: Literal['server_error', 'rate_limit_exceeded']
    message: str
StepDetails: TypeAlias = Annotated[Union[MessageCreationStepDetails, ToolCallsStepDetails], PropertyInfo(discriminator='type')]

class Usage(BaseModel):
    """Usage statistics related to the run step.

    This value will be `null` while the run step's status is `in_progress`.
    """
    completion_tokens: int
    prompt_tokens: int
    total_tokens: int

class RunStep(BaseModel):
    """Represents a step in execution of a run."""
    id: str
    assistant_id: str
    cancelled_at: Optional[int] = None
    completed_at: Optional[int] = None
    created_at: int
    expired_at: Optional[int] = None
    failed_at: Optional[int] = None
    last_error: Optional[LastError] = None
    metadata: Optional[Metadata] = None
    object: Literal['thread.run.step']
    run_id: str
    status: Literal['in_progress', 'cancelled', 'failed', 'completed', 'expired']
    step_details: StepDetails
    thread_id: str
    type: Literal['message_creation', 'tool_calls']
    usage: Optional[Usage] = None
