# Frozen from MCP 2.3.0; see corpus README.md and LICENSE.
from __future__ import annotations
from typing import Annotated, Any, Literal
from mcp_types._wire_base import WireModel
from pydantic import ConfigDict, Field

class BaseMetadata(WireModel):
    model_config = ConfigDict(extra='ignore')
    name: str
    title: str | None = None

class BlobResourceContents(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[dict[str, Any] | None, Field(alias='_meta')] = None
    blob: str
    mime_type: Annotated[str | None, Field(alias='mimeType')] = None
    uri: str

class BooleanSchema(WireModel):
    model_config = ConfigDict(extra='ignore')
    default: bool | None = None
    description: str | None = None
    title: str | None = None
    type: Literal['boolean']

class Params(WireModel):
    model_config = ConfigDict(extra='ignore')
    task_id: Annotated[str, Field(alias='taskId')]

class Elicitation(WireModel):
    model_config = ConfigDict(extra='ignore')
    form: dict[str, Any] | None = None
    url: dict[str, Any] | None = None

class Roots(WireModel):
    model_config = ConfigDict(extra='ignore')
    list_changed: Annotated[bool | None, Field(alias='listChanged')] = None

class Sampling(WireModel):
    model_config = ConfigDict(extra='ignore')
    context: dict[str, Any] | None = None
    tools: dict[str, Any] | None = None

class Elicitation1(WireModel):
    model_config = ConfigDict(extra='ignore')
    create: dict[str, Any] | None = None

class Sampling1(WireModel):
    model_config = ConfigDict(extra='ignore')
    create_message: Annotated[dict[str, Any] | None, Field(alias='createMessage')] = None

class Requests(WireModel):
    model_config = ConfigDict(extra='ignore')
    elicitation: Elicitation1 | None = None
    sampling: Sampling1 | None = None

class Tasks(WireModel):
    model_config = ConfigDict(extra='ignore')
    cancel: dict[str, Any] | None = None
    list: dict[str, Any] | None = None
    requests: Requests | None = None

class ClientCapabilities(WireModel):
    model_config = ConfigDict(extra='ignore')
    elicitation: Elicitation | None = None
    experimental: dict[str, dict[str, Any]] | None = None
    roots: Roots | None = None
    sampling: Sampling | None = None
    tasks: Tasks | None = None

class Argument(WireModel):
    model_config = ConfigDict(extra='ignore')
    name: str
    value: str

class Context(WireModel):
    model_config = ConfigDict(extra='ignore')
    arguments: dict[str, str] | None = None

class Completion(WireModel):
    model_config = ConfigDict(extra='ignore')
    has_more: Annotated[bool | None, Field(alias='hasMore')] = None
    total: int | None = None
    values: list[str]

class CompleteResult(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[dict[str, Any] | None, Field(alias='_meta')] = None
    completion: Completion
Cursor = str

class RequestedSchema(WireModel):
    model_config = ConfigDict(extra='ignore')
    schema_: Annotated[str | None, Field(alias='$schema')] = None
    properties: dict[str, Any]
    required: list[str] | None = None
    type: Literal['object']

class ElicitResult(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[dict[str, Any] | None, Field(alias='_meta')] = None
    action: Literal['accept', 'cancel', 'decline']
    content: dict[str, list[str] | str | int | float | bool | None] | None = None

class Params1(WireModel):
    model_config = ConfigDict(extra='ignore')
    elicitation_id: Annotated[str, Field(alias='elicitationId')]

class ElicitationCompleteNotification(WireModel):
    model_config = ConfigDict(extra='ignore')
    jsonrpc: Literal['2.0']
    method: Literal['notifications/elicitation/complete']
    params: Params1

class Error(WireModel):
    model_config = ConfigDict(extra='ignore')
    code: int
    data: Any | None = None
    message: str

class Params2(WireModel):
    model_config = ConfigDict(extra='ignore')
    task_id: Annotated[str, Field(alias='taskId')]

class GetTaskPayloadResult(WireModel):
    model_config = ConfigDict(extra='allow')
    meta: Annotated[dict[str, Any] | None, Field(alias='_meta')] = None

class Params3(WireModel):
    model_config = ConfigDict(extra='ignore')
    task_id: Annotated[str, Field(alias='taskId')]

class Icon(WireModel):
    model_config = ConfigDict(extra='ignore')
    mime_type: Annotated[str | None, Field(alias='mimeType')] = None
    sizes: list[str] | None = None
    src: str
    theme: Literal['dark', 'light'] | None = None

class Icons(WireModel):
    model_config = ConfigDict(extra='ignore')
    icons: list[Icon] | None = None

class Implementation(WireModel):
    model_config = ConfigDict(extra='ignore')
    description: str | None = None
    icons: list[Icon] | None = None
    name: str
    title: str | None = None
    version: str
    website_url: Annotated[str | None, Field(alias='websiteUrl')] = None

class JSONRPCNotification(WireModel):
    model_config = ConfigDict(extra='ignore')
    jsonrpc: Literal['2.0']
    method: str
    params: dict[str, Any] | None = None

class LegacyTitledEnumSchema(WireModel):
    model_config = ConfigDict(extra='ignore')
    default: str | None = None
    description: str | None = None
    enum: list[str]
    enum_names: Annotated[list[str] | None, Field(alias='enumNames')] = None
    title: str | None = None
    type: Literal['string']
LoggingLevel = Literal['alert', 'critical', 'debug', 'emergency', 'error', 'info', 'notice', 'warning']

class LoggingMessageNotificationParams(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[dict[str, Any] | None, Field(alias='_meta')] = None
    data: Any
    level: LoggingLevel
    logger: str | None = None

class ModelHint(WireModel):
    model_config = ConfigDict(extra='ignore')
    name: str | None = None

class ModelPreferences(WireModel):
    model_config = ConfigDict(extra='ignore')
    cost_priority: Annotated[float | None, Field(alias='costPriority', ge=0.0, le=1.0)] = None
    hints: list[ModelHint] | None = None
    intelligence_priority: Annotated[float | None, Field(alias='intelligencePriority', ge=0.0, le=1.0)] = None
    speed_priority: Annotated[float | None, Field(alias='speedPriority', ge=0.0, le=1.0)] = None

class Notification(WireModel):
    model_config = ConfigDict(extra='ignore')
    method: str
    params: dict[str, Any] | None = None

class NotificationParams(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[dict[str, Any] | None, Field(alias='_meta')] = None

class NumberSchema(WireModel):
    model_config = ConfigDict(extra='ignore')
    default: int | float | None = None
    description: str | None = None
    maximum: int | float | None = None
    minimum: int | float | None = None
    title: str | None = None
    type: Literal['integer', 'number']

class PaginatedResult(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[dict[str, Any] | None, Field(alias='_meta')] = None
    next_cursor: Annotated[str | None, Field(alias='nextCursor')] = None
ProgressToken = str | int

class PromptArgument(WireModel):
    model_config = ConfigDict(extra='ignore')
    description: str | None = None
    name: str
    required: bool | None = None
    title: str | None = None

class PromptListChangedNotification(WireModel):
    model_config = ConfigDict(extra='ignore')
    jsonrpc: Literal['2.0']
    method: Literal['notifications/prompts/list_changed']
    params: NotificationParams | None = None

class PromptReference(WireModel):
    model_config = ConfigDict(extra='ignore')
    name: str
    title: str | None = None
    type: Literal['ref/prompt']

class Meta(WireModel):
    model_config = ConfigDict(extra='allow')
    progress_token: Annotated[ProgressToken | None, Field(alias='progressToken')] = None

class ReadResourceRequestParams(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[Meta | None, Field(alias='_meta')] = None
    uri: str

class RelatedTaskMetadata(WireModel):
    model_config = ConfigDict(extra='ignore')
    task_id: Annotated[str, Field(alias='taskId')]

class Request(WireModel):
    model_config = ConfigDict(extra='ignore')
    method: str
    params: dict[str, Any] | None = None
RequestId = str | int

class RequestParams(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[Meta | None, Field(alias='_meta')] = None

class ResourceContents(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[dict[str, Any] | None, Field(alias='_meta')] = None
    mime_type: Annotated[str | None, Field(alias='mimeType')] = None
    uri: str

class ResourceListChangedNotification(WireModel):
    model_config = ConfigDict(extra='ignore')
    jsonrpc: Literal['2.0']
    method: Literal['notifications/resources/list_changed']
    params: NotificationParams | None = None

class ResourceRequestParams(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[Meta | None, Field(alias='_meta')] = None
    uri: str

class ResourceTemplateReference(WireModel):
    model_config = ConfigDict(extra='ignore')
    type: Literal['ref/resource']
    uri: str

class ResourceUpdatedNotificationParams(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[dict[str, Any] | None, Field(alias='_meta')] = None
    uri: str

class Result(WireModel):
    model_config = ConfigDict(extra='allow')
    meta: Annotated[dict[str, Any] | None, Field(alias='_meta')] = None
Role = Literal['assistant', 'user']

class Root(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[dict[str, Any] | None, Field(alias='_meta')] = None
    name: str | None = None
    uri: str

class RootsListChangedNotification(WireModel):
    model_config = ConfigDict(extra='ignore')
    jsonrpc: Literal['2.0']
    method: Literal['notifications/roots/list_changed']
    params: NotificationParams | None = None

class Prompts(WireModel):
    model_config = ConfigDict(extra='ignore')
    list_changed: Annotated[bool | None, Field(alias='listChanged')] = None

class Resources(WireModel):
    model_config = ConfigDict(extra='ignore')
    list_changed: Annotated[bool | None, Field(alias='listChanged')] = None
    subscribe: bool | None = None

class Tools(WireModel):
    model_config = ConfigDict(extra='ignore')
    call: dict[str, Any] | None = None

class Requests1(WireModel):
    model_config = ConfigDict(extra='ignore')
    tools: Tools | None = None

class Tasks1(WireModel):
    model_config = ConfigDict(extra='ignore')
    cancel: dict[str, Any] | None = None
    list: dict[str, Any] | None = None
    requests: Requests1 | None = None

class Tools1(WireModel):
    model_config = ConfigDict(extra='ignore')
    list_changed: Annotated[bool | None, Field(alias='listChanged')] = None

class ServerCapabilities(WireModel):
    model_config = ConfigDict(extra='ignore')
    completions: dict[str, Any] | None = None
    experimental: dict[str, dict[str, Any]] | None = None
    logging: dict[str, Any] | None = None
    prompts: Prompts | None = None
    resources: Resources | None = None
    tasks: Tasks1 | None = None
    tools: Tools1 | None = None

class SetLevelRequestParams(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[Meta | None, Field(alias='_meta')] = None
    level: LoggingLevel

class StringSchema(WireModel):
    model_config = ConfigDict(extra='ignore')
    default: str | None = None
    description: str | None = None
    format: Literal['date', 'date-time', 'email', 'uri'] | None = None
    max_length: Annotated[int | None, Field(alias='maxLength')] = None
    min_length: Annotated[int | None, Field(alias='minLength')] = None
    title: str | None = None
    type: Literal['string']

class SubscribeRequestParams(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[Meta | None, Field(alias='_meta')] = None
    uri: str

class TaskMetadata(WireModel):
    model_config = ConfigDict(extra='ignore')
    ttl: int | None = None
TaskStatus = Literal['cancelled', 'completed', 'failed', 'input_required', 'working']

class TextResourceContents(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[dict[str, Any] | None, Field(alias='_meta')] = None
    mime_type: Annotated[str | None, Field(alias='mimeType')] = None
    text: str
    uri: str

class AnyOfItem(WireModel):
    model_config = ConfigDict(extra='ignore')
    const: str
    title: str

class Items(WireModel):
    model_config = ConfigDict(extra='ignore')
    any_of: Annotated[list[AnyOfItem], Field(alias='anyOf')]

class TitledMultiSelectEnumSchema(WireModel):
    model_config = ConfigDict(extra='ignore')
    default: list[str] | None = None
    description: str | None = None
    items: Items
    max_items: Annotated[int | None, Field(alias='maxItems')] = None
    min_items: Annotated[int | None, Field(alias='minItems')] = None
    title: str | None = None
    type: Literal['array']

class OneOfItem(WireModel):
    model_config = ConfigDict(extra='ignore')
    const: str
    title: str

class TitledSingleSelectEnumSchema(WireModel):
    model_config = ConfigDict(extra='ignore')
    default: str | None = None
    description: str | None = None
    one_of: Annotated[list[OneOfItem], Field(alias='oneOf')]
    title: str | None = None
    type: Literal['string']

class InputSchema(WireModel):
    model_config = ConfigDict(extra='allow')
    schema_: Annotated[str | None, Field(alias='$schema')] = None
    properties: dict[str, dict[str, Any] | bool] | None = None
    required: list[str] | None = None
    type: Literal['object']

class OutputSchema(WireModel):
    model_config = ConfigDict(extra='allow')
    schema_: Annotated[str | None, Field(alias='$schema')] = None
    properties: dict[str, dict[str, Any] | bool] | None = None
    required: list[str] | None = None
    type: Literal['object']

class ToolAnnotations(WireModel):
    model_config = ConfigDict(extra='ignore')
    destructive_hint: Annotated[bool | None, Field(alias='destructiveHint')] = None
    idempotent_hint: Annotated[bool | None, Field(alias='idempotentHint')] = None
    open_world_hint: Annotated[bool | None, Field(alias='openWorldHint')] = None
    read_only_hint: Annotated[bool | None, Field(alias='readOnlyHint')] = None
    title: str | None = None

class ToolChoice(WireModel):
    model_config = ConfigDict(extra='ignore')
    mode: Literal['auto', 'none', 'required'] | None = None

class ToolExecution(WireModel):
    model_config = ConfigDict(extra='ignore')
    task_support: Annotated[Literal['forbidden', 'optional', 'required'] | None, Field(alias='taskSupport')] = None

class ToolListChangedNotification(WireModel):
    model_config = ConfigDict(extra='ignore')
    jsonrpc: Literal['2.0']
    method: Literal['notifications/tools/list_changed']
    params: NotificationParams | None = None

class ToolUseContent(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[dict[str, Any] | None, Field(alias='_meta')] = None
    id: str
    input: dict[str, Any]
    name: str
    type: Literal['tool_use']

class UnsubscribeRequestParams(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[Meta | None, Field(alias='_meta')] = None
    uri: str

class Items1(WireModel):
    model_config = ConfigDict(extra='ignore')
    enum: list[str]
    type: Literal['string']

class UntitledMultiSelectEnumSchema(WireModel):
    model_config = ConfigDict(extra='ignore')
    default: list[str] | None = None
    description: str | None = None
    items: Items1
    max_items: Annotated[int | None, Field(alias='maxItems')] = None
    min_items: Annotated[int | None, Field(alias='minItems')] = None
    title: str | None = None
    type: Literal['array']

class UntitledSingleSelectEnumSchema(WireModel):
    model_config = ConfigDict(extra='ignore')
    default: str | None = None
    description: str | None = None
    enum: list[str]
    title: str | None = None
    type: Literal['string']

class Annotations(WireModel):
    model_config = ConfigDict(extra='ignore')
    audience: list[Role] | None = None
    last_modified: Annotated[str | None, Field(alias='lastModified')] = None
    priority: Annotated[float | None, Field(ge=0.0, le=1.0)] = None

class AudioContent(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[dict[str, Any] | None, Field(alias='_meta')] = None
    annotations: Annotations | None = None
    data: str
    mime_type: Annotated[str, Field(alias='mimeType')]
    type: Literal['audio']

class CallToolRequestParams(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[Meta | None, Field(alias='_meta')] = None
    arguments: dict[str, Any] | None = None
    name: str
    task: TaskMetadata | None = None

class CancelTaskRequest(WireModel):
    model_config = ConfigDict(extra='ignore')
    id: RequestId
    jsonrpc: Literal['2.0']
    method: Literal['tasks/cancel']
    params: Params

class CancelledNotificationParams(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[dict[str, Any] | None, Field(alias='_meta')] = None
    reason: str | None = None
    request_id: Annotated[RequestId | None, Field(alias='requestId')] = None

class CompleteRequestParams(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[Meta | None, Field(alias='_meta')] = None
    argument: Argument
    context: Context | None = None
    ref: PromptReference | ResourceTemplateReference

class ElicitRequestFormParams(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[Meta | None, Field(alias='_meta')] = None
    message: str
    mode: Literal['form'] = 'form'
    requested_schema: Annotated[RequestedSchema, Field(alias='requestedSchema')]
    task: TaskMetadata | None = None

class ElicitRequestURLParams(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[Meta | None, Field(alias='_meta')] = None
    elicitation_id: Annotated[str, Field(alias='elicitationId')]
    message: str
    mode: Literal['url']
    task: TaskMetadata | None = None
    url: str

class EmbeddedResource(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[dict[str, Any] | None, Field(alias='_meta')] = None
    annotations: Annotations | None = None
    resource: TextResourceContents | BlobResourceContents
    type: Literal['resource']
EmptyResult = Result
EnumSchema = UntitledSingleSelectEnumSchema | TitledSingleSelectEnumSchema | UntitledMultiSelectEnumSchema | TitledMultiSelectEnumSchema | LegacyTitledEnumSchema

class GetPromptRequestParams(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[Meta | None, Field(alias='_meta')] = None
    arguments: dict[str, str] | None = None
    name: str

class GetTaskPayloadRequest(WireModel):
    model_config = ConfigDict(extra='ignore')
    id: RequestId
    jsonrpc: Literal['2.0']
    method: Literal['tasks/result']
    params: Params2

class GetTaskRequest(WireModel):
    model_config = ConfigDict(extra='ignore')
    id: RequestId
    jsonrpc: Literal['2.0']
    method: Literal['tasks/get']
    params: Params3

class ImageContent(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[dict[str, Any] | None, Field(alias='_meta')] = None
    annotations: Annotations | None = None
    data: str
    mime_type: Annotated[str, Field(alias='mimeType')]
    type: Literal['image']

class InitializeRequestParams(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[Meta | None, Field(alias='_meta')] = None
    capabilities: ClientCapabilities
    client_info: Annotated[Implementation, Field(alias='clientInfo')]
    protocol_version: Annotated[str, Field(alias='protocolVersion')]

class InitializeResult(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[dict[str, Any] | None, Field(alias='_meta')] = None
    capabilities: ServerCapabilities
    instructions: str | None = None
    protocol_version: Annotated[str, Field(alias='protocolVersion')]
    server_info: Annotated[Implementation, Field(alias='serverInfo')]

class InitializedNotification(WireModel):
    model_config = ConfigDict(extra='ignore')
    jsonrpc: Literal['2.0']
    method: Literal['notifications/initialized']
    params: NotificationParams | None = None

class JSONRPCErrorResponse(WireModel):
    model_config = ConfigDict(extra='ignore')
    error: Error
    id: RequestId | None = None
    jsonrpc: Literal['2.0']

class JSONRPCRequest(WireModel):
    model_config = ConfigDict(extra='ignore')
    id: RequestId
    jsonrpc: Literal['2.0']
    method: str
    params: dict[str, Any] | None = None

class JSONRPCResultResponse(WireModel):
    model_config = ConfigDict(extra='ignore')
    id: RequestId
    jsonrpc: Literal['2.0']
    result: Result

class ListRootsRequest(WireModel):
    model_config = ConfigDict(extra='ignore')
    id: RequestId
    jsonrpc: Literal['2.0']
    method: Literal['roots/list']
    params: RequestParams | None = None

class ListRootsResult(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[dict[str, Any] | None, Field(alias='_meta')] = None
    roots: list[Root]

class LoggingMessageNotification(WireModel):
    model_config = ConfigDict(extra='ignore')
    jsonrpc: Literal['2.0']
    method: Literal['notifications/message']
    params: LoggingMessageNotificationParams
MultiSelectEnumSchema = UntitledMultiSelectEnumSchema | TitledMultiSelectEnumSchema

class PaginatedRequestParams(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[Meta | None, Field(alias='_meta')] = None
    cursor: str | None = None

class PingRequest(WireModel):
    model_config = ConfigDict(extra='ignore')
    id: RequestId
    jsonrpc: Literal['2.0']
    method: Literal['ping']
    params: RequestParams | None = None
PrimitiveSchemaDefinition = StringSchema | NumberSchema | BooleanSchema | UntitledSingleSelectEnumSchema | TitledSingleSelectEnumSchema | UntitledMultiSelectEnumSchema | TitledMultiSelectEnumSchema | LegacyTitledEnumSchema

class ProgressNotificationParams(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[dict[str, Any] | None, Field(alias='_meta')] = None
    message: str | None = None
    progress: float
    progress_token: Annotated[ProgressToken, Field(alias='progressToken')]
    total: float | None = None

class Prompt(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[dict[str, Any] | None, Field(alias='_meta')] = None
    arguments: list[PromptArgument] | None = None
    description: str | None = None
    icons: list[Icon] | None = None
    name: str
    title: str | None = None

class ReadResourceRequest(WireModel):
    model_config = ConfigDict(extra='ignore')
    id: RequestId
    jsonrpc: Literal['2.0']
    method: Literal['resources/read']
    params: ReadResourceRequestParams

class ReadResourceResult(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[dict[str, Any] | None, Field(alias='_meta')] = None
    contents: list[TextResourceContents | BlobResourceContents]

class Resource(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[dict[str, Any] | None, Field(alias='_meta')] = None
    annotations: Annotations | None = None
    description: str | None = None
    icons: list[Icon] | None = None
    mime_type: Annotated[str | None, Field(alias='mimeType')] = None
    name: str
    size: int | None = None
    title: str | None = None
    uri: str

class ResourceLink(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[dict[str, Any] | None, Field(alias='_meta')] = None
    annotations: Annotations | None = None
    description: str | None = None
    icons: list[Icon] | None = None
    mime_type: Annotated[str | None, Field(alias='mimeType')] = None
    name: str
    size: int | None = None
    title: str | None = None
    type: Literal['resource_link']
    uri: str

class ResourceTemplate(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[dict[str, Any] | None, Field(alias='_meta')] = None
    annotations: Annotations | None = None
    description: str | None = None
    icons: list[Icon] | None = None
    mime_type: Annotated[str | None, Field(alias='mimeType')] = None
    name: str
    title: str | None = None
    uri_template: Annotated[str, Field(alias='uriTemplate')]

class ResourceUpdatedNotification(WireModel):
    model_config = ConfigDict(extra='ignore')
    jsonrpc: Literal['2.0']
    method: Literal['notifications/resources/updated']
    params: ResourceUpdatedNotificationParams

class SetLevelRequest(WireModel):
    model_config = ConfigDict(extra='ignore')
    id: RequestId
    jsonrpc: Literal['2.0']
    method: Literal['logging/setLevel']
    params: SetLevelRequestParams
SingleSelectEnumSchema = UntitledSingleSelectEnumSchema | TitledSingleSelectEnumSchema

class SubscribeRequest(WireModel):
    model_config = ConfigDict(extra='ignore')
    id: RequestId
    jsonrpc: Literal['2.0']
    method: Literal['resources/subscribe']
    params: SubscribeRequestParams

class Task(WireModel):
    model_config = ConfigDict(extra='ignore')
    created_at: Annotated[str, Field(alias='createdAt')]
    last_updated_at: Annotated[str, Field(alias='lastUpdatedAt')]
    poll_interval: Annotated[int | None, Field(alias='pollInterval')] = None
    status: TaskStatus
    status_message: Annotated[str | None, Field(alias='statusMessage')] = None
    task_id: Annotated[str, Field(alias='taskId')]
    ttl: int | None

class TaskAugmentedRequestParams(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[Meta | None, Field(alias='_meta')] = None
    task: TaskMetadata | None = None

class TaskStatusNotificationParams(NotificationParams, Task):
    model_config = ConfigDict(extra='ignore')

class TextContent(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[dict[str, Any] | None, Field(alias='_meta')] = None
    annotations: Annotations | None = None
    text: str
    type: Literal['text']

class Tool(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[dict[str, Any] | None, Field(alias='_meta')] = None
    annotations: ToolAnnotations | None = None
    description: str | None = None
    execution: ToolExecution | None = None
    icons: list[Icon] | None = None
    input_schema: Annotated[InputSchema, Field(alias='inputSchema')]
    name: str
    output_schema: Annotated[OutputSchema | None, Field(alias='outputSchema')] = None
    title: str | None = None

class Data(WireModel):
    model_config = ConfigDict(extra='allow')
    elicitations: list[ElicitRequestURLParams]

class Error1(Error):
    model_config = ConfigDict(extra='ignore')
    code: Literal[-32042]
    data: Data

class URLElicitationRequiredError(WireModel):
    model_config = ConfigDict(extra='ignore')
    error: Error1
    id: RequestId | None = None
    jsonrpc: Literal['2.0']

class UnsubscribeRequest(WireModel):
    model_config = ConfigDict(extra='ignore')
    id: RequestId
    jsonrpc: Literal['2.0']
    method: Literal['resources/unsubscribe']
    params: UnsubscribeRequestParams

class CallToolRequest(WireModel):
    model_config = ConfigDict(extra='ignore')
    id: RequestId
    jsonrpc: Literal['2.0']
    method: Literal['tools/call']
    params: CallToolRequestParams

class CancelTaskResult(Result, Task):
    model_config = ConfigDict(extra='ignore')

class CancelledNotification(WireModel):
    model_config = ConfigDict(extra='ignore')
    jsonrpc: Literal['2.0']
    method: Literal['notifications/cancelled']
    params: CancelledNotificationParams

class CompleteRequest(WireModel):
    model_config = ConfigDict(extra='ignore')
    id: RequestId
    jsonrpc: Literal['2.0']
    method: Literal['completion/complete']
    params: CompleteRequestParams
ContentBlock = TextContent | ImageContent | AudioContent | ResourceLink | EmbeddedResource

class CreateTaskResult(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[dict[str, Any] | None, Field(alias='_meta')] = None
    task: Task
ElicitRequestParams = ElicitRequestURLParams | ElicitRequestFormParams

class GetPromptRequest(WireModel):
    model_config = ConfigDict(extra='ignore')
    id: RequestId
    jsonrpc: Literal['2.0']
    method: Literal['prompts/get']
    params: GetPromptRequestParams

class GetTaskResult(Result, Task):
    model_config = ConfigDict(extra='ignore')

class InitializeRequest(WireModel):
    model_config = ConfigDict(extra='ignore')
    id: RequestId
    jsonrpc: Literal['2.0']
    method: Literal['initialize']
    params: InitializeRequestParams
JSONRPCMessage = JSONRPCRequest | JSONRPCNotification | JSONRPCResultResponse | JSONRPCErrorResponse
JSONRPCResponse = JSONRPCResultResponse | JSONRPCErrorResponse

class ListPromptsRequest(WireModel):
    model_config = ConfigDict(extra='ignore')
    id: RequestId
    jsonrpc: Literal['2.0']
    method: Literal['prompts/list']
    params: PaginatedRequestParams | None = None

class ListPromptsResult(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[dict[str, Any] | None, Field(alias='_meta')] = None
    next_cursor: Annotated[str | None, Field(alias='nextCursor')] = None
    prompts: list[Prompt]

class ListResourceTemplatesRequest(WireModel):
    model_config = ConfigDict(extra='ignore')
    id: RequestId
    jsonrpc: Literal['2.0']
    method: Literal['resources/templates/list']
    params: PaginatedRequestParams | None = None

class ListResourceTemplatesResult(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[dict[str, Any] | None, Field(alias='_meta')] = None
    next_cursor: Annotated[str | None, Field(alias='nextCursor')] = None
    resource_templates: Annotated[list[ResourceTemplate], Field(alias='resourceTemplates')]

class ListResourcesRequest(WireModel):
    model_config = ConfigDict(extra='ignore')
    id: RequestId
    jsonrpc: Literal['2.0']
    method: Literal['resources/list']
    params: PaginatedRequestParams | None = None

class ListResourcesResult(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[dict[str, Any] | None, Field(alias='_meta')] = None
    next_cursor: Annotated[str | None, Field(alias='nextCursor')] = None
    resources: list[Resource]

class ListTasksRequest(WireModel):
    model_config = ConfigDict(extra='ignore')
    id: RequestId
    jsonrpc: Literal['2.0']
    method: Literal['tasks/list']
    params: PaginatedRequestParams | None = None

class ListTasksResult(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[dict[str, Any] | None, Field(alias='_meta')] = None
    next_cursor: Annotated[str | None, Field(alias='nextCursor')] = None
    tasks: list[Task]

class ListToolsRequest(WireModel):
    model_config = ConfigDict(extra='ignore')
    id: RequestId
    jsonrpc: Literal['2.0']
    method: Literal['tools/list']
    params: PaginatedRequestParams | None = None

class ListToolsResult(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[dict[str, Any] | None, Field(alias='_meta')] = None
    next_cursor: Annotated[str | None, Field(alias='nextCursor')] = None
    tools: list[Tool]

class PaginatedRequest(WireModel):
    model_config = ConfigDict(extra='ignore')
    id: RequestId
    jsonrpc: Literal['2.0']
    method: str
    params: PaginatedRequestParams | None = None

class ProgressNotification(WireModel):
    model_config = ConfigDict(extra='ignore')
    jsonrpc: Literal['2.0']
    method: Literal['notifications/progress']
    params: ProgressNotificationParams

class PromptMessage(WireModel):
    model_config = ConfigDict(extra='ignore')
    content: ContentBlock
    role: Role

class TaskStatusNotification(WireModel):
    model_config = ConfigDict(extra='ignore')
    jsonrpc: Literal['2.0']
    method: Literal['notifications/tasks/status']
    params: TaskStatusNotificationParams

class ToolResultContent(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[dict[str, Any] | None, Field(alias='_meta')] = None
    content: list[ContentBlock]
    is_error: Annotated[bool | None, Field(alias='isError')] = None
    structured_content: Annotated[dict[str, Any] | None, Field(alias='structuredContent')] = None
    tool_use_id: Annotated[str, Field(alias='toolUseId')]
    type: Literal['tool_result']

class CallToolResult(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[dict[str, Any] | None, Field(alias='_meta')] = None
    content: list[ContentBlock]
    is_error: Annotated[bool | None, Field(alias='isError')] = None
    structured_content: Annotated[dict[str, Any] | None, Field(alias='structuredContent')] = None
ClientNotification = CancelledNotification | InitializedNotification | ProgressNotification | TaskStatusNotification | RootsListChangedNotification
ClientRequest = InitializeRequest | PingRequest | ListResourcesRequest | ListResourceTemplatesRequest | ReadResourceRequest | SubscribeRequest | UnsubscribeRequest | ListPromptsRequest | GetPromptRequest | ListToolsRequest | CallToolRequest | GetTaskRequest | GetTaskPayloadRequest | CancelTaskRequest | ListTasksRequest | SetLevelRequest | CompleteRequest

class ElicitRequest(WireModel):
    model_config = ConfigDict(extra='ignore')
    id: RequestId
    jsonrpc: Literal['2.0']
    method: Literal['elicitation/create']
    params: ElicitRequestParams

class GetPromptResult(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[dict[str, Any] | None, Field(alias='_meta')] = None
    description: str | None = None
    messages: list[PromptMessage]
SamplingMessageContentBlock = TextContent | ImageContent | AudioContent | ToolUseContent | ToolResultContent
ServerNotification = CancelledNotification | ProgressNotification | ResourceListChangedNotification | ResourceUpdatedNotification | PromptListChangedNotification | ToolListChangedNotification | TaskStatusNotification | LoggingMessageNotification | ElicitationCompleteNotification
ServerResult = Result | InitializeResult | ListResourcesResult | ListResourceTemplatesResult | ReadResourceResult | ListPromptsResult | GetPromptResult | ListToolsResult | CallToolResult | GetTaskResult | GetTaskPayloadResult | CancelTaskResult | ListTasksResult | CompleteResult

class CreateMessageResult(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[dict[str, Any] | None, Field(alias='_meta')] = None
    content: TextContent | ImageContent | AudioContent | ToolUseContent | ToolResultContent | list[SamplingMessageContentBlock]
    model: str
    role: Role
    stop_reason: Annotated[str | None, Field(alias='stopReason')] = None

class SamplingMessage(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[dict[str, Any] | None, Field(alias='_meta')] = None
    content: TextContent | ImageContent | AudioContent | ToolUseContent | ToolResultContent | list[SamplingMessageContentBlock]
    role: Role
ClientResult = Result | GetTaskResult | GetTaskPayloadResult | CancelTaskResult | ListTasksResult | CreateMessageResult | ListRootsResult | ElicitResult

class CreateMessageRequestParams(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[Meta | None, Field(alias='_meta')] = None
    include_context: Annotated[Literal['allServers', 'none', 'thisServer'] | None, Field(alias='includeContext')] = None
    max_tokens: Annotated[int, Field(alias='maxTokens')]
    messages: list[SamplingMessage]
    metadata: dict[str, Any] | None = None
    model_preferences: Annotated[ModelPreferences | None, Field(alias='modelPreferences')] = None
    stop_sequences: Annotated[list[str] | None, Field(alias='stopSequences')] = None
    system_prompt: Annotated[str | None, Field(alias='systemPrompt')] = None
    task: TaskMetadata | None = None
    temperature: float | None = None
    tool_choice: Annotated[ToolChoice | None, Field(alias='toolChoice')] = None
    tools: list[Tool] | None = None

class CreateMessageRequest(WireModel):
    model_config = ConfigDict(extra='ignore')
    id: RequestId
    jsonrpc: Literal['2.0']
    method: Literal['sampling/createMessage']
    params: CreateMessageRequestParams
ServerRequest = PingRequest | GetTaskRequest | GetTaskPayloadRequest | CancelTaskRequest | ListTasksRequest | CreateMessageRequest | ListRootsRequest | ElicitRequest
