# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Dict, Union, Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_response_failed_event import BetaResponseFailedEvent
from .beta_response_queued_event import BetaResponseQueuedEvent
from .beta_response_created_event import BetaResponseCreatedEvent
from .beta_response_completed_event import BetaResponseCompletedEvent
from .beta_response_text_done_event import BetaResponseTextDoneEvent
from .beta_response_audio_done_event import BetaResponseAudioDoneEvent
from .beta_response_incomplete_event import BetaResponseIncompleteEvent
from .beta_response_text_delta_event import BetaResponseTextDeltaEvent
from .beta_response_audio_delta_event import BetaResponseAudioDeltaEvent
from .beta_response_in_progress_event import BetaResponseInProgressEvent
from .beta_response_refusal_done_event import BetaResponseRefusalDoneEvent
from .beta_response_refusal_delta_event import BetaResponseRefusalDeltaEvent
from .beta_response_mcp_call_failed_event import BetaResponseMcpCallFailedEvent
from .beta_response_output_item_done_event import BetaResponseOutputItemDoneEvent
from .beta_response_content_part_done_event import BetaResponseContentPartDoneEvent
from .beta_response_output_item_added_event import BetaResponseOutputItemAddedEvent
from .beta_response_content_part_added_event import BetaResponseContentPartAddedEvent
from .beta_response_mcp_call_completed_event import BetaResponseMcpCallCompletedEvent
from .beta_response_reasoning_text_done_event import BetaResponseReasoningTextDoneEvent
from .beta_response_mcp_call_in_progress_event import BetaResponseMcpCallInProgressEvent
from .beta_response_reasoning_text_delta_event import BetaResponseReasoningTextDeltaEvent
from .beta_response_audio_transcript_done_event import BetaResponseAudioTranscriptDoneEvent
from .beta_response_compaction_compacting_event import BetaResponseCompactionCompactingEvent
from .beta_response_mcp_list_tools_failed_event import BetaResponseMcpListToolsFailedEvent
from .beta_response_audio_transcript_delta_event import BetaResponseAudioTranscriptDeltaEvent
from .beta_response_mcp_call_arguments_done_event import BetaResponseMcpCallArgumentsDoneEvent
from .beta_response_shell_call_command_done_event import BetaResponseShellCallCommandDoneEvent
from .beta_response_image_gen_call_completed_event import BetaResponseImageGenCallCompletedEvent
from .beta_response_mcp_call_arguments_delta_event import BetaResponseMcpCallArgumentsDeltaEvent
from .beta_response_mcp_list_tools_completed_event import BetaResponseMcpListToolsCompletedEvent
from .beta_response_shell_call_command_added_event import BetaResponseShellCallCommandAddedEvent
from .beta_response_shell_call_command_delta_event import BetaResponseShellCallCommandDeltaEvent
from .beta_response_image_gen_call_generating_event import BetaResponseImageGenCallGeneratingEvent
from .beta_response_web_search_call_completed_event import BetaResponseWebSearchCallCompletedEvent
from .beta_response_web_search_call_searching_event import BetaResponseWebSearchCallSearchingEvent
from .beta_response_file_search_call_completed_event import BetaResponseFileSearchCallCompletedEvent
from .beta_response_file_search_call_searching_event import BetaResponseFileSearchCallSearchingEvent
from .beta_response_image_gen_call_in_progress_event import BetaResponseImageGenCallInProgressEvent
from .beta_response_mcp_list_tools_in_progress_event import BetaResponseMcpListToolsInProgressEvent
from .beta_response_custom_tool_call_input_done_event import BetaResponseCustomToolCallInputDoneEvent
from .beta_response_reasoning_summary_part_done_event import BetaResponseReasoningSummaryPartDoneEvent
from .beta_response_reasoning_summary_text_done_event import BetaResponseReasoningSummaryTextDoneEvent
from .beta_response_web_search_call_in_progress_event import BetaResponseWebSearchCallInProgressEvent
from .beta_response_custom_tool_call_input_delta_event import BetaResponseCustomToolCallInputDeltaEvent
from .beta_response_file_search_call_in_progress_event import BetaResponseFileSearchCallInProgressEvent
from .beta_response_function_call_arguments_done_event import BetaResponseFunctionCallArgumentsDoneEvent
from .beta_response_image_gen_call_partial_image_event import BetaResponseImageGenCallPartialImageEvent
from .beta_response_output_text_annotation_added_event import BetaResponseOutputTextAnnotationAddedEvent
from .beta_response_reasoning_summary_part_added_event import BetaResponseReasoningSummaryPartAddedEvent
from .beta_response_reasoning_summary_text_delta_event import BetaResponseReasoningSummaryTextDeltaEvent
from .beta_response_function_call_arguments_delta_event import BetaResponseFunctionCallArgumentsDeltaEvent
from .beta_response_shell_call_output_content_done_event import BetaResponseShellCallOutputContentDoneEvent
from .beta_response_code_interpreter_call_code_done_event import BetaResponseCodeInterpreterCallCodeDoneEvent
from .beta_response_code_interpreter_call_completed_event import BetaResponseCodeInterpreterCallCompletedEvent
from .beta_response_shell_call_output_content_delta_event import BetaResponseShellCallOutputContentDeltaEvent
from .beta_response_code_interpreter_call_code_delta_event import BetaResponseCodeInterpreterCallCodeDeltaEvent
from .beta_response_code_interpreter_call_in_progress_event import BetaResponseCodeInterpreterCallInProgressEvent
from .beta_response_code_interpreter_call_interpreting_event import BetaResponseCodeInterpreterCallInterpretingEvent

class BetaResponseAudioWsDelta(BetaResponseAudioDeltaEvent):
    """Emitted when there is a partial audio response."""
    stream_id: Optional[str] = None

class BetaResponseAudioWsDone(BetaResponseAudioDoneEvent):
    """Emitted when the audio response is complete."""
    stream_id: Optional[str] = None

class BetaResponseAudioTranscriptWsDelta(BetaResponseAudioTranscriptDeltaEvent):
    """Emitted when there is a partial transcript of audio."""
    stream_id: Optional[str] = None

class BetaResponseAudioTranscriptWsDone(BetaResponseAudioTranscriptDoneEvent):
    """Emitted when the full audio transcript is completed."""
    stream_id: Optional[str] = None

class BetaResponseCodeInterpreterCallCodeWsDelta(BetaResponseCodeInterpreterCallCodeDeltaEvent):
    """Emitted when a partial code snippet is streamed by the code interpreter."""
    stream_id: Optional[str] = None

class BetaResponseCodeInterpreterCallCodeWsDone(BetaResponseCodeInterpreterCallCodeDoneEvent):
    """Emitted when the code snippet is finalized by the code interpreter."""
    stream_id: Optional[str] = None

class BetaResponseCodeInterpreterCallWsCompleted(BetaResponseCodeInterpreterCallCompletedEvent):
    """Emitted when the code interpreter call is completed."""
    stream_id: Optional[str] = None

class BetaResponseCodeInterpreterCallInWsProgress(BetaResponseCodeInterpreterCallInProgressEvent):
    """Emitted when a code interpreter call is in progress."""
    stream_id: Optional[str] = None

class BetaResponseCodeInterpreterCallWsInterpreting(BetaResponseCodeInterpreterCallInterpretingEvent):
    """Emitted when the code interpreter is actively interpreting the code snippet."""
    stream_id: Optional[str] = None

class BetaResponseCompactionWsCompacting(BetaResponseCompactionCompactingEvent):
    """Emitted when new summary content is sampled for a compaction trigger.

    Contains no summary content.
    """
    stream_id: Optional[str] = None

class BetaResponseWsCompleted(BetaResponseCompletedEvent):
    """Emitted when the model response is complete."""
    stream_id: Optional[str] = None

class BetaResponseContentPartWsAdded(BetaResponseContentPartAddedEvent):
    """Emitted when a new content part is added."""
    stream_id: Optional[str] = None

class BetaResponseContentPartWsDone(BetaResponseContentPartDoneEvent):
    """Emitted when a content part is done."""
    stream_id: Optional[str] = None

class BetaResponseWsCreated(BetaResponseCreatedEvent):
    """An event that is emitted when a response is created."""
    stream_id: Optional[str] = None

class BetaResponseFileSearchCallWsCompleted(BetaResponseFileSearchCallCompletedEvent):
    """Emitted when a file search call is completed (results found)."""
    stream_id: Optional[str] = None

class BetaResponseFileSearchCallInWsProgress(BetaResponseFileSearchCallInProgressEvent):
    """Emitted when a file search call is initiated."""
    stream_id: Optional[str] = None

class BetaResponseFileSearchCallWsSearching(BetaResponseFileSearchCallSearchingEvent):
    """Emitted when a file search is currently searching."""
    stream_id: Optional[str] = None

class BetaResponseFunctionCallArgumentsWsDelta(BetaResponseFunctionCallArgumentsDeltaEvent):
    """Emitted when there is a partial function-call arguments delta."""
    stream_id: Optional[str] = None

class BetaResponseFunctionCallArgumentsWsDone(BetaResponseFunctionCallArgumentsDoneEvent):
    """Emitted when function-call arguments are finalized."""
    stream_id: Optional[str] = None

class BetaResponseShellCallCommandWsAdded(BetaResponseShellCallCommandAddedEvent):
    """A streaming event that indicated a shell command was added to a tool call."""
    stream_id: Optional[str] = None

class BetaResponseShellCallCommandWsDelta(BetaResponseShellCallCommandDeltaEvent):
    """A streaming event that indicated a shell command was incrementally updated."""
    stream_id: Optional[str] = None

class BetaResponseShellCallCommandWsDone(BetaResponseShellCallCommandDoneEvent):
    """A streaming event that indicated a shell command was completed."""
    stream_id: Optional[str] = None

class BetaResponseShellCallOutputContentWsDelta(BetaResponseShellCallOutputContentDeltaEvent):
    """A streaming event that indicated shell call output was incrementally added."""
    stream_id: Optional[str] = None

class BetaResponseShellCallOutputContentWsDone(BetaResponseShellCallOutputContentDoneEvent):
    """A streaming event that indicated shell call output was completed."""
    stream_id: Optional[str] = None

class BetaResponseInWsProgress(BetaResponseInProgressEvent):
    """Emitted when the response is in progress."""
    stream_id: Optional[str] = None

class BetaResponseWsFailed(BetaResponseFailedEvent):
    """An event that is emitted when a response fails."""
    stream_id: Optional[str] = None

class BetaResponseWsIncomplete(BetaResponseIncompleteEvent):
    """An event that is emitted when a response finishes as incomplete.

    Over WebSocket, steering can finish a response with
    `response.incomplete_details.reason` set to `steered`, followed automatically
    by a successor `response.created` that commits the queued steering input.
    """
    stream_id: Optional[str] = None

class BetaResponseOutputItemWsAdded(BetaResponseOutputItemAddedEvent):
    """Emitted when a new output item is added."""
    stream_id: Optional[str] = None

class BetaResponseOutputItemWsDone(BetaResponseOutputItemDoneEvent):
    """Emitted when an output item is marked done."""
    stream_id: Optional[str] = None

class BetaResponseReasoningSummaryPartWsAdded(BetaResponseReasoningSummaryPartAddedEvent):
    """Emitted when a new reasoning summary part is added."""
    stream_id: Optional[str] = None

class BetaResponseReasoningSummaryPartWsDone(BetaResponseReasoningSummaryPartDoneEvent):
    """Emitted when a reasoning summary part is completed."""
    stream_id: Optional[str] = None

class BetaResponseReasoningSummaryTextWsDelta(BetaResponseReasoningSummaryTextDeltaEvent):
    """Emitted when a delta is added to a reasoning summary text."""
    stream_id: Optional[str] = None

class BetaResponseReasoningSummaryTextWsDone(BetaResponseReasoningSummaryTextDoneEvent):
    """Emitted when a reasoning summary text is completed."""
    stream_id: Optional[str] = None

class BetaResponseReasoningTextWsDelta(BetaResponseReasoningTextDeltaEvent):
    """Emitted when a delta is added to a reasoning text."""
    stream_id: Optional[str] = None

class BetaResponseReasoningTextWsDone(BetaResponseReasoningTextDoneEvent):
    """Emitted when a reasoning text is completed."""
    stream_id: Optional[str] = None

class BetaResponseRefusalWsDelta(BetaResponseRefusalDeltaEvent):
    """Emitted when there is a partial refusal text."""
    stream_id: Optional[str] = None

class BetaResponseRefusalWsDone(BetaResponseRefusalDoneEvent):
    """Emitted when refusal text is finalized."""
    stream_id: Optional[str] = None

class BetaResponseTextWsDelta(BetaResponseTextDeltaEvent):
    """Emitted when there is an additional text delta."""
    stream_id: Optional[str] = None

class BetaResponseTextWsDone(BetaResponseTextDoneEvent):
    """Emitted when text content is finalized."""
    stream_id: Optional[str] = None

class BetaResponseWebSearchCallWsCompleted(BetaResponseWebSearchCallCompletedEvent):
    """Emitted when a web search call is completed."""
    stream_id: Optional[str] = None

class BetaResponseWebSearchCallInWsProgress(BetaResponseWebSearchCallInProgressEvent):
    """Emitted when a web search call is initiated."""
    stream_id: Optional[str] = None

class BetaResponseWebSearchCallWsSearching(BetaResponseWebSearchCallSearchingEvent):
    """Emitted when a web search call is executing."""
    stream_id: Optional[str] = None

class BetaResponseImageGenCallWsCompleted(BetaResponseImageGenCallCompletedEvent):
    """
    Emitted when an image generation tool call has completed and the final image is available.
    """
    stream_id: Optional[str] = None

class BetaResponseImageGenCallWsGenerating(BetaResponseImageGenCallGeneratingEvent):
    """
    Emitted when an image generation tool call is actively generating an image (intermediate state).
    """
    stream_id: Optional[str] = None

class BetaResponseImageGenCallInWsProgress(BetaResponseImageGenCallInProgressEvent):
    """Emitted when an image generation tool call is in progress."""
    stream_id: Optional[str] = None

class BetaResponseImageGenCallPartialWsImage(BetaResponseImageGenCallPartialImageEvent):
    """Emitted when a partial image is available during image generation streaming."""
    stream_id: Optional[str] = None

class BetaResponseMcpCallArgumentsWsDelta(BetaResponseMcpCallArgumentsDeltaEvent):
    """
    Emitted when there is a delta (partial update) to the arguments of an MCP tool call.
    """
    stream_id: Optional[str] = None

class BetaResponseMcpCallArgumentsWsDone(BetaResponseMcpCallArgumentsDoneEvent):
    """Emitted when the arguments for an MCP tool call are finalized."""
    stream_id: Optional[str] = None

class BetaResponseMcpCallWsCompleted(BetaResponseMcpCallCompletedEvent):
    """Emitted when an MCP  tool call has completed successfully."""
    stream_id: Optional[str] = None

class BetaResponseMcpCallWsFailed(BetaResponseMcpCallFailedEvent):
    """Emitted when an MCP  tool call has failed."""
    stream_id: Optional[str] = None

class BetaResponseMcpCallInWsProgress(BetaResponseMcpCallInProgressEvent):
    """Emitted when an MCP  tool call is in progress."""
    stream_id: Optional[str] = None

class BetaResponseMcpListToolsWsCompleted(BetaResponseMcpListToolsCompletedEvent):
    """Emitted when the list of available MCP tools has been successfully retrieved."""
    stream_id: Optional[str] = None

class BetaResponseMcpListToolsWsFailed(BetaResponseMcpListToolsFailedEvent):
    """Emitted when the attempt to list available MCP tools has failed."""
    stream_id: Optional[str] = None

class BetaResponseMcpListToolsInWsProgress(BetaResponseMcpListToolsInProgressEvent):
    """
    Emitted when the system is in the process of retrieving the list of available MCP tools.
    """
    stream_id: Optional[str] = None

class BetaResponseOutputTextAnnotationWsAdded(BetaResponseOutputTextAnnotationAddedEvent):
    """Emitted when an annotation is added to output text content."""
    stream_id: Optional[str] = None

class BetaResponseWsQueued(BetaResponseQueuedEvent):
    """Emitted when a response is queued and waiting to be processed."""
    stream_id: Optional[str] = None

class BetaResponseCustomToolCallInputWsDelta(BetaResponseCustomToolCallInputDeltaEvent):
    """Event representing a delta (partial update) to the input of a custom tool call."""
    stream_id: Optional[str] = None

class BetaResponseCustomToolCallInputWsDone(BetaResponseCustomToolCallInputDoneEvent):
    """Event indicating that input for a custom tool call is complete."""
    stream_id: Optional[str] = None

class BetaResponseWsErrorErrorMisalignmentSteer(BaseModel):
    """An optional public continuation instruction."""
    message: str

class BetaResponseWsErrorErrorMisalignment(BaseModel):
    detailed_explanation: Optional[str] = None
    error_type: Union[str, Literal['potentially_unintended_data_transfer', 'potentially_unintended_data_access', 'potentially_unintended_destructive_activity', 'other'], None] = None
    review_target: Optional[str] = None
    steer: Optional[BetaResponseWsErrorErrorMisalignmentSteer] = None

class BetaResponseWsErrorError(BaseModel):
    """Details about the error."""
    code: Optional[str] = None
    message: str
    param: Optional[str] = None
    type: str
    headers: Optional[Dict[str, str]] = None
    misalignment: Optional[BetaResponseWsErrorErrorMisalignment] = None

class BetaResponseWsErrorAgent(BaseModel):
    """The agent that owns this multi-agent streaming event."""
    agent_name: str

class BetaResponseWsError(BaseModel):
    """Emitted when an error occurs while processing a Responses WebSocket request."""
    error: BetaResponseWsErrorError
    type: Literal['error']
    agent: Optional[BetaResponseWsErrorAgent] = None
    sequence_number: Optional[int] = None
    status: Optional[int] = None
    stream_id: Optional[str] = None
