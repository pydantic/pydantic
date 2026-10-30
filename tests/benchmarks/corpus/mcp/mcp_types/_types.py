# Frozen from MCP 2.3.0; see corpus README.md and LICENSE.
from __future__ import annotations
from typing import Annotated, Any, ClassVar, Final, Generic, Literal, TypeAlias, TypeVar, get_args
from pydantic import BaseModel, ConfigDict, Field, FileUrl, TypeAdapter, model_validator
from pydantic.alias_generators import to_camel
from typing_extensions import NotRequired, Self, TypedDict
from mcp_types.jsonrpc import RequestId
DEFAULT_NEGOTIATED_VERSION: Final[str] = '2025-03-26'
ProgressToken = str | int
Role = Literal['user', 'assistant']
IconTheme = Literal['light', 'dark']

class MCPModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
Meta: TypeAlias = dict[str, Any]
PROTOCOL_VERSION_META_KEY = 'io.modelcontextprotocol/protocolVersion'
CLIENT_INFO_META_KEY = 'io.modelcontextprotocol/clientInfo'
CLIENT_CAPABILITIES_META_KEY = 'io.modelcontextprotocol/clientCapabilities'
LOG_LEVEL_META_KEY = 'io.modelcontextprotocol/logLevel'
SERVER_INFO_META_KEY = 'io.modelcontextprotocol/serverInfo'

class RequestParamsMeta(TypedDict, extra_items=Any):
    progress_token: NotRequired[ProgressToken]

class RequestParams(MCPModel):
    meta: RequestParamsMeta | None = Field(alias='_meta', default=None)

class PaginatedRequestParams(RequestParams):
    cursor: str | None = None

class NotificationParams(MCPModel):
    meta: Meta | None = Field(alias='_meta', default=None)
RequestParamsT = TypeVar('RequestParamsT', bound=RequestParams | dict[str, Any] | None)
NotificationParamsT = TypeVar('NotificationParamsT', bound=NotificationParams | dict[str, Any] | None)
MethodT = TypeVar('MethodT', bound=str)

class Request(MCPModel, Generic[RequestParamsT, MethodT]):
    method: MethodT
    params: RequestParamsT
    name_param: ClassVar[str | None] = None

class PaginatedRequest(Request[PaginatedRequestParams | None, MethodT], Generic[MethodT]):
    params: PaginatedRequestParams | None = None

class Notification(MCPModel, Generic[NotificationParamsT, MethodT]):
    method: MethodT
    params: NotificationParamsT
_CoreResultType = Literal['complete', 'input_required']
ResultType = _CoreResultType | str
CORE_RESULT_TYPES: Final[frozenset[str]] = frozenset(get_args(_CoreResultType))

class Result(MCPModel):
    meta: Meta | None = Field(alias='_meta', default=None)

class PaginatedResult(Result):
    next_cursor: str | None = None

class CacheableResult(Result):
    ttl_ms: Annotated[int, Field(ge=0)] = 0
    cache_scope: Literal['public', 'private'] = 'private'

class EmptyResult(Result):
    result_type: ResultType | None = None

class BaseMetadata(MCPModel):
    name: str
    title: str | None = None

class Icon(MCPModel):
    src: str
    mime_type: str | None = None
    sizes: list[str] | None = None
    theme: IconTheme | None = None

class Implementation(BaseMetadata):
    version: str
    description: str | None = None
    website_url: str | None = None
    icons: list[Icon] | None = None

class RootsCapability(MCPModel):
    list_changed: bool | None = None

class SamplingContextCapability(MCPModel):
    pass

class SamplingToolsCapability(MCPModel):
    pass

class FormElicitationCapability(MCPModel):
    pass

class UrlElicitationCapability(MCPModel):
    pass

class ElicitationCapability(MCPModel):
    form: FormElicitationCapability | None = None
    url: UrlElicitationCapability | None = None

class SamplingCapability(MCPModel):
    context: SamplingContextCapability | None = None
    tools: SamplingToolsCapability | None = None

class TasksListCapability(MCPModel):
    pass

class TasksCancelCapability(MCPModel):
    pass

class TasksCreateMessageCapability(MCPModel):
    pass

class TasksSamplingCapability(MCPModel):
    create_message: TasksCreateMessageCapability | None = None

class TasksCreateElicitationCapability(MCPModel):
    pass

class TasksElicitationCapability(MCPModel):
    create: TasksCreateElicitationCapability | None = None

class ClientTasksRequestsCapability(MCPModel):
    sampling: TasksSamplingCapability | None = None
    elicitation: TasksElicitationCapability | None = None

class ClientTasksCapability(MCPModel):
    list: TasksListCapability | None = None
    cancel: TasksCancelCapability | None = None
    requests: ClientTasksRequestsCapability | None = None

class ClientCapabilities(MCPModel):
    experimental: dict[str, dict[str, Any]] | None = None
    sampling: SamplingCapability | None = None
    elicitation: ElicitationCapability | None = None
    roots: RootsCapability | None = None
    extensions: dict[str, dict[str, Any]] | None = None
    tasks: ClientTasksCapability | None = None

class UnsupportedProtocolVersionErrorData(MCPModel):
    supported: list[str]
    requested: str

class MissingRequiredClientCapabilityErrorData(MCPModel):
    required_capabilities: ClientCapabilities

class PromptsCapability(MCPModel):
    list_changed: bool | None = None

class ResourcesCapability(MCPModel):
    subscribe: bool | None = None
    list_changed: bool | None = None

class ToolsCapability(MCPModel):
    list_changed: bool | None = None

class LoggingCapability(MCPModel):
    pass

class CompletionsCapability(MCPModel):
    pass

class TasksCallCapability(MCPModel):
    pass

class TasksToolsCapability(MCPModel):
    call: TasksCallCapability | None = None

class ServerTasksRequestsCapability(MCPModel):
    tools: TasksToolsCapability | None = None

class ServerTasksCapability(MCPModel):
    list: TasksListCapability | None = None
    cancel: TasksCancelCapability | None = None
    requests: ServerTasksRequestsCapability | None = None

class ServerCapabilities(MCPModel):
    experimental: dict[str, dict[str, Any]] | None = None
    logging: LoggingCapability | None = None
    prompts: PromptsCapability | None = None
    resources: ResourcesCapability | None = None
    tools: ToolsCapability | None = None
    completions: CompletionsCapability | None = None
    extensions: dict[str, dict[str, Any]] | None = None
    tasks: ServerTasksCapability | None = None

class InitializeRequestParams(RequestParams):
    protocol_version: str
    capabilities: ClientCapabilities
    client_info: Implementation

class InitializeRequest(Request[InitializeRequestParams, Literal['initialize']]):
    method: Literal['initialize'] = 'initialize'
    params: InitializeRequestParams

class InitializeResult(Result):
    protocol_version: str
    capabilities: ServerCapabilities
    server_info: Implementation
    instructions: str | None = None

class InitializedNotification(Notification[NotificationParams | None, Literal['notifications/initialized']]):
    method: Literal['notifications/initialized'] = 'notifications/initialized'
    params: NotificationParams | None = None

class PingRequest(Request[RequestParams | None, Literal['ping']]):
    method: Literal['ping'] = 'ping'
    params: RequestParams | None = None

class DiscoverRequest(Request[RequestParams | None, Literal['server/discover']]):
    method: Literal['server/discover'] = 'server/discover'
    params: RequestParams | None = None

class DiscoverResult(CacheableResult):
    supported_versions: list[str]
    capabilities: ServerCapabilities
    instructions: str | None = None
    result_type: ResultType = 'complete'

class ToolExecution(MCPModel):
    task_support: Literal['forbidden', 'optional', 'required'] | None = None

class TaskMetadata(MCPModel):
    ttl: int | None = None

class RelatedTaskMetadata(MCPModel):
    task_id: str
TaskStatus = Literal['working', 'input_required', 'completed', 'failed', 'cancelled']

class Task(MCPModel):
    task_id: str
    status: TaskStatus
    status_message: str | None = None
    created_at: str
    last_updated_at: str
    ttl: int | None
    poll_interval: int | None = None

class CreateTaskResult(Result):
    task: Task

class GetTaskRequestParams(RequestParams):
    task_id: str

class GetTaskRequest(Request[GetTaskRequestParams, Literal['tasks/get']]):
    method: Literal['tasks/get'] = 'tasks/get'
    params: GetTaskRequestParams

class GetTaskResult(Result, Task):
    pass

class CancelTaskRequestParams(RequestParams):
    task_id: str

class CancelTaskRequest(Request[CancelTaskRequestParams, Literal['tasks/cancel']]):
    method: Literal['tasks/cancel'] = 'tasks/cancel'
    params: CancelTaskRequestParams

class CancelTaskResult(Result, Task):
    pass

class TaskStatusNotificationParams(NotificationParams, Task):
    pass

class TaskStatusNotification(Notification[TaskStatusNotificationParams, Literal['notifications/tasks/status']]):
    method: Literal['notifications/tasks/status'] = 'notifications/tasks/status'
    params: TaskStatusNotificationParams

class GetTaskPayloadRequestParams(RequestParams):
    task_id: str

class GetTaskPayloadRequest(Request[GetTaskPayloadRequestParams, Literal['tasks/result']]):
    method: Literal['tasks/result'] = 'tasks/result'
    params: GetTaskPayloadRequestParams

class GetTaskPayloadResult(Result):
    pass

class ListTasksRequest(PaginatedRequest[Literal['tasks/list']]):
    method: Literal['tasks/list'] = 'tasks/list'

class ListTasksResult(PaginatedResult):
    tasks: list[Task]

class ProgressNotificationParams(NotificationParams):
    progress_token: ProgressToken
    progress: float
    total: float | None = None
    message: str | None = None

class ProgressNotification(Notification[ProgressNotificationParams, Literal['notifications/progress']]):
    method: Literal['notifications/progress'] = 'notifications/progress'
    params: ProgressNotificationParams

class ListResourcesRequest(PaginatedRequest[Literal['resources/list']]):
    method: Literal['resources/list'] = 'resources/list'

class Annotations(MCPModel):
    audience: list[Role] | None = None
    priority: Annotated[float, Field(ge=0.0, le=1.0)] | None = None
    last_modified: str | None = None

class Resource(BaseMetadata):
    uri: str
    description: str | None = None
    mime_type: str | None = None
    size: int | None = None
    icons: list[Icon] | None = None
    annotations: Annotations | None = None
    meta: Meta | None = Field(alias='_meta', default=None)

class ResourceTemplate(BaseMetadata):
    uri_template: str
    description: str | None = None
    mime_type: str | None = None
    icons: list[Icon] | None = None
    annotations: Annotations | None = None
    meta: Meta | None = Field(alias='_meta', default=None)

class ListResourcesResult(PaginatedResult, CacheableResult):
    resources: list[Resource]
    result_type: ResultType = 'complete'

class ListResourceTemplatesRequest(PaginatedRequest[Literal['resources/templates/list']]):
    method: Literal['resources/templates/list'] = 'resources/templates/list'

class ListResourceTemplatesResult(PaginatedResult, CacheableResult):
    resource_templates: list[ResourceTemplate]
    result_type: ResultType = 'complete'

class InputResponseRequestParams(RequestParams):
    input_responses: InputResponses | None = None
    request_state: str | None = None

class ReadResourceRequestParams(InputResponseRequestParams):
    uri: str

class ReadResourceRequest(Request[ReadResourceRequestParams, Literal['resources/read']]):
    method: Literal['resources/read'] = 'resources/read'
    params: ReadResourceRequestParams

class ResourceContents(MCPModel):
    uri: str
    mime_type: str | None = None
    meta: Meta | None = Field(alias='_meta', default=None)

class TextResourceContents(ResourceContents):
    text: str

class BlobResourceContents(ResourceContents):
    blob: str

class ReadResourceResult(CacheableResult):
    contents: list[TextResourceContents | BlobResourceContents]
    result_type: ResultType = 'complete'

class ResourceListChangedNotification(Notification[NotificationParams | None, Literal['notifications/resources/list_changed']]):
    method: Literal['notifications/resources/list_changed'] = 'notifications/resources/list_changed'
    params: NotificationParams | None = None

class SubscribeRequestParams(RequestParams):
    uri: str

class SubscribeRequest(Request[SubscribeRequestParams, Literal['resources/subscribe']]):
    method: Literal['resources/subscribe'] = 'resources/subscribe'
    params: SubscribeRequestParams

class UnsubscribeRequestParams(RequestParams):
    uri: str

class UnsubscribeRequest(Request[UnsubscribeRequestParams, Literal['resources/unsubscribe']]):
    method: Literal['resources/unsubscribe'] = 'resources/unsubscribe'
    params: UnsubscribeRequestParams

class ResourceUpdatedNotificationParams(NotificationParams):
    uri: str

class ResourceUpdatedNotification(Notification[ResourceUpdatedNotificationParams, Literal['notifications/resources/updated']]):
    method: Literal['notifications/resources/updated'] = 'notifications/resources/updated'
    params: ResourceUpdatedNotificationParams

class SubscriptionFilter(MCPModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra='allow')
    tools_list_changed: bool | None = None
    prompts_list_changed: bool | None = None
    resources_list_changed: bool | None = None
    resource_subscriptions: list[str] | None = None

class SubscriptionsListenRequestParams(RequestParams):
    notifications: SubscriptionFilter

class SubscriptionsListenRequest(Request[SubscriptionsListenRequestParams, Literal['subscriptions/listen']]):
    method: Literal['subscriptions/listen'] = 'subscriptions/listen'
    params: SubscriptionsListenRequestParams

class SubscriptionsAcknowledgedNotificationParams(NotificationParams):
    notifications: SubscriptionFilter

class SubscriptionsAcknowledgedNotification(Notification[SubscriptionsAcknowledgedNotificationParams, Literal['notifications/subscriptions/acknowledged']]):
    method: Literal['notifications/subscriptions/acknowledged'] = 'notifications/subscriptions/acknowledged'
    params: SubscriptionsAcknowledgedNotificationParams

class SubscriptionsListenResult(Result):
    result_type: ResultType = 'complete'

class ListPromptsRequest(PaginatedRequest[Literal['prompts/list']]):
    method: Literal['prompts/list'] = 'prompts/list'

class PromptArgument(BaseMetadata):
    description: str | None = None
    required: bool | None = None

class Prompt(BaseMetadata):
    description: str | None = None
    arguments: list[PromptArgument] | None = None
    icons: list[Icon] | None = None
    meta: Meta | None = Field(alias='_meta', default=None)

class ListPromptsResult(PaginatedResult, CacheableResult):
    prompts: list[Prompt]
    result_type: ResultType = 'complete'

class GetPromptRequestParams(InputResponseRequestParams):
    name: str
    arguments: dict[str, str] | None = None

class GetPromptRequest(Request[GetPromptRequestParams, Literal['prompts/get']]):
    method: Literal['prompts/get'] = 'prompts/get'
    params: GetPromptRequestParams

class TextContent(MCPModel):
    type: Literal['text'] = 'text'
    text: str
    annotations: Annotations | None = None
    meta: Meta | None = Field(alias='_meta', default=None)

class ImageContent(MCPModel):
    type: Literal['image'] = 'image'
    data: str
    mime_type: str
    annotations: Annotations | None = None
    meta: Meta | None = Field(alias='_meta', default=None)

class AudioContent(MCPModel):
    type: Literal['audio'] = 'audio'
    data: str
    mime_type: str
    annotations: Annotations | None = None
    meta: Meta | None = Field(alias='_meta', default=None)

class ToolUseContent(MCPModel):
    type: Literal['tool_use'] = 'tool_use'
    name: str
    id: str
    input: dict[str, Any]
    meta: Meta | None = Field(alias='_meta', default=None)

class ToolResultContent(MCPModel):
    type: Literal['tool_result'] = 'tool_result'
    tool_use_id: str
    content: list[ContentBlock] = []
    structured_content: Any = None
    is_error: bool | None = None
    meta: Meta | None = Field(alias='_meta', default=None)
SamplingMessageContentBlock: TypeAlias = TextContent | ImageContent | AudioContent | ToolUseContent | ToolResultContent
SamplingContent: TypeAlias = TextContent | ImageContent | AudioContent

class SamplingMessage(MCPModel):
    role: Role
    content: SamplingMessageContentBlock | list[SamplingMessageContentBlock]
    meta: Meta | None = Field(alias='_meta', default=None)

class EmbeddedResource(MCPModel):
    type: Literal['resource'] = 'resource'
    resource: TextResourceContents | BlobResourceContents
    annotations: Annotations | None = None
    meta: Meta | None = Field(alias='_meta', default=None)

class ResourceLink(Resource):
    type: Literal['resource_link'] = 'resource_link'
ContentBlock = TextContent | ImageContent | AudioContent | ResourceLink | EmbeddedResource

class PromptMessage(MCPModel):
    role: Role
    content: ContentBlock

class GetPromptResult(Result):
    description: str | None = None
    messages: list[PromptMessage]
    result_type: ResultType = 'complete'

class PromptListChangedNotification(Notification[NotificationParams | None, Literal['notifications/prompts/list_changed']]):
    method: Literal['notifications/prompts/list_changed'] = 'notifications/prompts/list_changed'
    params: NotificationParams | None = None

class ListToolsRequest(PaginatedRequest[Literal['tools/list']]):
    method: Literal['tools/list'] = 'tools/list'

class ToolAnnotations(MCPModel):
    title: str | None = None
    read_only_hint: bool | None = None
    destructive_hint: bool | None = None
    idempotent_hint: bool | None = None
    open_world_hint: bool | None = None

class Tool(BaseMetadata):
    description: str | None = None
    input_schema: dict[str, Any]
    execution: ToolExecution | None = None
    output_schema: dict[str, Any] | None = None
    icons: list[Icon] | None = None
    annotations: ToolAnnotations | None = None
    meta: Meta | None = Field(alias='_meta', default=None)

class ListToolsResult(PaginatedResult, CacheableResult):
    tools: list[Tool]
    result_type: ResultType = 'complete'

class CallToolRequestParams(InputResponseRequestParams):
    name: str
    arguments: dict[str, Any] | None = None
    task: TaskMetadata | None = None

class CallToolRequest(Request[CallToolRequestParams, Literal['tools/call']]):
    method: Literal['tools/call'] = 'tools/call'
    params: CallToolRequestParams

class CallToolResult(Result):
    content: list[ContentBlock]
    structured_content: Any = None
    is_error: bool = False
    result_type: ResultType = 'complete'

class ToolListChangedNotification(Notification[NotificationParams | None, Literal['notifications/tools/list_changed']]):
    method: Literal['notifications/tools/list_changed'] = 'notifications/tools/list_changed'
    params: NotificationParams | None = None
LoggingLevel = Literal['debug', 'info', 'notice', 'warning', 'error', 'critical', 'alert', 'emergency']

class SetLevelRequestParams(RequestParams):
    level: LoggingLevel

class SetLevelRequest(Request[SetLevelRequestParams, Literal['logging/setLevel']]):
    method: Literal['logging/setLevel'] = 'logging/setLevel'
    params: SetLevelRequestParams

class LoggingMessageNotificationParams(NotificationParams):
    level: LoggingLevel
    logger: str | None = None
    data: Any

class LoggingMessageNotification(Notification[LoggingMessageNotificationParams, Literal['notifications/message']]):
    method: Literal['notifications/message'] = 'notifications/message'
    params: LoggingMessageNotificationParams
IncludeContext = Literal['none', 'thisServer', 'allServers']

class ModelHint(MCPModel):
    name: str | None = None

class ModelPreferences(MCPModel):
    hints: list[ModelHint] | None = None
    cost_priority: float | None = None
    speed_priority: float | None = None
    intelligence_priority: float | None = None

class ToolChoice(MCPModel):
    mode: Literal['auto', 'required', 'none'] | None = None

class CreateMessageRequestParams(RequestParams):
    messages: list[SamplingMessage]
    model_preferences: ModelPreferences | None = None
    system_prompt: str | None = None
    include_context: IncludeContext | None = None
    temperature: float | None = None
    max_tokens: int
    stop_sequences: list[str] | None = None
    metadata: dict[str, Any] | None = None
    tools: list[Tool] | None = None
    tool_choice: ToolChoice | None = None
    task: TaskMetadata | None = None

class CreateMessageRequest(Request[CreateMessageRequestParams, Literal['sampling/createMessage']]):
    method: Literal['sampling/createMessage'] = 'sampling/createMessage'
    params: CreateMessageRequestParams
StopReason = Literal['endTurn', 'stopSequence', 'maxTokens', 'toolUse'] | str

class CreateMessageResult(Result):
    role: Role
    content: SamplingContent
    model: str
    stop_reason: StopReason | None = None

class CreateMessageResultWithTools(Result):
    role: Role
    content: SamplingMessageContentBlock | list[SamplingMessageContentBlock]
    model: str
    stop_reason: StopReason | None = None

class ResourceTemplateReference(MCPModel):
    type: Literal['ref/resource'] = 'ref/resource'
    uri: str

class PromptReference(MCPModel):
    type: Literal['ref/prompt'] = 'ref/prompt'
    name: str
    title: str | None = None

class CompletionArgument(MCPModel):
    name: str
    value: str

class CompletionContext(MCPModel):
    arguments: dict[str, str] | None = None

class CompleteRequestParams(RequestParams):
    ref: ResourceTemplateReference | PromptReference
    argument: CompletionArgument
    context: CompletionContext | None = None

class CompleteRequest(Request[CompleteRequestParams, Literal['completion/complete']]):
    method: Literal['completion/complete'] = 'completion/complete'
    params: CompleteRequestParams

class Completion(MCPModel):
    values: list[str]
    total: int | None = None
    has_more: bool | None = None

class CompleteResult(Result):
    completion: Completion
    result_type: ResultType = 'complete'

class ListRootsRequest(Request[RequestParams | None, Literal['roots/list']]):
    method: Literal['roots/list'] = 'roots/list'
    params: RequestParams | None = None

class Root(MCPModel):
    uri: FileUrl
    name: str | None = None
    meta: Meta | None = Field(alias='_meta', default=None)

class ListRootsResult(Result):
    roots: list[Root]

class RootsListChangedNotification(Notification[NotificationParams | None, Literal['notifications/roots/list_changed']]):
    method: Literal['notifications/roots/list_changed'] = 'notifications/roots/list_changed'
    params: NotificationParams | None = None

class CancelledNotificationParams(NotificationParams):
    request_id: RequestId | None = None
    reason: str | None = None

class CancelledNotification(Notification[CancelledNotificationParams, Literal['notifications/cancelled']]):
    method: Literal['notifications/cancelled'] = 'notifications/cancelled'
    params: CancelledNotificationParams

class ElicitCompleteNotificationParams(NotificationParams):
    elicitation_id: str

class ElicitCompleteNotification(Notification[ElicitCompleteNotificationParams, Literal['notifications/elicitation/complete']]):
    method: Literal['notifications/elicitation/complete'] = 'notifications/elicitation/complete'
    params: ElicitCompleteNotificationParams
ElicitRequestedSchema: TypeAlias = dict[str, Any]

class ElicitRequestFormParams(RequestParams):
    mode: Literal['form'] = 'form'
    message: str
    requested_schema: ElicitRequestedSchema
    task: TaskMetadata | None = None

class ElicitRequestURLParams(RequestParams):
    mode: Literal['url'] = 'url'
    message: str
    url: str
    elicitation_id: str | None = None
    task: TaskMetadata | None = None
ElicitRequestParams: TypeAlias = ElicitRequestURLParams | ElicitRequestFormParams

class ElicitRequest(Request[ElicitRequestParams, Literal['elicitation/create']]):
    method: Literal['elicitation/create'] = 'elicitation/create'
    params: ElicitRequestParams

class ElicitResult(Result):
    action: Literal['accept', 'decline', 'cancel']
    content: dict[str, str | int | float | bool | list[str] | None] | None = None

class ElicitationRequiredErrorData(MCPModel):
    elicitations: list[ElicitRequestURLParams]
InputRequest: TypeAlias = CreateMessageRequest | ListRootsRequest | ElicitRequest
InputRequests: TypeAlias = dict[str, InputRequest]
InputResponse: TypeAlias = CreateMessageResult | CreateMessageResultWithTools | ListRootsResult | ElicitResult
InputResponses: TypeAlias = dict[str, InputResponse]

class InputRequiredResult(Result):
    result_type: Literal['input_required'] = 'input_required'
    input_requests: InputRequests | None = None
    request_state: str | None = None

    @model_validator(mode='after')
    def _require_one_field(self) -> Self:
        if not self.input_requests and self.request_state is None:
            raise ValueError('InputRequiredResult requires at least one of input_requests or request_state')
        return self
ClientRequest = PingRequest | InitializeRequest | CompleteRequest | SetLevelRequest | GetPromptRequest | ListPromptsRequest | ListResourcesRequest | ListResourceTemplatesRequest | ReadResourceRequest | SubscribeRequest | UnsubscribeRequest | CallToolRequest | ListToolsRequest | DiscoverRequest | SubscriptionsListenRequest
client_request_adapter = TypeAdapter[ClientRequest](ClientRequest)
ClientNotification = CancelledNotification | ProgressNotification | InitializedNotification | RootsListChangedNotification
client_notification_adapter = TypeAdapter[ClientNotification](ClientNotification)
ClientResult = EmptyResult | CreateMessageResult | CreateMessageResultWithTools | ListRootsResult | ElicitResult
client_result_adapter = TypeAdapter[ClientResult](ClientResult)
ServerRequest = PingRequest | CreateMessageRequest | ListRootsRequest | ElicitRequest
server_request_adapter = TypeAdapter[ServerRequest](ServerRequest)
ServerNotification = CancelledNotification | ProgressNotification | LoggingMessageNotification | ResourceUpdatedNotification | ResourceListChangedNotification | ToolListChangedNotification | PromptListChangedNotification | ElicitCompleteNotification | SubscriptionsAcknowledgedNotification
server_notification_adapter = TypeAdapter[ServerNotification](ServerNotification)
ServerResult = EmptyResult | InitializeResult | DiscoverResult | CompleteResult | GetPromptResult | ListPromptsResult | ListResourcesResult | ListResourceTemplatesResult | ReadResourceResult | CallToolResult | ListToolsResult | SubscriptionsListenResult | InputRequiredResult
server_result_adapter = TypeAdapter[ServerResult](ServerResult)
