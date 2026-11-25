# Frozen from MCP 2.3.0; see corpus README.md and LICENSE.
from __future__ import annotations
from typing import Annotated, Any, Literal, Union
from mcp_types._wire_base import WireModel
from pydantic import ConfigDict, Field
from typing_extensions import TypeAliasType

class BaseMetadata(WireModel):
    model_config = ConfigDict(extra='ignore')
    name: str
    title: str | None = None

class BooleanSchema(WireModel):
    model_config = ConfigDict(extra='ignore')
    default: bool | None = None
    description: str | None = None
    title: str | None = None
    type: Literal['boolean']

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
    values: Annotated[list[str], Field(max_length=100)]
Cursor = str

class RequestedSchema(WireModel):
    model_config = ConfigDict(extra='ignore')
    schema_: Annotated[str | None, Field(alias='$schema')] = None
    properties: dict[str, Any]
    required: list[str] | None = None
    type: Literal['object']

class ElicitRequestFormParams(WireModel):
    model_config = ConfigDict(extra='ignore')
    message: str
    mode: Literal['form'] = 'form'
    requested_schema: Annotated[RequestedSchema, Field(alias='requestedSchema')]

class ElicitRequestURLParams(WireModel):
    model_config = ConfigDict(extra='ignore')
    message: str
    mode: Literal['url']
    url: str

class ElicitResult(WireModel):
    model_config = ConfigDict(extra='ignore')
    action: Literal['accept', 'cancel', 'decline']
    content: dict[str, list[str] | str | int | float | bool | None] | None = None

class Error(WireModel):
    model_config = ConfigDict(extra='ignore')
    code: int
    data: Any | None = None
    message: str

class Error1(Error):
    model_config = ConfigDict(extra='ignore')
    code: Literal[-32020]

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

class InternalError(WireModel):
    model_config = ConfigDict(extra='ignore')
    code: Literal[-32603]
    data: Any | None = None
    message: str

class InvalidParamsError(WireModel):
    model_config = ConfigDict(extra='ignore')
    code: Literal[-32602]
    data: Any | None = None
    message: str

class InvalidRequestError(WireModel):
    model_config = ConfigDict(extra='ignore')
    code: Literal[-32600]
    data: Any | None = None
    message: str

class JSONRPCNotification(WireModel):
    model_config = ConfigDict(extra='ignore')
    jsonrpc: Literal['2.0']
    method: str
    params: dict[str, Any] | None = None
JSONValue = TypeAliasType('JSONValue', Union[dict[str, 'JSONValue'], list['JSONValue'], str | int | float | bool | None])

class LegacyTitledEnumSchema(WireModel):
    model_config = ConfigDict(extra='ignore')
    default: str | None = None
    description: str | None = None
    enum: list[str]
    enum_names: Annotated[list[str] | None, Field(alias='enumNames')] = None
    title: str | None = None
    type: Literal['string']
LoggingLevel = Literal['alert', 'critical', 'debug', 'emergency', 'error', 'info', 'notice', 'warning']

class MetaObject(WireModel):
    model_config = ConfigDict(extra='allow')

class MethodNotFoundError(WireModel):
    model_config = ConfigDict(extra='ignore')
    code: Literal[-32601]
    data: Any | None = None
    message: str

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

class NumberSchema(WireModel):
    model_config = ConfigDict(extra='ignore')
    default: int | float | None = None
    description: str | None = None
    maximum: int | float | None = None
    minimum: int | float | None = None
    title: str | None = None
    type: Literal['integer', 'number']

class ParseError(WireModel):
    model_config = ConfigDict(extra='ignore')
    code: Literal[-32700]
    data: Any | None = None
    message: str
ProgressToken = str | int

class PromptArgument(WireModel):
    model_config = ConfigDict(extra='ignore')
    description: str | None = None
    name: str
    required: bool | None = None
    title: str | None = None

class PromptReference(WireModel):
    model_config = ConfigDict(extra='ignore')
    name: str
    title: str | None = None
    type: Literal['ref/prompt']

class Request(WireModel):
    model_config = ConfigDict(extra='ignore')
    method: str
    params: dict[str, Any] | None = None
RequestId = str | int

class ResourceContents(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[MetaObject | None, Field(alias='_meta')] = None
    mime_type: Annotated[str | None, Field(alias='mimeType')] = None
    uri: str

class ResourceTemplateReference(WireModel):
    model_config = ConfigDict(extra='ignore')
    type: Literal['ref/resource']
    uri: str

class ResultMetaObject(WireModel):
    model_config = ConfigDict(extra='allow')
    io_modelcontextprotocol_server_info: Annotated[Any | None, Field(alias='io.modelcontextprotocol/serverInfo')] = None
ResultType = str
Role = Literal['assistant', 'user']

class Root(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[MetaObject | None, Field(alias='_meta')] = None
    name: str | None = None
    uri: str

class Prompts(WireModel):
    model_config = ConfigDict(extra='ignore')
    list_changed: Annotated[bool | None, Field(alias='listChanged')] = None

class Resources(WireModel):
    model_config = ConfigDict(extra='ignore')
    list_changed: Annotated[bool | None, Field(alias='listChanged')] = None
    subscribe: bool | None = None

class Tools(WireModel):
    model_config = ConfigDict(extra='ignore')
    list_changed: Annotated[bool | None, Field(alias='listChanged')] = None

class StringSchema(WireModel):
    model_config = ConfigDict(extra='ignore')
    default: str | None = None
    description: str | None = None
    format: Literal['date', 'date-time', 'email', 'uri'] | None = None
    max_length: Annotated[int | None, Field(alias='maxLength')] = None
    min_length: Annotated[int | None, Field(alias='minLength')] = None
    title: str | None = None
    type: Literal['string']

class SubscriptionFilter(WireModel):
    model_config = ConfigDict(extra='ignore')
    prompts_list_changed: Annotated[bool | None, Field(alias='promptsListChanged')] = None
    resource_subscriptions: Annotated[list[str] | None, Field(alias='resourceSubscriptions')] = None
    resources_list_changed: Annotated[bool | None, Field(alias='resourcesListChanged')] = None
    tools_list_changed: Annotated[bool | None, Field(alias='toolsListChanged')] = None

class SubscriptionsListenResultMeta(WireModel):
    model_config = ConfigDict(extra='allow')
    io_modelcontextprotocol_server_info: Annotated[Any | None, Field(alias='io.modelcontextprotocol/serverInfo')] = None
    io_modelcontextprotocol_subscription_id: Annotated[RequestId, Field(alias='io.modelcontextprotocol/subscriptionId')]

class TextResourceContents(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[MetaObject | None, Field(alias='_meta')] = None
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
    type: Literal['object']

class OutputSchema(WireModel):
    model_config = ConfigDict(extra='allow')
    schema_: Annotated[str | None, Field(alias='$schema')] = None

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

class ToolUseContent(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[MetaObject | None, Field(alias='_meta')] = None
    id: str
    input: dict[str, Any]
    name: str
    type: Literal['tool_use']

class Data1(WireModel):
    model_config = ConfigDict(extra='ignore')
    requested: str
    supported: list[str]

class Error3(Error):
    model_config = ConfigDict(extra='ignore')
    code: Literal[-32022]
    data: Data1

class UnsupportedProtocolVersionError(WireModel):
    model_config = ConfigDict(extra='ignore')
    error: Error3
    id: RequestId | None = None
    jsonrpc: Literal['2.0']

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
    meta: Annotated[MetaObject | None, Field(alias='_meta')] = None
    annotations: Annotations | None = None
    data: str
    mime_type: Annotated[str, Field(alias='mimeType')]
    type: Literal['audio']

class BlobResourceContents(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[MetaObject | None, Field(alias='_meta')] = None
    blob: str
    mime_type: Annotated[str | None, Field(alias='mimeType')] = None
    uri: str

class CacheableResult(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[ResultMetaObject | None, Field(alias='_meta')] = None
    cache_scope: Annotated[Literal['private', 'public'], Field(alias='cacheScope')]
    result_type: Annotated[str, Field(alias='resultType')]
    ttl_ms: Annotated[int, Field(alias='ttlMs', ge=0)]

class CompleteResult(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[ResultMetaObject | None, Field(alias='_meta')] = None
    completion: Completion
    result_type: Annotated[str, Field(alias='resultType')]

class CompleteResultResponse(WireModel):
    model_config = ConfigDict(extra='ignore')
    id: RequestId
    jsonrpc: Literal['2.0']
    result: CompleteResult
ElicitRequestParams = ElicitRequestFormParams | ElicitRequestURLParams

class EmbeddedResource(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[MetaObject | None, Field(alias='_meta')] = None
    annotations: Annotations | None = None
    resource: TextResourceContents | BlobResourceContents
    type: Literal['resource']
EnumSchema = UntitledSingleSelectEnumSchema | TitledSingleSelectEnumSchema | UntitledMultiSelectEnumSchema | TitledMultiSelectEnumSchema | LegacyTitledEnumSchema

class HeaderMismatchError(WireModel):
    model_config = ConfigDict(extra='ignore')
    error: Error1
    id: RequestId | None = None
    jsonrpc: Literal['2.0']

class ImageContent(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[MetaObject | None, Field(alias='_meta')] = None
    annotations: Annotations | None = None
    data: str
    mime_type: Annotated[str, Field(alias='mimeType')]
    type: Literal['image']
JSONArray = list[JSONValue]
JSONObject = dict[str, JSONValue]

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

class Params(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[MetaObject | None, Field(alias='_meta')] = None

class ListRootsRequest(WireModel):
    model_config = ConfigDict(extra='ignore')
    method: Literal['roots/list']
    params: Params | None = None

class ListRootsResult(WireModel):
    model_config = ConfigDict(extra='ignore')
    roots: list[Root]
MultiSelectEnumSchema = UntitledMultiSelectEnumSchema | TitledMultiSelectEnumSchema

class NotificationMetaObject(WireModel):
    model_config = ConfigDict(extra='allow')
    io_modelcontextprotocol_subscription_id: Annotated[RequestId | None, Field(alias='io.modelcontextprotocol/subscriptionId')] = None

class NotificationParams(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[NotificationMetaObject | None, Field(alias='_meta')] = None

class PaginatedResult(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[ResultMetaObject | None, Field(alias='_meta')] = None
    next_cursor: Annotated[str | None, Field(alias='nextCursor')] = None
    result_type: Annotated[str, Field(alias='resultType')]
PrimitiveSchemaDefinition = StringSchema | NumberSchema | BooleanSchema | UntitledSingleSelectEnumSchema | TitledSingleSelectEnumSchema | UntitledMultiSelectEnumSchema | TitledMultiSelectEnumSchema | LegacyTitledEnumSchema

class ProgressNotificationParams(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[NotificationMetaObject | None, Field(alias='_meta')] = None
    message: str | None = None
    progress: float
    progress_token: Annotated[ProgressToken, Field(alias='progressToken')]
    total: float | None = None

class Prompt(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[MetaObject | None, Field(alias='_meta')] = None
    arguments: list[PromptArgument] | None = None
    description: str | None = None
    icons: list[Icon] | None = None
    name: str
    title: str | None = None

class PromptListChangedNotification(WireModel):
    model_config = ConfigDict(extra='ignore')
    jsonrpc: Literal['2.0']
    method: Literal['notifications/prompts/list_changed']
    params: NotificationParams | None = None

class ReadResourceResult(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[ResultMetaObject | None, Field(alias='_meta')] = None
    cache_scope: Annotated[Literal['private', 'public'], Field(alias='cacheScope')]
    contents: list[TextResourceContents | BlobResourceContents]
    result_type: Annotated[str, Field(alias='resultType')]
    ttl_ms: Annotated[int, Field(alias='ttlMs', ge=0)]

class Resource(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[MetaObject | None, Field(alias='_meta')] = None
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
    meta: Annotated[MetaObject | None, Field(alias='_meta')] = None
    annotations: Annotations | None = None
    description: str | None = None
    icons: list[Icon] | None = None
    mime_type: Annotated[str | None, Field(alias='mimeType')] = None
    name: str
    size: int | None = None
    title: str | None = None
    type: Literal['resource_link']
    uri: str

class ResourceListChangedNotification(WireModel):
    model_config = ConfigDict(extra='ignore')
    jsonrpc: Literal['2.0']
    method: Literal['notifications/resources/list_changed']
    params: NotificationParams | None = None

class ResourceTemplate(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[MetaObject | None, Field(alias='_meta')] = None
    annotations: Annotations | None = None
    description: str | None = None
    icons: list[Icon] | None = None
    mime_type: Annotated[str | None, Field(alias='mimeType')] = None
    name: str
    title: str | None = None
    uri_template: Annotated[str, Field(alias='uriTemplate')]

class ResourceUpdatedNotificationParams(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[NotificationMetaObject | None, Field(alias='_meta')] = None
    uri: str

class Result(WireModel):
    model_config = ConfigDict(extra='allow')
    meta: Annotated[ResultMetaObject | None, Field(alias='_meta')] = None
    result_type: Annotated[str, Field(alias='resultType')]

class ServerCapabilities(WireModel):
    model_config = ConfigDict(extra='ignore')
    completions: JSONObject | None = None
    experimental: dict[str, JSONObject] | None = None
    extensions: dict[str, JSONObject] | None = None
    logging: JSONObject | None = None
    prompts: Prompts | None = None
    resources: Resources | None = None
    tools: Tools | None = None
SingleSelectEnumSchema = UntitledSingleSelectEnumSchema | TitledSingleSelectEnumSchema

class SubscriptionsAcknowledgedNotificationParams(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[NotificationMetaObject | None, Field(alias='_meta')] = None
    notifications: SubscriptionFilter

class SubscriptionsListenResult(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[SubscriptionsListenResultMeta, Field(alias='_meta')]
    result_type: Annotated[str, Field(alias='resultType')]

class TextContent(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[MetaObject | None, Field(alias='_meta')] = None
    annotations: Annotations | None = None
    text: str
    type: Literal['text']

class Tool(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[MetaObject | None, Field(alias='_meta')] = None
    annotations: ToolAnnotations | None = None
    description: str | None = None
    icons: list[Icon] | None = None
    input_schema: Annotated[InputSchema, Field(alias='inputSchema')]
    name: str
    output_schema: Annotated[OutputSchema | None, Field(alias='outputSchema')] = None
    title: str | None = None

class ToolListChangedNotification(WireModel):
    model_config = ConfigDict(extra='ignore')
    jsonrpc: Literal['2.0']
    method: Literal['notifications/tools/list_changed']
    params: NotificationParams | None = None

class CancelledNotificationParams(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[NotificationMetaObject | None, Field(alias='_meta')] = None
    reason: str | None = None
    request_id: Annotated[RequestId, Field(alias='requestId')]

class Elicitation(WireModel):
    model_config = ConfigDict(extra='ignore')
    form: JSONObject | None = None
    url: JSONObject | None = None

class Sampling(WireModel):
    model_config = ConfigDict(extra='ignore')
    context: JSONObject | None = None
    tools: JSONObject | None = None

class ClientCapabilities(WireModel):
    model_config = ConfigDict(extra='ignore')
    elicitation: Elicitation | None = None
    experimental: dict[str, JSONObject] | None = None
    extensions: dict[str, JSONObject] | None = None
    roots: dict[str, Any] | None = None
    sampling: Sampling | None = None

class ClientNotification(WireModel):
    model_config = ConfigDict(extra='ignore')
    jsonrpc: Literal['2.0']
    method: Literal['notifications/cancelled']
    params: CancelledNotificationParams
ClientResult = Result
ContentBlock = TextContent | ImageContent | AudioContent | ResourceLink | EmbeddedResource

class DiscoverResult(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[ResultMetaObject | None, Field(alias='_meta')] = None
    cache_scope: Annotated[Literal['private', 'public'], Field(alias='cacheScope')]
    capabilities: ServerCapabilities
    instructions: str | None = None
    result_type: Annotated[str, Field(alias='resultType')]
    supported_versions: Annotated[list[str], Field(alias='supportedVersions')]
    ttl_ms: Annotated[int, Field(alias='ttlMs', ge=0)]

class DiscoverResultResponse(WireModel):
    model_config = ConfigDict(extra='ignore')
    id: RequestId
    jsonrpc: Literal['2.0']
    result: DiscoverResult

class ElicitRequest(WireModel):
    model_config = ConfigDict(extra='ignore')
    method: Literal['elicitation/create']
    params: ElicitRequestParams
EmptyResult = Result

class JSONRPCResultResponse(WireModel):
    model_config = ConfigDict(extra='ignore')
    id: RequestId
    jsonrpc: Literal['2.0']
    result: Result

class ListPromptsResult(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[ResultMetaObject | None, Field(alias='_meta')] = None
    cache_scope: Annotated[Literal['private', 'public'], Field(alias='cacheScope')]
    next_cursor: Annotated[str | None, Field(alias='nextCursor')] = None
    prompts: list[Prompt]
    result_type: Annotated[str, Field(alias='resultType')]
    ttl_ms: Annotated[int, Field(alias='ttlMs', ge=0)]

class ListPromptsResultResponse(WireModel):
    model_config = ConfigDict(extra='ignore')
    id: RequestId
    jsonrpc: Literal['2.0']
    result: ListPromptsResult

class ListResourceTemplatesResult(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[ResultMetaObject | None, Field(alias='_meta')] = None
    cache_scope: Annotated[Literal['private', 'public'], Field(alias='cacheScope')]
    next_cursor: Annotated[str | None, Field(alias='nextCursor')] = None
    resource_templates: Annotated[list[ResourceTemplate], Field(alias='resourceTemplates')]
    result_type: Annotated[str, Field(alias='resultType')]
    ttl_ms: Annotated[int, Field(alias='ttlMs', ge=0)]

class ListResourceTemplatesResultResponse(WireModel):
    model_config = ConfigDict(extra='ignore')
    id: RequestId
    jsonrpc: Literal['2.0']
    result: ListResourceTemplatesResult

class ListResourcesResult(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[ResultMetaObject | None, Field(alias='_meta')] = None
    cache_scope: Annotated[Literal['private', 'public'], Field(alias='cacheScope')]
    next_cursor: Annotated[str | None, Field(alias='nextCursor')] = None
    resources: list[Resource]
    result_type: Annotated[str, Field(alias='resultType')]
    ttl_ms: Annotated[int, Field(alias='ttlMs', ge=0)]

class ListResourcesResultResponse(WireModel):
    model_config = ConfigDict(extra='ignore')
    id: RequestId
    jsonrpc: Literal['2.0']
    result: ListResourcesResult

class ListToolsResult(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[ResultMetaObject | None, Field(alias='_meta')] = None
    cache_scope: Annotated[Literal['private', 'public'], Field(alias='cacheScope')]
    next_cursor: Annotated[str | None, Field(alias='nextCursor')] = None
    result_type: Annotated[str, Field(alias='resultType')]
    tools: list[Tool]
    ttl_ms: Annotated[int, Field(alias='ttlMs', ge=0)]

class ListToolsResultResponse(WireModel):
    model_config = ConfigDict(extra='ignore')
    id: RequestId
    jsonrpc: Literal['2.0']
    result: ListToolsResult

class LoggingMessageNotificationParams(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[NotificationMetaObject | None, Field(alias='_meta')] = None
    data: Any
    level: LoggingLevel
    logger: str | None = None

class Data(WireModel):
    model_config = ConfigDict(extra='ignore')
    required_capabilities: Annotated[ClientCapabilities, Field(alias='requiredCapabilities')]

class Error2(Error):
    model_config = ConfigDict(extra='ignore')
    code: Literal[-32021]
    data: Data

class MissingRequiredClientCapabilityError(WireModel):
    model_config = ConfigDict(extra='ignore')
    error: Error2
    id: RequestId | None = None
    jsonrpc: Literal['2.0']

class ProgressNotification(WireModel):
    model_config = ConfigDict(extra='ignore')
    jsonrpc: Literal['2.0']
    method: Literal['notifications/progress']
    params: ProgressNotificationParams

class PromptMessage(WireModel):
    model_config = ConfigDict(extra='ignore')
    content: ContentBlock
    role: Role

class RequestMetaObject(WireModel):
    model_config = ConfigDict(extra='allow')
    io_modelcontextprotocol_client_capabilities: Annotated[ClientCapabilities, Field(alias='io.modelcontextprotocol/clientCapabilities')]
    io_modelcontextprotocol_client_info: Annotated[Implementation | None, Field(alias='io.modelcontextprotocol/clientInfo')] = None
    io_modelcontextprotocol_log_level: Annotated[LoggingLevel | None, Field(alias='io.modelcontextprotocol/logLevel')] = None
    io_modelcontextprotocol_protocol_version: Annotated[str, Field(alias='io.modelcontextprotocol/protocolVersion')]
    progress_token: Annotated[ProgressToken | None, Field(alias='progressToken')] = None

class RequestParams(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[RequestMetaObject, Field(alias='_meta')]

class ResourceRequestParams(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[RequestMetaObject, Field(alias='_meta')]
    uri: str

class ResourceUpdatedNotification(WireModel):
    model_config = ConfigDict(extra='ignore')
    jsonrpc: Literal['2.0']
    method: Literal['notifications/resources/updated']
    params: ResourceUpdatedNotificationParams

class SubscriptionsAcknowledgedNotification(WireModel):
    model_config = ConfigDict(extra='ignore')
    jsonrpc: Literal['2.0']
    method: Literal['notifications/subscriptions/acknowledged']
    params: SubscriptionsAcknowledgedNotificationParams

class SubscriptionsListenRequestParams(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[RequestMetaObject, Field(alias='_meta')]
    notifications: SubscriptionFilter

class ToolResultContent(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[MetaObject | None, Field(alias='_meta')] = None
    content: list[ContentBlock]
    is_error: Annotated[bool | None, Field(alias='isError')] = None
    structured_content: Annotated[Any | None, Field(alias='structuredContent')] = None
    tool_use_id: Annotated[str, Field(alias='toolUseId')]
    type: Literal['tool_result']

class CallToolResult(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[ResultMetaObject | None, Field(alias='_meta')] = None
    content: list[ContentBlock]
    is_error: Annotated[bool | None, Field(alias='isError')] = None
    result_type: Annotated[str, Field(alias='resultType')]
    structured_content: Annotated[Any | None, Field(alias='structuredContent')] = None

class CancelledNotification(WireModel):
    model_config = ConfigDict(extra='ignore')
    jsonrpc: Literal['2.0']
    method: Literal['notifications/cancelled']
    params: CancelledNotificationParams

class CompleteRequestParams(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[RequestMetaObject, Field(alias='_meta')]
    argument: Argument
    context: Context | None = None
    ref: PromptReference | ResourceTemplateReference

class DiscoverRequest(WireModel):
    model_config = ConfigDict(extra='ignore')
    id: RequestId
    jsonrpc: Literal['2.0']
    method: Literal['server/discover']
    params: RequestParams

class GetPromptResult(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[ResultMetaObject | None, Field(alias='_meta')] = None
    description: str | None = None
    messages: list[PromptMessage]
    result_type: Annotated[str, Field(alias='resultType')]
JSONRPCMessage = JSONRPCRequest | JSONRPCNotification | JSONRPCResultResponse | JSONRPCErrorResponse
JSONRPCResponse = JSONRPCResultResponse | JSONRPCErrorResponse

class LoggingMessageNotification(WireModel):
    model_config = ConfigDict(extra='ignore')
    jsonrpc: Literal['2.0']
    method: Literal['notifications/message']
    params: LoggingMessageNotificationParams

class PaginatedRequestParams(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[RequestMetaObject, Field(alias='_meta')]
    cursor: str | None = None
SamplingMessageContentBlock = TextContent | ImageContent | AudioContent | ToolUseContent | ToolResultContent
ServerNotification = CancelledNotification | ProgressNotification | ResourceListChangedNotification | SubscriptionsAcknowledgedNotification | ResourceUpdatedNotification | PromptListChangedNotification | ToolListChangedNotification | LoggingMessageNotification

class SubscriptionsListenRequest(WireModel):
    model_config = ConfigDict(extra='ignore')
    id: RequestId
    jsonrpc: Literal['2.0']
    method: Literal['subscriptions/listen']
    params: SubscriptionsListenRequestParams

class CompleteRequest(WireModel):
    model_config = ConfigDict(extra='ignore')
    id: RequestId
    jsonrpc: Literal['2.0']
    method: Literal['completion/complete']
    params: CompleteRequestParams

class CreateMessageResult(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[MetaObject | None, Field(alias='_meta')] = None
    content: TextContent | ImageContent | AudioContent | ToolUseContent | ToolResultContent | list[SamplingMessageContentBlock]
    model: str
    role: Role
    stop_reason: Annotated[str | None, Field(alias='stopReason')] = None
InputResponse = CreateMessageResult | ListRootsResult | ElicitResult
InputResponses = dict[str, InputResponse]

class ListPromptsRequest(WireModel):
    model_config = ConfigDict(extra='ignore')
    id: RequestId
    jsonrpc: Literal['2.0']
    method: Literal['prompts/list']
    params: PaginatedRequestParams

class ListResourceTemplatesRequest(WireModel):
    model_config = ConfigDict(extra='ignore')
    id: RequestId
    jsonrpc: Literal['2.0']
    method: Literal['resources/templates/list']
    params: PaginatedRequestParams

class ListResourcesRequest(WireModel):
    model_config = ConfigDict(extra='ignore')
    id: RequestId
    jsonrpc: Literal['2.0']
    method: Literal['resources/list']
    params: PaginatedRequestParams

class ListToolsRequest(WireModel):
    model_config = ConfigDict(extra='ignore')
    id: RequestId
    jsonrpc: Literal['2.0']
    method: Literal['tools/list']
    params: PaginatedRequestParams

class PaginatedRequest(WireModel):
    model_config = ConfigDict(extra='ignore')
    id: RequestId
    jsonrpc: Literal['2.0']
    method: str
    params: PaginatedRequestParams

class ReadResourceRequestParams(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[RequestMetaObject, Field(alias='_meta')]
    input_responses: Annotated[InputResponses | None, Field(alias='inputResponses')] = None
    request_state: Annotated[str | None, Field(alias='requestState')] = None
    uri: str

class SamplingMessage(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[MetaObject | None, Field(alias='_meta')] = None
    content: TextContent | ImageContent | AudioContent | ToolUseContent | ToolResultContent | list[SamplingMessageContentBlock]
    role: Role

class CallToolRequestParams(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[RequestMetaObject, Field(alias='_meta')]
    arguments: dict[str, Any] | None = None
    input_responses: Annotated[InputResponses | None, Field(alias='inputResponses')] = None
    name: str
    request_state: Annotated[str | None, Field(alias='requestState')] = None

class CreateMessageRequestParams(WireModel):
    model_config = ConfigDict(extra='ignore')
    include_context: Annotated[Literal['allServers', 'none', 'thisServer'] | None, Field(alias='includeContext')] = None
    max_tokens: Annotated[int, Field(alias='maxTokens')]
    messages: list[SamplingMessage]
    metadata: JSONObject | None = None
    model_preferences: Annotated[ModelPreferences | None, Field(alias='modelPreferences')] = None
    stop_sequences: Annotated[list[str] | None, Field(alias='stopSequences')] = None
    system_prompt: Annotated[str | None, Field(alias='systemPrompt')] = None
    temperature: float | None = None
    tool_choice: Annotated[ToolChoice | None, Field(alias='toolChoice')] = None
    tools: list[Tool] | None = None

class GetPromptRequestParams(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[RequestMetaObject, Field(alias='_meta')]
    arguments: dict[str, str] | None = None
    input_responses: Annotated[InputResponses | None, Field(alias='inputResponses')] = None
    name: str
    request_state: Annotated[str | None, Field(alias='requestState')] = None

class InputResponseRequestParams(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[RequestMetaObject, Field(alias='_meta')]
    input_responses: Annotated[InputResponses | None, Field(alias='inputResponses')] = None
    request_state: Annotated[str | None, Field(alias='requestState')] = None

class ReadResourceRequest(WireModel):
    model_config = ConfigDict(extra='ignore')
    id: RequestId
    jsonrpc: Literal['2.0']
    method: Literal['resources/read']
    params: ReadResourceRequestParams

class CallToolRequest(WireModel):
    model_config = ConfigDict(extra='ignore')
    id: RequestId
    jsonrpc: Literal['2.0']
    method: Literal['tools/call']
    params: CallToolRequestParams

class CreateMessageRequest(WireModel):
    model_config = ConfigDict(extra='ignore')
    method: Literal['sampling/createMessage']
    params: CreateMessageRequestParams

class GetPromptRequest(WireModel):
    model_config = ConfigDict(extra='ignore')
    id: RequestId
    jsonrpc: Literal['2.0']
    method: Literal['prompts/get']
    params: GetPromptRequestParams
InputRequest = CreateMessageRequest | ListRootsRequest | ElicitRequest
InputRequests = dict[str, InputRequest]

class InputRequiredResult(WireModel):
    model_config = ConfigDict(extra='ignore')
    meta: Annotated[ResultMetaObject | None, Field(alias='_meta')] = None
    input_requests: Annotated[InputRequests | None, Field(alias='inputRequests')] = None
    request_state: Annotated[str | None, Field(alias='requestState')] = None
    result_type: Annotated[str, Field(alias='resultType')]

class ReadResourceResultResponse(WireModel):
    model_config = ConfigDict(extra='ignore')
    id: RequestId
    jsonrpc: Literal['2.0']
    result: InputRequiredResult | ReadResourceResult
ServerResult = Result | InputRequiredResult | DiscoverResult | ListResourcesResult | ListResourceTemplatesResult | ReadResourceResult | SubscriptionsListenResult | ListPromptsResult | GetPromptResult | ListToolsResult | CallToolResult | CompleteResult

class CallToolResultResponse(WireModel):
    model_config = ConfigDict(extra='ignore')
    id: RequestId
    jsonrpc: Literal['2.0']
    result: InputRequiredResult | CallToolResult
ClientRequest = DiscoverRequest | ListResourcesRequest | ListResourceTemplatesRequest | ReadResourceRequest | SubscriptionsListenRequest | ListPromptsRequest | GetPromptRequest | ListToolsRequest | CallToolRequest | CompleteRequest

class GetPromptResultResponse(WireModel):
    model_config = ConfigDict(extra='ignore')
    id: RequestId
    jsonrpc: Literal['2.0']
    result: InputRequiredResult | GetPromptResult
AnyCallToolResult = CallToolResult | InputRequiredResult
AnyGetPromptResult = GetPromptResult | InputRequiredResult
AnyReadResourceResult = ReadResourceResult | InputRequiredResult
