# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from ...._models import BaseModel
from .run_status import RunStatus
from ..assistant_tool import AssistantTool
from ...shared.metadata import Metadata
from ..assistant_tool_choice_option import AssistantToolChoiceOption
from ..assistant_response_format_option import AssistantResponseFormatOption
from .required_action_function_tool_call import RequiredActionFunctionToolCall

class IncompleteDetails(BaseModel):
    """Details on why the run is incomplete.

    Will be `null` if the run is not incomplete.
    """
    reason: Optional[Literal['max_completion_tokens', 'max_prompt_tokens']] = None

class LastError(BaseModel):
    """The last error associated with this run. Will be `null` if there are no errors."""
    code: Literal['server_error', 'rate_limit_exceeded', 'invalid_prompt']
    message: str

class RequiredActionSubmitToolOutputs(BaseModel):
    """Details on the tool outputs needed for this run to continue."""
    tool_calls: List[RequiredActionFunctionToolCall]

class RequiredAction(BaseModel):
    """Details on the action required to continue the run.

    Will be `null` if no action is required.
    """
    submit_tool_outputs: RequiredActionSubmitToolOutputs
    type: Literal['submit_tool_outputs']

class TruncationStrategy(BaseModel):
    """Controls for how a thread will be truncated prior to the run.

    Use this to control the initial context window of the run.
    """
    type: Literal['auto', 'last_messages']
    last_messages: Optional[int] = None

class Usage(BaseModel):
    """Usage statistics related to the run.

    This value will be `null` if the run is not in a terminal state (i.e. `in_progress`, `queued`, etc.).
    """
    completion_tokens: int
    prompt_tokens: int
    total_tokens: int

class Run(BaseModel):
    """
    Represents an execution run on a [thread](https://developers.openai.com/api/docs/assistants/migration).
    """
    id: str
    assistant_id: str
    cancelled_at: Optional[int] = None
    completed_at: Optional[int] = None
    created_at: int
    expires_at: Optional[int] = None
    failed_at: Optional[int] = None
    incomplete_details: Optional[IncompleteDetails] = None
    instructions: str
    last_error: Optional[LastError] = None
    max_completion_tokens: Optional[int] = None
    max_prompt_tokens: Optional[int] = None
    metadata: Optional[Metadata] = None
    model: str
    object: Literal['thread.run']
    parallel_tool_calls: bool
    required_action: Optional[RequiredAction] = None
    response_format: Optional[AssistantResponseFormatOption] = None
    started_at: Optional[int] = None
    status: RunStatus
    thread_id: str
    tool_choice: Optional[AssistantToolChoiceOption] = None
    tools: List[AssistantTool]
    truncation_strategy: Optional[TruncationStrategy] = None
    usage: Optional[Usage] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
