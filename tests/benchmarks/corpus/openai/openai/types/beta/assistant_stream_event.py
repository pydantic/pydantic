# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from .thread import Thread
from ..._models import BaseModel
from .threads.run import Run
from .threads.message import Message
from ..shared.error_object import ErrorObject
from .threads.runs.run_step import RunStep
from .threads.message_delta_event import MessageDeltaEvent
from .threads.runs.run_step_delta_event import RunStepDeltaEvent

class ThreadCreated(BaseModel):
    """
    Occurs when a new [thread](https://developers.openai.com/api/docs/assistants/migration) is created.
    """
    data: Thread
    event: Literal['thread.created']
    enabled: Optional[bool] = None

class ThreadRunCreated(BaseModel):
    """
    Occurs when a new [run](https://developers.openai.com/api/docs/assistants/migration) is created.
    """
    data: Run
    event: Literal['thread.run.created']

class ThreadRunQueued(BaseModel):
    """
    Occurs when a [run](https://developers.openai.com/api/docs/assistants/migration) moves to a `queued` status.
    """
    data: Run
    event: Literal['thread.run.queued']

class ThreadRunInProgress(BaseModel):
    """
    Occurs when a [run](https://developers.openai.com/api/docs/assistants/migration) moves to an `in_progress` status.
    """
    data: Run
    event: Literal['thread.run.in_progress']

class ThreadRunRequiresAction(BaseModel):
    """
    Occurs when a [run](https://developers.openai.com/api/docs/assistants/migration) moves to a `requires_action` status.
    """
    data: Run
    event: Literal['thread.run.requires_action']

class ThreadRunCompleted(BaseModel):
    """
    Occurs when a [run](https://developers.openai.com/api/docs/assistants/migration) is completed.
    """
    data: Run
    event: Literal['thread.run.completed']

class ThreadRunIncomplete(BaseModel):
    """
    Occurs when a [run](https://developers.openai.com/api/docs/assistants/migration) ends with status `incomplete`.
    """
    data: Run
    event: Literal['thread.run.incomplete']

class ThreadRunFailed(BaseModel):
    """
    Occurs when a [run](https://developers.openai.com/api/docs/assistants/migration) fails.
    """
    data: Run
    event: Literal['thread.run.failed']

class ThreadRunCancelling(BaseModel):
    """
    Occurs when a [run](https://developers.openai.com/api/docs/assistants/migration) moves to a `cancelling` status.
    """
    data: Run
    event: Literal['thread.run.cancelling']

class ThreadRunCancelled(BaseModel):
    """
    Occurs when a [run](https://developers.openai.com/api/docs/assistants/migration) is cancelled.
    """
    data: Run
    event: Literal['thread.run.cancelled']

class ThreadRunExpired(BaseModel):
    """
    Occurs when a [run](https://developers.openai.com/api/docs/assistants/migration) expires.
    """
    data: Run
    event: Literal['thread.run.expired']

class ThreadRunStepCreated(BaseModel):
    """
    Occurs when a [run step](https://developers.openai.com/api/docs/assistants/migration) is created.
    """
    data: RunStep
    event: Literal['thread.run.step.created']

class ThreadRunStepInProgress(BaseModel):
    """
    Occurs when a [run step](https://developers.openai.com/api/docs/assistants/migration) moves to an `in_progress` state.
    """
    data: RunStep
    event: Literal['thread.run.step.in_progress']

class ThreadRunStepDelta(BaseModel):
    """
    Occurs when parts of a [run step](https://developers.openai.com/api/docs/assistants/migration) are being streamed.
    """
    data: RunStepDeltaEvent
    event: Literal['thread.run.step.delta']

class ThreadRunStepCompleted(BaseModel):
    """
    Occurs when a [run step](https://developers.openai.com/api/docs/assistants/migration) is completed.
    """
    data: RunStep
    event: Literal['thread.run.step.completed']

class ThreadRunStepFailed(BaseModel):
    """
    Occurs when a [run step](https://developers.openai.com/api/docs/assistants/migration) fails.
    """
    data: RunStep
    event: Literal['thread.run.step.failed']

class ThreadRunStepCancelled(BaseModel):
    """
    Occurs when a [run step](https://developers.openai.com/api/docs/assistants/migration) is cancelled.
    """
    data: RunStep
    event: Literal['thread.run.step.cancelled']

class ThreadRunStepExpired(BaseModel):
    """
    Occurs when a [run step](https://developers.openai.com/api/docs/assistants/migration) expires.
    """
    data: RunStep
    event: Literal['thread.run.step.expired']

class ThreadMessageCreated(BaseModel):
    """
    Occurs when a [message](https://developers.openai.com/api/docs/assistants/migration) is created.
    """
    data: Message
    event: Literal['thread.message.created']

class ThreadMessageInProgress(BaseModel):
    """
    Occurs when a [message](https://developers.openai.com/api/docs/assistants/migration) moves to an `in_progress` state.
    """
    data: Message
    event: Literal['thread.message.in_progress']

class ThreadMessageDelta(BaseModel):
    """
    Occurs when parts of a [Message](https://developers.openai.com/api/docs/assistants/migration) are being streamed.
    """
    data: MessageDeltaEvent
    event: Literal['thread.message.delta']

class ThreadMessageCompleted(BaseModel):
    """
    Occurs when a [message](https://developers.openai.com/api/docs/assistants/migration) is completed.
    """
    data: Message
    event: Literal['thread.message.completed']

class ThreadMessageIncomplete(BaseModel):
    """
    Occurs when a [message](https://developers.openai.com/api/docs/assistants/migration) ends before it is completed.
    """
    data: Message
    event: Literal['thread.message.incomplete']

class ErrorEvent(BaseModel):
    """
    Occurs when an [error](https://developers.openai.com/api/docs/guides/error-codes#api-errors) occurs. This can happen due to an internal server error or a timeout.
    """
    data: ErrorObject
    event: Literal['error']
