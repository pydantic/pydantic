# Copyright 2025 Google LLC
# Modified from google-genai 2.34.0; see LICENSE and README.md.
from abc import ABC
import datetime
from enum import Enum, EnumMeta
import io
import sys
import types as builtin_types
import typing
from typing import Annotated, Any, Callable, Literal, Optional, Union
import pydantic
from pydantic import ConfigDict, Field, PrivateAttr, WrapValidator, model_validator
from typing_extensions import TypedDict
from . import _common
if sys.version_info >= (3, 14):
    VersionedUnionType = builtin_types.UnionType
    _UNION_TYPES = (typing.Union, builtin_types.UnionType)
else:
    VersionedUnionType = Union[builtin_types.UnionType, typing._UnionGenericAlias]
    _UNION_TYPES = (typing.Union, builtin_types.UnionType)
_is_pillow_image_imported = False
PIL_Image: typing.Type = Any
PIL_Image = None
_is_pillow_image_imported = False
_is_httpx_imported = False
HttpxClient: typing.Type = Any
HttpxAsyncClient: typing.Type = Any
import httpx
_is_httpx_imported = True
import httpx2
HttpxClient = Union[httpx.Client, httpx2.Client]
HttpxAsyncClient = Union[httpx.AsyncClient, httpx2.AsyncClient]
ClientSession: typing.Type = Any
ClientSession = None
_is_aiohttp_imported = False

class MediaProcessing(_common.CaseInSensitiveEnum):
    """How the model processes input media for understanding."""
    MEDIA_PROCESSING_UNSPECIFIED = 'MEDIA_PROCESSING_UNSPECIFIED'
    STATIC = 'STATIC'
    AGENTIC = 'AGENTIC'

class Outcome(_common.CaseInSensitiveEnum):
    """Outcome of the code execution."""
    OUTCOME_UNSPECIFIED = 'OUTCOME_UNSPECIFIED'
    OUTCOME_OK = 'OUTCOME_OK'
    OUTCOME_FAILED = 'OUTCOME_FAILED'
    OUTCOME_DEADLINE_EXCEEDED = 'OUTCOME_DEADLINE_EXCEEDED'

class Language(_common.CaseInSensitiveEnum):
    """Programming language of the `code`."""
    LANGUAGE_UNSPECIFIED = 'LANGUAGE_UNSPECIFIED'
    PYTHON = 'PYTHON'

class FunctionResponseScheduling(_common.CaseInSensitiveEnum):
    """Specifies how the response should be scheduled in the conversation.

  Only applicable to NON_BLOCKING function calls, is ignored otherwise. Defaults
  to WHEN_IDLE.
  """
    SCHEDULING_UNSPECIFIED = 'SCHEDULING_UNSPECIFIED'
    SILENT = 'SILENT'
    WHEN_IDLE = 'WHEN_IDLE'
    INTERRUPT = 'INTERRUPT'

class Type(_common.CaseInSensitiveEnum):
    """Data type of the schema field."""
    TYPE_UNSPECIFIED = 'TYPE_UNSPECIFIED'
    STRING = 'STRING'
    NUMBER = 'NUMBER'
    INTEGER = 'INTEGER'
    BOOLEAN = 'BOOLEAN'
    ARRAY = 'ARRAY'
    OBJECT = 'OBJECT'
    NULL = 'NULL'

class AuthType(_common.CaseInSensitiveEnum):
    """Type of auth scheme. This enum is not supported in Gemini API."""
    AUTH_TYPE_UNSPECIFIED = 'AUTH_TYPE_UNSPECIFIED'
    NO_AUTH = 'NO_AUTH'
    API_KEY_AUTH = 'API_KEY_AUTH'
    HTTP_BASIC_AUTH = 'HTTP_BASIC_AUTH'
    GOOGLE_SERVICE_ACCOUNT_AUTH = 'GOOGLE_SERVICE_ACCOUNT_AUTH'
    OAUTH = 'OAUTH'
    OIDC_AUTH = 'OIDC_AUTH'

class HttpElementLocation(_common.CaseInSensitiveEnum):
    """The location of the API key. This enum is not supported in Gemini API."""
    HTTP_IN_UNSPECIFIED = 'HTTP_IN_UNSPECIFIED'
    HTTP_IN_QUERY = 'HTTP_IN_QUERY'
    HTTP_IN_HEADER = 'HTTP_IN_HEADER'
    HTTP_IN_PATH = 'HTTP_IN_PATH'
    HTTP_IN_BODY = 'HTTP_IN_BODY'
    HTTP_IN_COOKIE = 'HTTP_IN_COOKIE'

class ApiSpec(_common.CaseInSensitiveEnum):
    """The API spec that the external API implements.

  This enum is not supported in Gemini API.
  """
    API_SPEC_UNSPECIFIED = 'API_SPEC_UNSPECIFIED'
    SIMPLE_SEARCH = 'SIMPLE_SEARCH'
    ELASTIC_SEARCH = 'ELASTIC_SEARCH'

class SafetyPolicy(_common.CaseInSensitiveEnum):
    """SafetyPolicy"""
    SAFETY_POLICY_UNSPECIFIED = 'SAFETY_POLICY_UNSPECIFIED'
    FINANCIAL_TRANSACTIONS = 'FINANCIAL_TRANSACTIONS'
    SENSITIVE_DATA_MODIFICATION = 'SENSITIVE_DATA_MODIFICATION'
    COMMUNICATION_TOOL = 'COMMUNICATION_TOOL'
    ACCOUNT_CREATION = 'ACCOUNT_CREATION'
    DATA_MODIFICATION = 'DATA_MODIFICATION'
    USER_CONSENT_MANAGEMENT = 'USER_CONSENT_MANAGEMENT'
    LEGAL_TERMS_AND_AGREEMENTS = 'LEGAL_TERMS_AND_AGREEMENTS'

class Environment(_common.CaseInSensitiveEnum):
    """The target environment where the computer use tool operates."""
    ENVIRONMENT_UNSPECIFIED = 'ENVIRONMENT_UNSPECIFIED'
    ENVIRONMENT_BROWSER = 'ENVIRONMENT_BROWSER'
    ENVIRONMENT_MOBILE = 'ENVIRONMENT_MOBILE'
    ENVIRONMENT_DESKTOP = 'ENVIRONMENT_DESKTOP'

class PhishBlockThreshold(_common.CaseInSensitiveEnum):
    """Sites with confidence level chosen & above this value will be blocked from the search results.

  This enum is not supported in Gemini API.
  """
    PHISH_BLOCK_THRESHOLD_UNSPECIFIED = 'PHISH_BLOCK_THRESHOLD_UNSPECIFIED'
    BLOCK_LOW_AND_ABOVE = 'BLOCK_LOW_AND_ABOVE'
    BLOCK_MEDIUM_AND_ABOVE = 'BLOCK_MEDIUM_AND_ABOVE'
    BLOCK_HIGH_AND_ABOVE = 'BLOCK_HIGH_AND_ABOVE'
    BLOCK_HIGHER_AND_ABOVE = 'BLOCK_HIGHER_AND_ABOVE'
    BLOCK_VERY_HIGH_AND_ABOVE = 'BLOCK_VERY_HIGH_AND_ABOVE'
    BLOCK_ONLY_EXTREMELY_HIGH = 'BLOCK_ONLY_EXTREMELY_HIGH'

class Behavior(_common.CaseInSensitiveEnum):
    """Specifies the function Behavior.

  If not specified, the system keeps the current function call behavior. This
  field is currently only supported by the BidiGenerateContent method.
  """
    UNSPECIFIED = 'UNSPECIFIED'
    BLOCKING = 'BLOCKING'
    NON_BLOCKING = 'NON_BLOCKING'

class DynamicRetrievalConfigMode(_common.CaseInSensitiveEnum):
    """The mode of the predictor to be used in dynamic retrieval."""
    MODE_UNSPECIFIED = 'MODE_UNSPECIFIED'
    MODE_DYNAMIC = 'MODE_DYNAMIC'

class ThinkingLevel(_common.CaseInSensitiveEnum):
    """The number of thoughts tokens that the model should generate."""
    THINKING_LEVEL_UNSPECIFIED = 'THINKING_LEVEL_UNSPECIFIED'
    MINIMAL = 'MINIMAL'
    LOW = 'LOW'
    MEDIUM = 'MEDIUM'
    HIGH = 'HIGH'

class PersonGeneration(_common.CaseInSensitiveEnum):
    """Enum that controls the generation of people."""
    DONT_ALLOW = 'DONT_ALLOW'
    ALLOW_ADULT = 'ALLOW_ADULT'
    ALLOW_ALL = 'ALLOW_ALL'

class ProminentPeople(_common.CaseInSensitiveEnum):
    """Controls whether prominent people (celebrities) generation is allowed.

  If used with personGeneration, personGeneration enum would take precedence.
  For instance, if ALLOW_NONE is set, all person generation would be blocked. If
  this field is unspecified, the default behavior is to allow prominent people.
  This enum is not supported in Gemini API.
  """
    PROMINENT_PEOPLE_UNSPECIFIED = 'PROMINENT_PEOPLE_UNSPECIFIED'
    ALLOW_PROMINENT_PEOPLE = 'ALLOW_PROMINENT_PEOPLE'
    BLOCK_PROMINENT_PEOPLE = 'BLOCK_PROMINENT_PEOPLE'

class HarmCategory(_common.CaseInSensitiveEnum):
    """The harm category to be blocked."""
    HARM_CATEGORY_UNSPECIFIED = 'HARM_CATEGORY_UNSPECIFIED'
    HARM_CATEGORY_HARASSMENT = 'HARM_CATEGORY_HARASSMENT'
    HARM_CATEGORY_HATE_SPEECH = 'HARM_CATEGORY_HATE_SPEECH'
    HARM_CATEGORY_SEXUALLY_EXPLICIT = 'HARM_CATEGORY_SEXUALLY_EXPLICIT'
    HARM_CATEGORY_DANGEROUS_CONTENT = 'HARM_CATEGORY_DANGEROUS_CONTENT'
    HARM_CATEGORY_CIVIC_INTEGRITY = 'HARM_CATEGORY_CIVIC_INTEGRITY'
    HARM_CATEGORY_JAILBREAK = 'HARM_CATEGORY_JAILBREAK'
    HARM_CATEGORY_IMAGE_HATE = 'HARM_CATEGORY_IMAGE_HATE'
    HARM_CATEGORY_IMAGE_DANGEROUS_CONTENT = 'HARM_CATEGORY_IMAGE_DANGEROUS_CONTENT'
    HARM_CATEGORY_IMAGE_HARASSMENT = 'HARM_CATEGORY_IMAGE_HARASSMENT'
    HARM_CATEGORY_IMAGE_SEXUALLY_EXPLICIT = 'HARM_CATEGORY_IMAGE_SEXUALLY_EXPLICIT'

class HarmBlockMethod(_common.CaseInSensitiveEnum):
    """The method for blocking content.

  If not specified, the default behavior is to use the probability score. This
  enum is not supported in Gemini API.
  """
    HARM_BLOCK_METHOD_UNSPECIFIED = 'HARM_BLOCK_METHOD_UNSPECIFIED'
    SEVERITY = 'SEVERITY'
    PROBABILITY = 'PROBABILITY'

class HarmBlockThreshold(_common.CaseInSensitiveEnum):
    """The threshold for blocking content.

  If the harm probability exceeds this threshold, the content will be blocked.
  """
    HARM_BLOCK_THRESHOLD_UNSPECIFIED = 'HARM_BLOCK_THRESHOLD_UNSPECIFIED'
    BLOCK_LOW_AND_ABOVE = 'BLOCK_LOW_AND_ABOVE'
    BLOCK_MEDIUM_AND_ABOVE = 'BLOCK_MEDIUM_AND_ABOVE'
    BLOCK_ONLY_HIGH = 'BLOCK_ONLY_HIGH'
    BLOCK_NONE = 'BLOCK_NONE'
    OFF = 'OFF'

class FunctionCallingConfigMode(_common.CaseInSensitiveEnum):
    """Function calling mode."""
    MODE_UNSPECIFIED = 'MODE_UNSPECIFIED'
    AUTO = 'AUTO'
    ANY = 'ANY'
    NONE = 'NONE'
    VALIDATED = 'VALIDATED'

class AudioTranscriptionConfigMode(_common.CaseInSensitiveEnum):
    """Transcription mode."""
    MODE_UNSPECIFIED = 'MODE_UNSPECIFIED'
    VERBATIM = 'VERBATIM'
    SMART = 'SMART'

class FinishReason(_common.CaseInSensitiveEnum):
    """Output only. The reason why the model stopped generating tokens.

  If empty, the model has not stopped generating the tokens.
  """
    FINISH_REASON_UNSPECIFIED = 'FINISH_REASON_UNSPECIFIED'
    STOP = 'STOP'
    MAX_TOKENS = 'MAX_TOKENS'
    SAFETY = 'SAFETY'
    RECITATION = 'RECITATION'
    LANGUAGE = 'LANGUAGE'
    OTHER = 'OTHER'
    BLOCKLIST = 'BLOCKLIST'
    PROHIBITED_CONTENT = 'PROHIBITED_CONTENT'
    SPII = 'SPII'
    MALFORMED_FUNCTION_CALL = 'MALFORMED_FUNCTION_CALL'
    IMAGE_SAFETY = 'IMAGE_SAFETY'
    UNEXPECTED_TOOL_CALL = 'UNEXPECTED_TOOL_CALL'
    TOO_MANY_TOOL_CALLS = 'TOO_MANY_TOOL_CALLS'
    IMAGE_PROHIBITED_CONTENT = 'IMAGE_PROHIBITED_CONTENT'
    NO_IMAGE = 'NO_IMAGE'
    IMAGE_RECITATION = 'IMAGE_RECITATION'
    IMAGE_OTHER = 'IMAGE_OTHER'
    CONTINUATION = 'CONTINUATION'

class HarmProbability(_common.CaseInSensitiveEnum):
    """Output only. The probability of harm for this category."""
    HARM_PROBABILITY_UNSPECIFIED = 'HARM_PROBABILITY_UNSPECIFIED'
    NEGLIGIBLE = 'NEGLIGIBLE'
    LOW = 'LOW'
    MEDIUM = 'MEDIUM'
    HIGH = 'HIGH'

class HarmSeverity(_common.CaseInSensitiveEnum):
    """Output only.

  The severity of harm for this category. This enum is not supported in Gemini
  API.
  """
    HARM_SEVERITY_UNSPECIFIED = 'HARM_SEVERITY_UNSPECIFIED'
    HARM_SEVERITY_NEGLIGIBLE = 'HARM_SEVERITY_NEGLIGIBLE'
    HARM_SEVERITY_LOW = 'HARM_SEVERITY_LOW'
    HARM_SEVERITY_MEDIUM = 'HARM_SEVERITY_MEDIUM'
    HARM_SEVERITY_HIGH = 'HARM_SEVERITY_HIGH'

class UrlRetrievalStatus(_common.CaseInSensitiveEnum):
    """The status of the URL retrieval."""
    URL_RETRIEVAL_STATUS_UNSPECIFIED = 'URL_RETRIEVAL_STATUS_UNSPECIFIED'
    URL_RETRIEVAL_STATUS_SUCCESS = 'URL_RETRIEVAL_STATUS_SUCCESS'
    URL_RETRIEVAL_STATUS_ERROR = 'URL_RETRIEVAL_STATUS_ERROR'
    URL_RETRIEVAL_STATUS_PAYWALL = 'URL_RETRIEVAL_STATUS_PAYWALL'
    URL_RETRIEVAL_STATUS_UNSAFE = 'URL_RETRIEVAL_STATUS_UNSAFE'

class BlockedReason(_common.CaseInSensitiveEnum):
    """Output only. The reason why the prompt was blocked."""
    BLOCKED_REASON_UNSPECIFIED = 'BLOCKED_REASON_UNSPECIFIED'
    SAFETY = 'SAFETY'
    OTHER = 'OTHER'
    BLOCKLIST = 'BLOCKLIST'
    PROHIBITED_CONTENT = 'PROHIBITED_CONTENT'
    IMAGE_SAFETY = 'IMAGE_SAFETY'
    MODEL_ARMOR = 'MODEL_ARMOR'
    JAILBREAK = 'JAILBREAK'

class TrafficType(_common.CaseInSensitiveEnum):
    """Output only.

  The traffic type for this request. This enum is not supported in Gemini API.
  """
    TRAFFIC_TYPE_UNSPECIFIED = 'TRAFFIC_TYPE_UNSPECIFIED'
    ON_DEMAND = 'ON_DEMAND'
    ON_DEMAND_PRIORITY = 'ON_DEMAND_PRIORITY'
    ON_DEMAND_FLEX = 'ON_DEMAND_FLEX'
    ON_DEMAND_OFFPEAK = 'ON_DEMAND_OFFPEAK'
    PROVISIONED_THROUGHPUT = 'PROVISIONED_THROUGHPUT'

class MediaModality(_common.CaseInSensitiveEnum):
    """The modality that this token count applies to."""
    MODALITY_UNSPECIFIED = 'MODALITY_UNSPECIFIED'
    TEXT = 'TEXT'
    IMAGE = 'IMAGE'
    VIDEO = 'VIDEO'
    AUDIO = 'AUDIO'
    DOCUMENT = 'DOCUMENT'

class ModelStage(_common.CaseInSensitiveEnum):
    """The stage of the underlying model.

  This enum is not supported in Vertex AI.
  """
    MODEL_STAGE_UNSPECIFIED = 'MODEL_STAGE_UNSPECIFIED'
    UNSTABLE_EXPERIMENTAL = 'UNSTABLE_EXPERIMENTAL'
    EXPERIMENTAL = 'EXPERIMENTAL'
    PREVIEW = 'PREVIEW'
    STABLE = 'STABLE'
    LEGACY = 'LEGACY'
    DEPRECATED = 'DEPRECATED'
    RETIRED = 'RETIRED'

class MediaResolution(_common.CaseInSensitiveEnum):
    """The media resolution to use."""
    MEDIA_RESOLUTION_UNSPECIFIED = 'MEDIA_RESOLUTION_UNSPECIFIED'
    MEDIA_RESOLUTION_LOW = 'MEDIA_RESOLUTION_LOW'
    MEDIA_RESOLUTION_MEDIUM = 'MEDIA_RESOLUTION_MEDIUM'
    MEDIA_RESOLUTION_HIGH = 'MEDIA_RESOLUTION_HIGH'

class Modality(_common.CaseInSensitiveEnum):
    """Server content modalities."""
    MODALITY_UNSPECIFIED = 'MODALITY_UNSPECIFIED'
    TEXT = 'TEXT'
    IMAGE = 'IMAGE'
    AUDIO = 'AUDIO'
    VIDEO = 'VIDEO'

class Delivery(_common.CaseInSensitiveEnum):
    """Delivery mode for the generated content."""
    DELIVERY_UNSPECIFIED = 'DELIVERY_UNSPECIFIED'
    INLINE = 'INLINE'
    URI = 'URI'

class AspectRatio(_common.CaseInSensitiveEnum):
    """The aspect ratio for the image output."""
    ASPECT_RATIO_UNSPECIFIED = 'ASPECT_RATIO_UNSPECIFIED'
    ASPECT_RATIO_ONE_BY_ONE = 'ASPECT_RATIO_ONE_BY_ONE'
    ASPECT_RATIO_TWO_BY_THREE = 'ASPECT_RATIO_TWO_BY_THREE'
    ASPECT_RATIO_THREE_BY_TWO = 'ASPECT_RATIO_THREE_BY_TWO'
    ASPECT_RATIO_THREE_BY_FOUR = 'ASPECT_RATIO_THREE_BY_FOUR'
    ASPECT_RATIO_FOUR_BY_THREE = 'ASPECT_RATIO_FOUR_BY_THREE'
    ASPECT_RATIO_FOUR_BY_FIVE = 'ASPECT_RATIO_FOUR_BY_FIVE'
    ASPECT_RATIO_FIVE_BY_FOUR = 'ASPECT_RATIO_FIVE_BY_FOUR'
    ASPECT_RATIO_NINE_BY_SIXTEEN = 'ASPECT_RATIO_NINE_BY_SIXTEEN'
    ASPECT_RATIO_SIXTEEN_BY_NINE = 'ASPECT_RATIO_SIXTEEN_BY_NINE'
    ASPECT_RATIO_TWENTY_ONE_BY_NINE = 'ASPECT_RATIO_TWENTY_ONE_BY_NINE'
    ASPECT_RATIO_ONE_BY_EIGHT = 'ASPECT_RATIO_ONE_BY_EIGHT'
    ASPECT_RATIO_EIGHT_BY_ONE = 'ASPECT_RATIO_EIGHT_BY_ONE'
    ASPECT_RATIO_ONE_BY_FOUR = 'ASPECT_RATIO_ONE_BY_FOUR'
    ASPECT_RATIO_FOUR_BY_ONE = 'ASPECT_RATIO_FOUR_BY_ONE'

class ImageSize(_common.CaseInSensitiveEnum):
    """The size of the image output."""
    IMAGE_SIZE_UNSPECIFIED = 'IMAGE_SIZE_UNSPECIFIED'
    IMAGE_SIZE_FIVE_TWELVE = 'IMAGE_SIZE_FIVE_TWELVE'
    IMAGE_SIZE_ONE_K = 'IMAGE_SIZE_ONE_K'
    IMAGE_SIZE_TWO_K = 'IMAGE_SIZE_TWO_K'
    IMAGE_SIZE_FOUR_K = 'IMAGE_SIZE_FOUR_K'

class TuningMode(_common.CaseInSensitiveEnum):
    """Tuning mode. This enum is not supported in Gemini API."""
    TUNING_MODE_UNSPECIFIED = 'TUNING_MODE_UNSPECIFIED'
    TUNING_MODE_FULL = 'TUNING_MODE_FULL'
    TUNING_MODE_PEFT_ADAPTER = 'TUNING_MODE_PEFT_ADAPTER'

class AdapterSize(_common.CaseInSensitiveEnum):
    """Adapter size for tuning. This enum is not supported in Gemini API."""
    ADAPTER_SIZE_UNSPECIFIED = 'ADAPTER_SIZE_UNSPECIFIED'
    ADAPTER_SIZE_ONE = 'ADAPTER_SIZE_ONE'
    ADAPTER_SIZE_TWO = 'ADAPTER_SIZE_TWO'
    ADAPTER_SIZE_FOUR = 'ADAPTER_SIZE_FOUR'
    ADAPTER_SIZE_EIGHT = 'ADAPTER_SIZE_EIGHT'
    ADAPTER_SIZE_SIXTEEN = 'ADAPTER_SIZE_SIXTEEN'
    ADAPTER_SIZE_THIRTY_TWO = 'ADAPTER_SIZE_THIRTY_TWO'

class ResponseParseType(_common.CaseInSensitiveEnum):
    """Defines the type for parsing sample response.

  This enum is not supported in Gemini API.
  """
    RESPONSE_PARSE_TYPE_UNSPECIFIED = 'RESPONSE_PARSE_TYPE_UNSPECIFIED'
    IDENTITY = 'IDENTITY'
    REGEX_EXTRACT = 'REGEX_EXTRACT'

class MatchOperation(_common.CaseInSensitiveEnum):
    """Match operation to use for evaluating rewards.

  This enum is not supported in Gemini API.
  """
    MATCH_OPERATION_UNSPECIFIED = 'MATCH_OPERATION_UNSPECIFIED'
    REGEX_CONTAINS = 'REGEX_CONTAINS'
    PARTIAL_MATCH = 'PARTIAL_MATCH'
    EXACT_MATCH = 'EXACT_MATCH'

class ReinforcementTuningThinkingLevel(_common.CaseInSensitiveEnum):
    """Represents how much to think for the tuning job."""
    REINFORCEMENT_TUNING_THINKING_LEVEL_UNSPECIFIED = 'REINFORCEMENT_TUNING_THINKING_LEVEL_UNSPECIFIED'
    MINIMAL = 'MINIMAL'
    HIGH = 'HIGH'

class JobState(_common.CaseInSensitiveEnum):
    """Job state."""
    JOB_STATE_UNSPECIFIED = 'JOB_STATE_UNSPECIFIED'
    JOB_STATE_QUEUED = 'JOB_STATE_QUEUED'
    JOB_STATE_PENDING = 'JOB_STATE_PENDING'
    JOB_STATE_RUNNING = 'JOB_STATE_RUNNING'
    JOB_STATE_SUCCEEDED = 'JOB_STATE_SUCCEEDED'
    JOB_STATE_FAILED = 'JOB_STATE_FAILED'
    JOB_STATE_CANCELLING = 'JOB_STATE_CANCELLING'
    JOB_STATE_CANCELLED = 'JOB_STATE_CANCELLED'
    JOB_STATE_PAUSED = 'JOB_STATE_PAUSED'
    JOB_STATE_EXPIRED = 'JOB_STATE_EXPIRED'
    JOB_STATE_UPDATING = 'JOB_STATE_UPDATING'
    JOB_STATE_PARTIALLY_SUCCEEDED = 'JOB_STATE_PARTIALLY_SUCCEEDED'

class TuningJobState(_common.CaseInSensitiveEnum):
    """Output only.

  The detail state of the tuning job (while the overall `JobState` is running).
  This enum is not supported in Gemini API.
  """
    TUNING_JOB_STATE_UNSPECIFIED = 'TUNING_JOB_STATE_UNSPECIFIED'
    TUNING_JOB_STATE_WAITING_FOR_QUOTA = 'TUNING_JOB_STATE_WAITING_FOR_QUOTA'
    TUNING_JOB_STATE_PROCESSING_DATASET = 'TUNING_JOB_STATE_PROCESSING_DATASET'
    TUNING_JOB_STATE_WAITING_FOR_CAPACITY = 'TUNING_JOB_STATE_WAITING_FOR_CAPACITY'
    TUNING_JOB_STATE_TUNING = 'TUNING_JOB_STATE_TUNING'
    TUNING_JOB_STATE_POST_PROCESSING = 'TUNING_JOB_STATE_POST_PROCESSING'

class AggregationMetric(_common.CaseInSensitiveEnum):
    """Aggregation metric. This enum is not supported in Gemini API."""
    AGGREGATION_METRIC_UNSPECIFIED = 'AGGREGATION_METRIC_UNSPECIFIED'
    AVERAGE = 'AVERAGE'
    MODE = 'MODE'
    STANDARD_DEVIATION = 'STANDARD_DEVIATION'
    VARIANCE = 'VARIANCE'
    MINIMUM = 'MINIMUM'
    MAXIMUM = 'MAXIMUM'
    MEDIAN = 'MEDIAN'
    PERCENTILE_P90 = 'PERCENTILE_P90'
    PERCENTILE_P95 = 'PERCENTILE_P95'
    PERCENTILE_P99 = 'PERCENTILE_P99'

class PairwiseChoice(_common.CaseInSensitiveEnum):
    """Output only.

  Pairwise metric choice. This enum is not supported in Gemini API.
  """
    PAIRWISE_CHOICE_UNSPECIFIED = 'PAIRWISE_CHOICE_UNSPECIFIED'
    BASELINE = 'BASELINE'
    CANDIDATE = 'CANDIDATE'
    TIE = 'TIE'

class TuningSpeed(_common.CaseInSensitiveEnum):
    """The speed of the tuning job.

  Only supported for Veo 3.0 models. This enum is not supported in Gemini API.
  """
    TUNING_SPEED_UNSPECIFIED = 'TUNING_SPEED_UNSPECIFIED'
    REGULAR = 'REGULAR'
    FAST = 'FAST'

class TuningTask(_common.CaseInSensitiveEnum):
    """The tuning task for Veo. This enum is not supported in Gemini API."""
    TUNING_TASK_UNSPECIFIED = 'TUNING_TASK_UNSPECIFIED'
    TUNING_TASK_I2V = 'TUNING_TASK_I2V'
    TUNING_TASK_T2V = 'TUNING_TASK_T2V'
    TUNING_TASK_R2V = 'TUNING_TASK_R2V'

class VideoOrientation(_common.CaseInSensitiveEnum):
    """The orientation of the video.

  Defaults to LANDSCAPE. This enum is not supported in Gemini API.
  """
    VIDEO_ORIENTATION_UNSPECIFIED = 'VIDEO_ORIENTATION_UNSPECIFIED'
    LANDSCAPE = 'LANDSCAPE'
    PORTRAIT = 'PORTRAIT'

class DocumentState(_common.CaseInSensitiveEnum):
    """Output only.

  Current state of the `Document`. This enum is not supported in Vertex AI.
  """
    STATE_UNSPECIFIED = 'STATE_UNSPECIFIED'
    STATE_PENDING = 'STATE_PENDING'
    STATE_ACTIVE = 'STATE_ACTIVE'
    STATE_FAILED = 'STATE_FAILED'

class ServiceTier(_common.CaseInSensitiveEnum):
    """Pricing and performance service tier."""
    UNSPECIFIED = 'unspecified'
    FLEX = 'flex'
    STANDARD = 'standard'
    PRIORITY = 'priority'

class RubricContentType(_common.CaseInSensitiveEnum):
    """Represents the rubric content type."""
    RUBRIC_CONTENT_TYPE_UNSPECIFIED = 'RUBRIC_CONTENT_TYPE_UNSPECIFIED'
    PROPERTY = 'PROPERTY'
    NL_QUESTION_ANSWER = 'NL_QUESTION_ANSWER'
    PYTHON_CODE_ASSERTION = 'PYTHON_CODE_ASSERTION'

class ComputationBasedMetricType(_common.CaseInSensitiveEnum):
    """Represents the type of the computation based metric."""
    COMPUTATION_BASED_METRIC_TYPE_UNSPECIFIED = 'COMPUTATION_BASED_METRIC_TYPE_UNSPECIFIED'
    EXACT_MATCH = 'EXACT_MATCH'
    BLEU = 'BLEU'
    ROUGE = 'ROUGE'

class PartMediaResolutionLevel(_common.CaseInSensitiveEnum):
    """The tokenization quality used for given media."""
    MEDIA_RESOLUTION_UNSPECIFIED = 'MEDIA_RESOLUTION_UNSPECIFIED'
    MEDIA_RESOLUTION_LOW = 'MEDIA_RESOLUTION_LOW'
    MEDIA_RESOLUTION_MEDIUM = 'MEDIA_RESOLUTION_MEDIUM'
    MEDIA_RESOLUTION_HIGH = 'MEDIA_RESOLUTION_HIGH'
    MEDIA_RESOLUTION_ULTRA_HIGH = 'MEDIA_RESOLUTION_ULTRA_HIGH'

class ToolType(_common.CaseInSensitiveEnum):
    """The type of tool in the function call."""
    TOOL_TYPE_UNSPECIFIED = 'TOOL_TYPE_UNSPECIFIED'
    GOOGLE_SEARCH_WEB = 'GOOGLE_SEARCH_WEB'
    GOOGLE_SEARCH_IMAGE = 'GOOGLE_SEARCH_IMAGE'
    URL_CONTEXT = 'URL_CONTEXT'
    GOOGLE_MAPS = 'GOOGLE_MAPS'
    FILE_SEARCH = 'FILE_SEARCH'
    MEDIA_PROCESSING = 'MEDIA_PROCESSING'

class ResourceScope(_common.CaseInSensitiveEnum):
    """Resource scope."""
    COLLECTION = 'COLLECTION'

class JSONSchemaType(Enum):
    """The type of the data supported by JSON Schema.

  The values of the enums are lower case strings, while the values of the enums
  for the Type class are upper case strings.
  """
    NULL = 'null'
    BOOLEAN = 'boolean'
    OBJECT = 'object'
    ARRAY = 'array'
    NUMBER = 'number'
    INTEGER = 'integer'
    STRING = 'string'

class FeatureSelectionPreference(_common.CaseInSensitiveEnum):
    """Options for feature selection preference."""
    FEATURE_SELECTION_PREFERENCE_UNSPECIFIED = 'FEATURE_SELECTION_PREFERENCE_UNSPECIFIED'
    PRIORITIZE_QUALITY = 'PRIORITIZE_QUALITY'
    BALANCED = 'BALANCED'
    PRIORITIZE_COST = 'PRIORITIZE_COST'

class EmbeddingApiType(_common.CaseInSensitiveEnum):
    """Enum representing the Gemini Enterprise Agent Platform embedding API to use."""
    PREDICT = 'PREDICT'
    EMBED_CONTENT = 'EMBED_CONTENT'

class SafetyFilterLevel(_common.CaseInSensitiveEnum):
    """Enum that controls the safety filter level for objectionable content."""
    BLOCK_LOW_AND_ABOVE = 'BLOCK_LOW_AND_ABOVE'
    BLOCK_MEDIUM_AND_ABOVE = 'BLOCK_MEDIUM_AND_ABOVE'
    BLOCK_ONLY_HIGH = 'BLOCK_ONLY_HIGH'
    BLOCK_NONE = 'BLOCK_NONE'

class ImagePromptLanguage(_common.CaseInSensitiveEnum):
    """Enum that specifies the language of the text in the prompt."""
    auto = 'auto'
    en = 'en'
    ja = 'ja'
    ko = 'ko'
    hi = 'hi'
    zh = 'zh'
    pt = 'pt'
    es = 'es'

class MaskReferenceMode(_common.CaseInSensitiveEnum):
    """Enum representing the mask mode of a mask reference image."""
    MASK_MODE_DEFAULT = 'MASK_MODE_DEFAULT'
    MASK_MODE_USER_PROVIDED = 'MASK_MODE_USER_PROVIDED'
    MASK_MODE_BACKGROUND = 'MASK_MODE_BACKGROUND'
    MASK_MODE_FOREGROUND = 'MASK_MODE_FOREGROUND'
    MASK_MODE_SEMANTIC = 'MASK_MODE_SEMANTIC'

class ControlReferenceType(_common.CaseInSensitiveEnum):
    """Enum representing the control type of a control reference image."""
    CONTROL_TYPE_DEFAULT = 'CONTROL_TYPE_DEFAULT'
    CONTROL_TYPE_CANNY = 'CONTROL_TYPE_CANNY'
    CONTROL_TYPE_SCRIBBLE = 'CONTROL_TYPE_SCRIBBLE'
    CONTROL_TYPE_FACE_MESH = 'CONTROL_TYPE_FACE_MESH'

class SubjectReferenceType(_common.CaseInSensitiveEnum):
    """Enum representing the subject type of a subject reference image."""
    SUBJECT_TYPE_DEFAULT = 'SUBJECT_TYPE_DEFAULT'
    SUBJECT_TYPE_PERSON = 'SUBJECT_TYPE_PERSON'
    SUBJECT_TYPE_ANIMAL = 'SUBJECT_TYPE_ANIMAL'
    SUBJECT_TYPE_PRODUCT = 'SUBJECT_TYPE_PRODUCT'

class EditMode(_common.CaseInSensitiveEnum):
    """Enum representing the editing mode."""
    EDIT_MODE_DEFAULT = 'EDIT_MODE_DEFAULT'
    EDIT_MODE_INPAINT_REMOVAL = 'EDIT_MODE_INPAINT_REMOVAL'
    EDIT_MODE_INPAINT_INSERTION = 'EDIT_MODE_INPAINT_INSERTION'
    EDIT_MODE_OUTPAINT = 'EDIT_MODE_OUTPAINT'
    EDIT_MODE_CONTROLLED_EDITING = 'EDIT_MODE_CONTROLLED_EDITING'
    EDIT_MODE_STYLE = 'EDIT_MODE_STYLE'
    EDIT_MODE_BGSWAP = 'EDIT_MODE_BGSWAP'
    EDIT_MODE_PRODUCT_IMAGE = 'EDIT_MODE_PRODUCT_IMAGE'

class SegmentMode(_common.CaseInSensitiveEnum):
    """Enum that represents the segmentation mode."""
    FOREGROUND = 'FOREGROUND'
    BACKGROUND = 'BACKGROUND'
    PROMPT = 'PROMPT'
    SEMANTIC = 'SEMANTIC'
    INTERACTIVE = 'INTERACTIVE'

class VideoGenerationReferenceType(_common.CaseInSensitiveEnum):
    """Enum for the reference type of a video generation reference image."""
    ASSET = 'ASSET'
    STYLE = 'STYLE'

class VideoGenerationMaskMode(_common.CaseInSensitiveEnum):
    """Enum for the mask mode of a video generation mask."""
    INSERT = 'INSERT'
    REMOVE = 'REMOVE'
    REMOVE_STATIC = 'REMOVE_STATIC'
    OUTPAINT = 'OUTPAINT'

class VideoCompressionQuality(_common.CaseInSensitiveEnum):
    """Enum that controls the compression quality of the generated videos."""
    OPTIMIZED = 'OPTIMIZED'
    LOSSLESS = 'LOSSLESS'

class ImageResizeMode(_common.CaseInSensitiveEnum):
    """Resize mode for the image input for video generation."""
    CROP = 'CROP'
    PAD = 'PAD'

class TuningMethod(_common.CaseInSensitiveEnum):
    """Enum representing the tuning method."""
    SUPERVISED_FINE_TUNING = 'SUPERVISED_FINE_TUNING'
    PREFERENCE_TUNING = 'PREFERENCE_TUNING'
    DISTILLATION = 'DISTILLATION'
    REINFORCEMENT_TUNING = 'REINFORCEMENT_TUNING'

class FileState(_common.CaseInSensitiveEnum):
    """State for the lifecycle of a File."""
    STATE_UNSPECIFIED = 'STATE_UNSPECIFIED'
    PROCESSING = 'PROCESSING'
    ACTIVE = 'ACTIVE'
    FAILED = 'FAILED'

class FileSource(_common.CaseInSensitiveEnum):
    """Source of the File."""
    SOURCE_UNSPECIFIED = 'SOURCE_UNSPECIFIED'
    UPLOADED = 'UPLOADED'
    GENERATED = 'GENERATED'
    REGISTERED = 'REGISTERED'

class TurnCompleteReason(_common.CaseInSensitiveEnum):
    """The reason why the turn is complete."""
    TURN_COMPLETE_REASON_UNSPECIFIED = 'TURN_COMPLETE_REASON_UNSPECIFIED'
    MALFORMED_FUNCTION_CALL = 'MALFORMED_FUNCTION_CALL'
    RESPONSE_REJECTED = 'RESPONSE_REJECTED'
    NEED_MORE_INPUT = 'NEED_MORE_INPUT'
    PROHIBITED_INPUT_CONTENT = 'PROHIBITED_INPUT_CONTENT'
    IMAGE_PROHIBITED_INPUT_CONTENT = 'IMAGE_PROHIBITED_INPUT_CONTENT'
    INPUT_TEXT_CONTAIN_PROMINENT_PERSON_PROHIBITED = 'INPUT_TEXT_CONTAIN_PROMINENT_PERSON_PROHIBITED'
    INPUT_IMAGE_CELEBRITY = 'INPUT_IMAGE_CELEBRITY'
    INPUT_IMAGE_PHOTO_REALISTIC_CHILD_PROHIBITED = 'INPUT_IMAGE_PHOTO_REALISTIC_CHILD_PROHIBITED'
    INPUT_TEXT_NCII_PROHIBITED = 'INPUT_TEXT_NCII_PROHIBITED'
    INPUT_OTHER = 'INPUT_OTHER'
    INPUT_IP_PROHIBITED = 'INPUT_IP_PROHIBITED'
    BLOCKLIST = 'BLOCKLIST'
    UNSAFE_PROMPT_FOR_IMAGE_GENERATION = 'UNSAFE_PROMPT_FOR_IMAGE_GENERATION'
    GENERATED_IMAGE_SAFETY = 'GENERATED_IMAGE_SAFETY'
    GENERATED_CONTENT_SAFETY = 'GENERATED_CONTENT_SAFETY'
    GENERATED_AUDIO_SAFETY = 'GENERATED_AUDIO_SAFETY'
    GENERATED_VIDEO_SAFETY = 'GENERATED_VIDEO_SAFETY'
    GENERATED_CONTENT_PROHIBITED = 'GENERATED_CONTENT_PROHIBITED'
    GENERATED_CONTENT_BLOCKLIST = 'GENERATED_CONTENT_BLOCKLIST'
    GENERATED_IMAGE_PROHIBITED = 'GENERATED_IMAGE_PROHIBITED'
    GENERATED_IMAGE_CELEBRITY = 'GENERATED_IMAGE_CELEBRITY'
    GENERATED_IMAGE_PROMINENT_PEOPLE_DETECTED_BY_REWRITER = 'GENERATED_IMAGE_PROMINENT_PEOPLE_DETECTED_BY_REWRITER'
    GENERATED_IMAGE_IDENTIFIABLE_PEOPLE = 'GENERATED_IMAGE_IDENTIFIABLE_PEOPLE'
    GENERATED_IMAGE_MINORS = 'GENERATED_IMAGE_MINORS'
    OUTPUT_IMAGE_IP_PROHIBITED = 'OUTPUT_IMAGE_IP_PROHIBITED'
    GENERATED_OTHER = 'GENERATED_OTHER'
    MAX_REGENERATION_REACHED = 'MAX_REGENERATION_REACHED'

class InteractionStatus(_common.CaseInSensitiveEnum):
    """The different activity states of the live session."""
    INTERACTION_STATUS_UNSPECIFIED = 'INTERACTION_STATUS_UNSPECIFIED'
    IN_PROGRESS = 'IN_PROGRESS'
    REQUIRES_ACTION = 'REQUIRES_ACTION'
    IDLE = 'IDLE'

class VadSignalType(_common.CaseInSensitiveEnum):
    """The type of the VAD signal."""
    VAD_SIGNAL_TYPE_UNSPECIFIED = 'VAD_SIGNAL_TYPE_UNSPECIFIED'
    VAD_SIGNAL_TYPE_SOS = 'VAD_SIGNAL_TYPE_SOS'
    VAD_SIGNAL_TYPE_EOS = 'VAD_SIGNAL_TYPE_EOS'

class VoiceActivityType(_common.CaseInSensitiveEnum):
    """The type of the voice activity signal."""
    TYPE_UNSPECIFIED = 'TYPE_UNSPECIFIED'
    ACTIVITY_START = 'ACTIVITY_START'
    ACTIVITY_END = 'ACTIVITY_END'

class StartSensitivity(_common.CaseInSensitiveEnum):
    """Start of speech sensitivity."""
    START_SENSITIVITY_UNSPECIFIED = 'START_SENSITIVITY_UNSPECIFIED'
    START_SENSITIVITY_HIGH = 'START_SENSITIVITY_HIGH'
    START_SENSITIVITY_LOW = 'START_SENSITIVITY_LOW'

class EndSensitivity(_common.CaseInSensitiveEnum):
    """End of speech sensitivity."""
    END_SENSITIVITY_UNSPECIFIED = 'END_SENSITIVITY_UNSPECIFIED'
    END_SENSITIVITY_HIGH = 'END_SENSITIVITY_HIGH'
    END_SENSITIVITY_LOW = 'END_SENSITIVITY_LOW'

class ActivityHandling(_common.CaseInSensitiveEnum):
    """The different ways of handling user activity."""
    ACTIVITY_HANDLING_UNSPECIFIED = 'ACTIVITY_HANDLING_UNSPECIFIED'
    START_OF_ACTIVITY_INTERRUPTS = 'START_OF_ACTIVITY_INTERRUPTS'
    NO_INTERRUPTION = 'NO_INTERRUPTION'

class TurnCoverage(_common.CaseInSensitiveEnum):
    """Options about which input is included in the user's turn."""
    TURN_COVERAGE_UNSPECIFIED = 'TURN_COVERAGE_UNSPECIFIED'
    TURN_INCLUDES_ONLY_ACTIVITY = 'TURN_INCLUDES_ONLY_ACTIVITY'
    TURN_INCLUDES_ALL_INPUT = 'TURN_INCLUDES_ALL_INPUT'
    TURN_INCLUDES_AUDIO_ACTIVITY_AND_ALL_VIDEO = 'TURN_INCLUDES_AUDIO_ACTIVITY_AND_ALL_VIDEO'

class Scale(_common.CaseInSensitiveEnum):
    """Scale of the generated music."""
    SCALE_UNSPECIFIED = 'SCALE_UNSPECIFIED'
    C_MAJOR_A_MINOR = 'C_MAJOR_A_MINOR'
    D_FLAT_MAJOR_B_FLAT_MINOR = 'D_FLAT_MAJOR_B_FLAT_MINOR'
    D_MAJOR_B_MINOR = 'D_MAJOR_B_MINOR'
    E_FLAT_MAJOR_C_MINOR = 'E_FLAT_MAJOR_C_MINOR'
    E_MAJOR_D_FLAT_MINOR = 'E_MAJOR_D_FLAT_MINOR'
    F_MAJOR_D_MINOR = 'F_MAJOR_D_MINOR'
    G_FLAT_MAJOR_E_FLAT_MINOR = 'G_FLAT_MAJOR_E_FLAT_MINOR'
    G_MAJOR_E_MINOR = 'G_MAJOR_E_MINOR'
    A_FLAT_MAJOR_F_MINOR = 'A_FLAT_MAJOR_F_MINOR'
    A_MAJOR_G_FLAT_MINOR = 'A_MAJOR_G_FLAT_MINOR'
    B_FLAT_MAJOR_G_MINOR = 'B_FLAT_MAJOR_G_MINOR'
    B_MAJOR_A_FLAT_MINOR = 'B_MAJOR_A_FLAT_MINOR'

class MusicGenerationMode(_common.CaseInSensitiveEnum):
    """The mode of music generation."""
    MUSIC_GENERATION_MODE_UNSPECIFIED = 'MUSIC_GENERATION_MODE_UNSPECIFIED'
    QUALITY = 'QUALITY'
    DIVERSITY = 'DIVERSITY'
    VOCALIZATION = 'VOCALIZATION'

class LiveMusicPlaybackControl(_common.CaseInSensitiveEnum):
    """The playback control signal to apply to the music generation."""
    PLAYBACK_CONTROL_UNSPECIFIED = 'PLAYBACK_CONTROL_UNSPECIFIED'
    PLAY = 'PLAY'
    PAUSE = 'PAUSE'
    STOP = 'STOP'
    RESET_CONTEXT = 'RESET_CONTEXT'

class PartMediaResolution(_common.BaseModel):
    """Media resolution for the input media."""
    level: Optional[PartMediaResolutionLevel] = Field(default=None, description='The tokenization quality used for given media.\n    ')
    num_tokens: Optional[int] = Field(default=None, description='Specifies the required sequence length for media tokenization.\n    ')

class PartMediaResolutionDict(TypedDict, total=False):
    """Media resolution for the input media."""
    level: Optional[PartMediaResolutionLevel]
    num_tokens: Optional[int]

class ToolCall(_common.BaseModel):
    """A predicted server-side `ToolCall` returned from the model.

  This message contains information about a tool that the model wants to invoke.
  The client is NOT expected to execute this `ToolCall`. Instead, the
  client should pass this `ToolCall` back to the API in a subsequent turn
  within a `Content` message, along with the corresponding `ToolResponse`.
  """
    id: Optional[str] = Field(default=None, description='Unique identifier of the tool call. The server returns the tool response with the matching `id`.')
    tool_type: Optional[ToolType] = Field(default=None, description='The type of tool that was called.')
    args: Optional[dict[str, Any]] = Field(default=None, description='The tool call arguments. Example: {"arg1": "value1", "arg2": "value2"}.')

class ToolCallDict(TypedDict, total=False):
    """A predicted server-side `ToolCall` returned from the model.

  This message contains information about a tool that the model wants to invoke.
  The client is NOT expected to execute this `ToolCall`. Instead, the
  client should pass this `ToolCall` back to the API in a subsequent turn
  within a `Content` message, along with the corresponding `ToolResponse`.
  """
    id: Optional[str]
    tool_type: Optional[ToolType]
    args: Optional[dict[str, Any]]

class ToolResponse(_common.BaseModel):
    """The output from a server-side `ToolCall` execution.

  This message contains the results of a tool invocation that was initiated by a
  `ToolCall` from the model. The client should pass this `ToolResponse` back to
  the API in a subsequent turn within a `Content` message, along with the
  corresponding `ToolCall`.
  """
    id: Optional[str] = Field(default=None, description='The identifier of the tool call this response is for.')
    tool_type: Optional[ToolType] = Field(default=None, description='The type of tool that was called, matching the tool_type in the corresponding ToolCall.')
    response: Optional[dict[str, Any]] = Field(default=None, description='The tool response.')

class ToolResponseDict(TypedDict, total=False):
    """The output from a server-side `ToolCall` execution.

  This message contains the results of a tool invocation that was initiated by a
  `ToolCall` from the model. The client should pass this `ToolResponse` back to
  the API in a subsequent turn within a `Content` message, along with the
  corresponding `ToolCall`.
  """
    id: Optional[str]
    tool_type: Optional[ToolType]
    response: Optional[dict[str, Any]]

class SpeechMetadata(_common.BaseModel):
    """Extra metadata associated with the part for speech synthesis."""
    speaker: Optional[str] = Field(default=None, description='The speaker for this part, which must match a `speaker` name in\n      `MultiSpeakerVoiceConfig.speaker_voice_configs`.')
    style: Optional[str] = Field(default=None, description='The style instruction for how the voice should be synthesized\n      (e.g. "excited, fast-paced").')

class SpeechMetadataDict(TypedDict, total=False):
    """Extra metadata associated with the part for speech synthesis."""
    speaker: Optional[str]
    style: Optional[str]

class CodeExecutionResult(_common.BaseModel):
    """Result of executing the ExecutableCode.

  Generated only when the `CodeExecution` tool is used.
  """
    outcome: Optional[Outcome] = Field(default=None, description='Required. Outcome of the code execution.')
    output: Optional[str] = Field(default=None, description='Optional. Contains stdout when code execution is successful, stderr or other description otherwise.')
    id: Optional[str] = Field(default=None, description='Optional. The identifier of the `ExecutableCode` part this result is for. Only populated if the corresponding `ExecutableCode` has an id.')

class CodeExecutionResultDict(TypedDict, total=False):
    """Result of executing the ExecutableCode.

  Generated only when the `CodeExecution` tool is used.
  """
    outcome: Optional[Outcome]
    output: Optional[str]
    id: Optional[str]

class ExecutableCode(_common.BaseModel):
    """Code generated by the model that is meant to be executed, and the result returned to the model.

  Generated when using the `CodeExecution` tool, in which the code will be
  automatically executed, and a corresponding CodeExecutionResult will also be
  generated.
  """
    code: Optional[str] = Field(default=None, description='Required. The code to be executed.')
    language: Optional[Language] = Field(default=None, description='Required. Programming language of the `code`.')
    id: Optional[str] = Field(default=None, description='Optional. Unique identifier of the `ExecutableCode` part. The server returns the `CodeExecutionResult` with the matching `id`.')

class ExecutableCodeDict(TypedDict, total=False):
    """Code generated by the model that is meant to be executed, and the result returned to the model.

  Generated when using the `CodeExecution` tool, in which the code will be
  automatically executed, and a corresponding CodeExecutionResult will also be
  generated.
  """
    code: Optional[str]
    language: Optional[Language]
    id: Optional[str]

class FileData(_common.BaseModel):
    """URI-based data.

  A FileData message contains a URI pointing to data of a specific media type.
  It is used to represent images, audio, and video stored in Google Cloud
  Storage.
  """
    display_name: Optional[str] = Field(default=None, description='Optional. The display name of the file. Used to provide a label or filename to distinguish files. This field is only returned in `PromptMessage` for prompt management. It is used in the Gemini calls only when server side tools (`code_execution`, `google_search`, and `url_context`) are enabled.')
    file_uri: Optional[str] = Field(default=None, description='Required. The URI of the file in Google Cloud Storage.')
    mime_type: Optional[str] = Field(default=None, description='Required. The IANA standard MIME type of the source data.')

class FileDataDict(TypedDict, total=False):
    """URI-based data.

  A FileData message contains a URI pointing to data of a specific media type.
  It is used to represent images, audio, and video stored in Google Cloud
  Storage.
  """
    display_name: Optional[str]
    file_uri: Optional[str]
    mime_type: Optional[str]

class PartialArg(_common.BaseModel):
    """Partial argument value of the function call.

  This data type is not supported in Gemini API.
  """
    bool_value: Optional[bool] = Field(default=None, description='Optional. Represents a boolean value.')
    json_path: Optional[str] = Field(default=None, description='Required. A JSON Path (RFC 9535) to the argument being streamed. https://datatracker.ietf.org/doc/html/rfc9535. e.g. "$.foo.bar[0].data".')
    null_value: Optional[Literal['NULL_VALUE']] = Field(default=None, description='Optional. Represents a null value.')
    number_value: Optional[float] = Field(default=None, description='Optional. Represents a double value.')
    string_value: Optional[str] = Field(default=None, description='Optional. Represents a string value.')
    will_continue: Optional[bool] = Field(default=None, description='Optional. Whether this is not the last part of the same json_path. If true, another PartialArg message for the current json_path is expected to follow.')

class PartialArgDict(TypedDict, total=False):
    """Partial argument value of the function call.

  This data type is not supported in Gemini API.
  """
    bool_value: Optional[bool]
    json_path: Optional[str]
    null_value: Optional[Literal['NULL_VALUE']]
    number_value: Optional[float]
    string_value: Optional[str]
    will_continue: Optional[bool]

class FunctionCall(_common.BaseModel):
    """A predicted FunctionCall returned from the model that contains a string representing the FunctionDeclaration.name and a structured JSON object containing the parameters and their values."""
    id: Optional[str] = Field(default=None, description='Optional. The unique id of the function call. If populated, the client to execute the `function_call` and return the response with the matching `id`.')
    args: Optional[dict[str, Any]] = Field(default=None, description='Optional. The function parameters and values in JSON object format. See FunctionDeclaration.parameters for parameter details.')
    name: Optional[str] = Field(default=None, description='Optional. The name of the function to call. Matches FunctionDeclaration.name.')
    partial_args: Optional[list[PartialArg]] = Field(default=None, description='Optional. The partial argument value of the function call. If provided, represents the arguments/fields that are streamed incrementally. This field is not supported in Gemini API.')
    will_continue: Optional[bool] = Field(default=None, description='Optional. Whether this is the last part of the FunctionCall. If true, another partial message for the current FunctionCall is expected to follow. This field is not supported in Gemini API.')

class FunctionCallDict(TypedDict, total=False):
    """A predicted FunctionCall returned from the model that contains a string representing the FunctionDeclaration.name and a structured JSON object containing the parameters and their values."""
    id: Optional[str]
    args: Optional[dict[str, Any]]
    name: Optional[str]
    partial_args: Optional[list[PartialArgDict]]
    will_continue: Optional[bool]

class FunctionResponseBlob(_common.BaseModel):
    """Raw media bytes for function response.

  Text should not be sent as raw bytes, use the 'text' field.
  """
    mime_type: Optional[str] = Field(default=None, description='Required. The IANA standard MIME type of the source data.')
    data: Optional[bytes] = Field(default=None, description='Required. Raw bytes.')
    display_name: Optional[str] = Field(default=None, description='Optional. Display name of the blob. Used to provide a label or filename to distinguish blobs. This field is only returned in PromptMessage for prompt management. It is currently used in the Gemini GenerateContent calls only when server side tools (code_execution, google_search, and url_context) are enabled.')

class FunctionResponseBlobDict(TypedDict, total=False):
    """Raw media bytes for function response.

  Text should not be sent as raw bytes, use the 'text' field.
  """
    mime_type: Optional[str]
    data: Optional[bytes]
    display_name: Optional[str]

class FunctionResponseFileData(_common.BaseModel):
    """URI based data for function response."""
    file_uri: Optional[str] = Field(default=None, description='Required. URI.')
    mime_type: Optional[str] = Field(default=None, description='Required. The IANA standard MIME type of the source data.')
    display_name: Optional[str] = Field(default=None, description='Optional. Display name of the file data. Used to provide a label or filename to distinguish file datas. This field is only returned in PromptMessage for prompt management. It is currently used in the Gemini GenerateContent calls only when server side tools (code_execution, google_search, and url_context) are enabled.')

class FunctionResponseFileDataDict(TypedDict, total=False):
    """URI based data for function response."""
    file_uri: Optional[str]
    mime_type: Optional[str]
    display_name: Optional[str]

class FunctionResponsePart(_common.BaseModel):
    """A datatype containing media that is part of a `FunctionResponse` message.

  A `FunctionResponsePart` consists of data which has an associated datatype. A
  `FunctionResponsePart` can only contain one of the accepted types in
  `FunctionResponsePart.data`. A `FunctionResponsePart` must have a fixed IANA
  MIME type identifying the type and subtype of the media if the `inline_data`
  field is filled with raw bytes.
  """
    inline_data: Optional[FunctionResponseBlob] = Field(default=None, description='Inline media bytes.')
    file_data: Optional[FunctionResponseFileData] = Field(default=None, description='URI based data.')
    media_processing: Optional[MediaProcessing] = Field(default=None, description="Optional. How the model processes this part's media for understanding. Only meaningful for video parts (`inline_data` or `file_data` with video mime). Non-video parts ignore this field. This field is not supported in Vertex AI.")

class FunctionResponsePartDict(TypedDict, total=False):
    """A datatype containing media that is part of a `FunctionResponse` message.

  A `FunctionResponsePart` consists of data which has an associated datatype. A
  `FunctionResponsePart` can only contain one of the accepted types in
  `FunctionResponsePart.data`. A `FunctionResponsePart` must have a fixed IANA
  MIME type identifying the type and subtype of the media if the `inline_data`
  field is filled with raw bytes.
  """
    inline_data: Optional[FunctionResponseBlobDict]
    file_data: Optional[FunctionResponseFileDataDict]
    media_processing: Optional[MediaProcessing]

class FunctionResponse(_common.BaseModel):
    """The result output from a FunctionCall that contains a string representing the FunctionDeclaration.name and a structured JSON object containing any output from the function is used as context to the model.

  This should contain the result of a `FunctionCall` made based on model
  prediction.
  """
    will_continue: Optional[bool] = Field(default=None, description='Optional. Signals that function call continues, and more responses will be returned, turning the function call into a generator. Is only applicable to NON_BLOCKING function calls, is ignored otherwise. If set to false, future responses will not be considered. It is allowed to return empty `response` with `will_continue=False` to signal that the function call is finished. This may still trigger the model generation. To avoid triggering the generation and finish the function call, additionally set `scheduling` to `SILENT`. This field is not supported in Vertex AI.')
    scheduling: Optional[FunctionResponseScheduling] = Field(default=None, description='Optional. Specifies how the response should be scheduled in the conversation. Only applicable to NON_BLOCKING function calls, is ignored otherwise. Defaults to WHEN_IDLE.')
    parts: Optional[list[FunctionResponsePart]] = Field(default=None, description='Optional. Ordered `Parts` that constitute a function response. Parts may have different IANA MIME types.')
    id: Optional[str] = Field(default=None, description='Optional. The id of the function call this response is for. Populated by the client to match the corresponding function call `id`.')
    name: Optional[str] = Field(default=None, description='Required. The name of the function to call. Matches FunctionDeclaration.name and FunctionCall.name.')
    response: Optional[dict[str, Any]] = Field(default=None, description='Required. The function response in JSON object format. Use "output" key to specify function output and "error" key to specify error details (if any). If "output" and "error" keys are not specified, then whole "response" is treated as function output.')

class FunctionResponseDict(TypedDict, total=False):
    """The result output from a FunctionCall that contains a string representing the FunctionDeclaration.name and a structured JSON object containing any output from the function is used as context to the model.

  This should contain the result of a `FunctionCall` made based on model
  prediction.
  """
    will_continue: Optional[bool]
    scheduling: Optional[FunctionResponseScheduling]
    parts: Optional[list[FunctionResponsePartDict]]
    id: Optional[str]
    name: Optional[str]
    response: Optional[dict[str, Any]]

class Blob(_common.BaseModel):
    """A content blob.

  A Blob contains data of a specific media type. It is used to represent images,
  audio, and video.
  """
    data: Optional[bytes] = Field(default=None, description='Required. The raw bytes of the data.')
    display_name: Optional[str] = Field(default=None, description='Optional. The display name of the blob. Used to provide a label or filename to distinguish blobs. This field is only returned in `PromptMessage` for prompt management. It is used in the Gemini calls only when server-side tools (`code_execution`, `google_search`, and `url_context`) are enabled.')
    mime_type: Optional[str] = Field(default=None, description='Required. The IANA standard MIME type of the source data.')

class BlobDict(TypedDict, total=False):
    """A content blob.

  A Blob contains data of a specific media type. It is used to represent images,
  audio, and video.
  """
    data: Optional[bytes]
    display_name: Optional[str]
    mime_type: Optional[str]

class VideoMetadata(_common.BaseModel):
    """Provides metadata for a video, including the start and end offsets for clipping and the frame rate."""
    end_offset: Optional[str] = Field(default=None, description='Optional. The end offset of the video.')
    fps: Optional[float] = Field(default=None, description='Optional. The frame rate of the video sent to the model. If not specified, the default value is 1.0. The valid range is (0.0, 24.0].')
    start_offset: Optional[str] = Field(default=None, description='Optional. The start offset of the video.')

class VideoMetadataDict(TypedDict, total=False):
    """Provides metadata for a video, including the start and end offsets for clipping and the frame rate."""
    end_offset: Optional[str]
    fps: Optional[float]
    start_offset: Optional[str]

class WordInfo(_common.BaseModel):
    """Information about a single recognized word."""
    word: Optional[str] = Field(default=None, description='Transcript of the word.\n      ')
    start_offset: Optional[str] = Field(default=None, description='Start offset in time of the word relative to the start of the audio.\n      ')
    end_offset: Optional[str] = Field(default=None, description='End offset in time of the word relative to the start of the audio.\n      ')

class WordInfoDict(TypedDict, total=False):
    """Information about a single recognized word."""
    word: Optional[str]
    start_offset: Optional[str]
    end_offset: Optional[str]

class Transcription(_common.BaseModel):
    """Audio transcription in Server Content."""
    text: Optional[str] = Field(default=None, description='Optional. Transcription text.')
    finished: Optional[bool] = Field(default=None, description='Optional. The bool indicates the end of the transcription.')
    language_code: Optional[str] = Field(default=None, description='The BCP-47 language code of the transcription.')
    speaker_label: Optional[str] = Field(default=None, description='A label identifying the speaker of this audio segment (e.g. "spk_1", "spk_2").\n      ')
    words: Optional[list[WordInfo]] = Field(default=None, description='Detailed word-level transcriptions and timing details.\n      ')
    start_offset: Optional[str] = Field(default=None, description='Start offset in time of the transcription relative to the start of the audio.\n      ')
    end_offset: Optional[str] = Field(default=None, description='End offset in time of the transcription relative to the start of the audio.\n      ')

class TranscriptionDict(TypedDict, total=False):
    """Audio transcription in Server Content."""
    text: Optional[str]
    finished: Optional[bool]
    language_code: Optional[str]
    speaker_label: Optional[str]
    words: Optional[list[WordInfoDict]]
    start_offset: Optional[str]
    end_offset: Optional[str]

class Part(_common.BaseModel):
    """A datatype containing media content.

  Exactly one field within a Part should be set, representing the specific type
  of content being conveyed. Using multiple fields within the same `Part`
  instance is considered invalid.
  """
    media_resolution: Optional[PartMediaResolution] = Field(default=None, description='Media resolution for the input media.\n    ')
    code_execution_result: Optional[CodeExecutionResult] = Field(default=None, description='Optional. The result of executing the ExecutableCode.')
    executable_code: Optional[ExecutableCode] = Field(default=None, description='Optional. Code generated by the model that is intended to be executed.')
    file_data: Optional[FileData] = Field(default=None, description='Optional. The URI-based data of the part. This can be used to include files from Google Cloud Storage.')
    function_call: Optional[FunctionCall] = Field(default=None, description='Optional. A predicted function call returned from the model. This contains the name of the function to call and the arguments to pass to the function.')
    function_response: Optional[FunctionResponse] = Field(default=None, description='Optional. The result of a function call. This is used to provide the model with the result of a function call that it predicted.')
    inline_data: Optional[Blob] = Field(default=None, description='Optional. The inline data content of the part. This can be used to include images, audio, or video in a request.')
    text: Optional[str] = Field(default=None, description='Optional. The text content of the part. When sent from the VSCode Gemini Code Assist extension, references to @mentioned items will be converted to markdown boldface text. For example `@my-repo` will be converted to and sent as `**my-repo**` by the IDE agent.')
    thought: Optional[bool] = Field(default=None, description="Optional. Indicates whether the `part` represents the model's thought process or reasoning.")
    thought_signature: Optional[bytes] = Field(default=None, description='Optional. An opaque signature for the thought so it can be reused in subsequent requests.')
    video_metadata: Optional[VideoMetadata] = Field(default=None, description='Optional. Video metadata. The metadata should only be specified while the video data is presented in inline_data or file_data.')
    tool_call: Optional[ToolCall] = Field(default=None, description='Server-side tool call. This field is populated when the model predicts a tool invocation that should be executed on the server. The client is expected to echo this message back to the API.')
    tool_response: Optional[ToolResponse] = Field(default=None, description='The output from a server-side ToolCall execution. This field is populated by the client with the results of executing the corresponding ToolCall.')
    part_metadata: Optional[dict[str, Any]] = Field(default=None, description='Custom metadata associated with the Part. Agents using genai.Part as content representation may need to keep track of the additional information. For example it can be name of a file/source from which the Part originates or a way to multiplex multiple Part streams. This field is not supported in Vertex AI.')
    audio_transcription: Optional[Transcription] = Field(default=None, description='Output only. The transcription of the audio part.')
    media_processing: Optional[MediaProcessing] = Field(default=None, description="How the model processes this part's media for understanding.")
    speech_metadata: Optional[SpeechMetadata] = Field(default=None, description='Extra metadata associated with the part for speech synthesis, such\n      as speaker and style. Only valid when `Part.data` is set to `text`.')

    def __init__(self, value: Optional['PartUnionDict']=None, /, *, video_metadata: Optional[VideoMetadata]=None, thought: Optional[bool]=None, inline_data: Optional[Blob]=None, file_data: Optional[FileData]=None, thought_signature: Optional[bytes]=None, function_call: Optional[FunctionCall]=None, code_execution_result: Optional[CodeExecutionResult]=None, executable_code: Optional[ExecutableCode]=None, function_response: Optional[FunctionResponse]=None, text: Optional[str]=None, **kwargs: Any):
        part_dict = dict(video_metadata=video_metadata, thought=thought, inline_data=inline_data, file_data=file_data, thought_signature=thought_signature, function_call=function_call, code_execution_result=code_execution_result, executable_code=executable_code, function_response=function_response, text=text)
        part_dict = {k: v for k, v in part_dict.items() if v is not None}
        if part_dict and value is not None:
            raise ValueError('Positional and keyword arguments can not be combined when initializing a Part.')
        if value is None:
            pass
        elif isinstance(value, str):
            part_dict['text'] = value
        elif isinstance(value, File):
            if not value.uri or not value.mime_type:
                raise ValueError('file uri and mime_type are required.')
            part_dict['file_data'] = FileData(file_uri=value.uri, mime_type=value.mime_type, display_name=value.display_name)
        elif isinstance(value, dict):
            try:
                Part.model_validate(value)
                part_dict.update(value)
            except pydantic.ValidationError:
                part_dict['file_data'] = FileData.model_validate(value)
        elif isinstance(value, Part):
            part_dict.update(value.dict())
        elif 'image' in value.__class__.__name__.lower():
            suffix = value.format.lower() if value.format else 'jpeg'
            mimetype = f'image/{suffix}'
            bytes_io = io.BytesIO()
            value.save(bytes_io, suffix.upper())
            part_dict['inline_data'] = Blob(data=bytes_io.getvalue(), mime_type=mimetype)
        else:
            raise ValueError(f'Unsupported content part type: {type(value)}')
        super().__init__(**part_dict, **kwargs)

class PartDict(TypedDict, total=False):
    """A datatype containing media content.

  Exactly one field within a Part should be set, representing the specific type
  of content being conveyed. Using multiple fields within the same `Part`
  instance is considered invalid.
  """
    media_resolution: Optional[PartMediaResolutionDict]
    code_execution_result: Optional[CodeExecutionResultDict]
    executable_code: Optional[ExecutableCodeDict]
    file_data: Optional[FileDataDict]
    function_call: Optional[FunctionCallDict]
    function_response: Optional[FunctionResponseDict]
    inline_data: Optional[BlobDict]
    text: Optional[str]
    thought: Optional[bool]
    thought_signature: Optional[bytes]
    video_metadata: Optional[VideoMetadataDict]
    tool_call: Optional[ToolCallDict]
    tool_response: Optional[ToolResponseDict]
    part_metadata: Optional[dict[str, Any]]
    audio_transcription: Optional[TranscriptionDict]
    media_processing: Optional[MediaProcessing]
    speech_metadata: Optional[SpeechMetadataDict]

class Content(_common.BaseModel):
    """Contains the multi-part content of a message."""
    parts: Optional[list[Part]] = Field(default=None, description='List of parts that constitute a single message. Each part may have\n      a different IANA MIME type.')
    role: Optional[str] = Field(default=None, description="Optional. The producer of the content. Must be either 'user' or 'model'. If not set, the service will default to 'user'.")

class HttpRetryOptions(_common.BaseModel):
    """HTTP retry options to be used in each of the requests."""
    attempts: Optional[int] = Field(default=None, description='Maximum number of attempts, including the original request.\n      If 0 or 1, it means no retries. If not specified, default to 5.')
    initial_delay: Optional[float] = Field(default=None, description='Initial delay before the first retry, in fractions of a second. If not specified, default to 1.0 second.')
    max_delay: Optional[float] = Field(default=None, description='Maximum delay between retries, in fractions of a second. If not specified, default to 60.0 seconds.')
    exp_base: Optional[float] = Field(default=None, description='Multiplier by which the delay increases after each attempt. If not specified, default to 2.0.')
    jitter: Optional[float] = Field(default=None, description='Randomness factor for the delay. If not specified, default to 1.0.')
    http_status_codes: Optional[list[int]] = Field(default=None, description='List of HTTP status codes that should trigger a retry.\n      If not specified, a default set of retryable codes (408, 429, and 5xx) may be used.')

class HttpOptions(_common.BaseModel):
    """HTTP options to be used in each of the requests."""
    base_url: Optional[str] = Field(default=None, description='The base URL for the AI platform service endpoint.')
    base_url_resource_scope: Optional[ResourceScope] = Field(default=None, description='The resource scope used to constructing the resource name when base_url is set')
    api_version: Optional[str] = Field(default=None, description='Specifies the version of the API to use.')
    headers: Optional[dict[str, str]] = Field(default=None, description='Additional HTTP headers to be sent with the request.')
    timeout: Optional[int] = Field(default=None, description='Timeout for the request in milliseconds.')
    client_args: Optional[dict[str, Any]] = Field(default=None, description='Args passed to the HTTP client.')
    async_client_args: Optional[dict[str, Any]] = Field(default=None, description='Args passed to the async HTTP client.')
    extra_body: Optional[dict[str, Any]] = Field(default=None, description="Extra parameters to add to the request body.\n      The structure must match the backend API's request structure.\n      - Gemini Enterprise Agent Platform backend API docs: https://cloud.google.com/vertex-ai/docs/reference/rest\n      - GeminiAPI backend API docs: https://ai.google.dev/api/rest")
    retry_options: Optional[HttpRetryOptions] = Field(default=None, description='HTTP retry options for the request.')
    httpx_client: Optional['HttpxClient'] = Field(default=None, description='A custom httpx client to be used for the request.')
    httpx_async_client: Optional['HttpxAsyncClient'] = Field(default=None, description='A custom httpx async client to be used for the request.')
    aiohttp_client: Optional['ClientSession'] = Field(default=None, description='A custom aiohttp client session to be used for the request.')

class JSONSchema(_common.BaseModel):
    """A subset of JSON Schema according to 2020-12 JSON Schema draft.

  Represents a subset of a JSON Schema object that is used by the Gemini model.
  The difference between this class and the Schema class is that this class is
  compatible with OpenAPI 3.1 schema objects. And the Schema class is used to
  make API call to Gemini model.
  """
    type: Optional[Union[JSONSchemaType, list[JSONSchemaType]]] = Field(default=None, description='Validation succeeds if the type of the instance matches the type represented by the given type, or matches at least one of the given types.')
    format: Optional[str] = Field(default=None, description='Define semantic information about a string instance.')
    title: Optional[str] = Field(default=None, description='A preferably short description about the purpose of the instance described by the schema.')
    description: Optional[str] = Field(default=None, description='An explanation about the purpose of the instance described by the schema.')
    default: Optional[Any] = Field(default=None, description='This keyword can be used to supply a default JSON value associated with a particular schema.')
    items: Optional['JSONSchema'] = Field(default=None, description='Validation succeeds if each element of the instance not covered by prefixItems validates against this schema.')
    min_items: Optional[int] = Field(default=None, description='An array instance is valid if its size is greater than, or equal to, the value of this keyword.')
    max_items: Optional[int] = Field(default=None, description='An array instance is valid if its size is less than, or equal to, the value of this keyword.')
    enum: Optional[list[Any]] = Field(default=None, description='Validation succeeds if the instance is equal to one of the elements in this keyword’s array value.')
    properties: Optional[dict[str, 'JSONSchema']] = Field(default=None, description='Validation succeeds if, for each name that appears in both the instance and as a name within this keyword’s value, the child instance for that name successfully validates against the corresponding schema.')
    required: Optional[list[str]] = Field(default=None, description='An object instance is valid against this keyword if every item in the array is the name of a property in the instance.')
    min_properties: Optional[int] = Field(default=None, description='An object instance is valid if its number of properties is greater than, or equal to, the value of this keyword.')
    max_properties: Optional[int] = Field(default=None, description='An object instance is valid if its number of properties is less than, or equal to, the value of this keyword.')
    minimum: Optional[float] = Field(default=None, description='Validation succeeds if the numeric instance is greater than or equal to the given number.')
    maximum: Optional[float] = Field(default=None, description='Validation succeeds if the numeric instance is less than or equal to the given number.')
    min_length: Optional[int] = Field(default=None, description='A string instance is valid against this keyword if its length is greater than, or equal to, the value of this keyword.')
    max_length: Optional[int] = Field(default=None, description='A string instance is valid against this keyword if its length is less than, or equal to, the value of this keyword.')
    pattern: Optional[str] = Field(default=None, description='A string instance is considered valid if the regular expression matches the instance successfully.')
    additional_properties: Optional[Any] = Field(default=None, description='Can either be a boolean or an object; controls the presence of additional properties.')
    any_of: Optional[list['JSONSchema']] = Field(default=None, description='An instance validates successfully against this keyword if it validates successfully against at least one schema defined by this keyword’s value.')
    unique_items: Optional[bool] = Field(default=None, description='Boolean value that indicates whether the items in an array are unique.')
    ref: Optional[str] = Field(default=None, alias='$ref', description='Allows indirect references between schema nodes.')
    defs: Optional[dict[str, 'JSONSchema']] = Field(default=None, alias='$defs', description='Schema definitions to be used with $ref.')
    one_of: Optional[list['JSONSchema']] = Field(default=None, description="An instance validates successfully against this keyword if it validates successfully against exactly one schema defined by this keyword's value.")

class Schema(_common.BaseModel):
    """Schema is used to define the format of input/output data.

  Represents a select subset of an [OpenAPI 3.0 schema
  object](https://spec.openapis.org/oas/v3.0.3#schema-object). More fields may
  be added in the future as needed.
  """
    additional_properties: Optional[Any] = Field(default=None, description='Optional. Can either be a boolean or an object; controls the presence of additional properties.')
    defs: Optional[dict[str, 'Schema']] = Field(default=None, description='Optional. A map of definitions for use by `ref` Only allowed at the root of the schema.')
    ref: Optional[str] = Field(default=None, description='Optional. Allows indirect references between schema nodes. The value should be a valid reference to a child of the root `defs`. For example, the following schema defines a reference to a schema node named "Pet": type: object properties: pet: ref: #/defs/Pet defs: Pet: type: object properties: name: type: string The value of the "pet" property is a reference to the schema node named "Pet". See details in https://json-schema.org/understanding-json-schema/structuring')
    any_of: Optional[list['Schema']] = Field(default=None, description='Optional. The instance must be valid against any (one or more) of the subschemas listed in `any_of`.')
    default: Optional[Any] = Field(default=None, description='Optional. Default value to use if the field is not specified.')
    description: Optional[str] = Field(default=None, description='Optional. Describes the data. The model uses this field to understand the purpose of the schema and how to use it. It is a best practice to provide a clear and descriptive explanation for the schema and its properties here, rather than in the prompt.')
    enum: Optional[list[str]] = Field(default=None, description='Optional. Possible values of the field. This field can be used to restrict a value to a fixed set of values. To mark a field as an enum, set `format` to `enum` and provide the list of possible values in `enum`. For example: 1. To define directions: `{type:STRING, format:enum, enum:["EAST", "NORTH", "SOUTH", "WEST"]}` 2. To define apartment numbers: `{type:INTEGER, format:enum, enum:["101", "201", "301"]}`')
    example: Optional[Any] = Field(default=None, description='Optional. Example of an instance of this schema.')
    format: Optional[str] = Field(default=None, description='Optional. The format of the data. For `NUMBER` type, format can be `float` or `double`. For `INTEGER` type, format can be `int32` or `int64`. For `STRING` type, format can be `email`, `byte`, `date`, `date-time`, `password`, and other formats to further refine the data type.')
    items: Optional['Schema'] = Field(default=None, description='Optional. If type is `ARRAY`, `items` specifies the schema of elements in the array.')
    max_items: Optional[int] = Field(default=None, description='Optional. If type is `ARRAY`, `max_items` specifies the maximum number of items in an array.')
    max_length: Optional[int] = Field(default=None, description='Optional. If type is `STRING`, `max_length` specifies the maximum length of the string.')
    max_properties: Optional[int] = Field(default=None, description='Optional. If type is `OBJECT`, `max_properties` specifies the maximum number of properties that can be provided.')
    maximum: Optional[float] = Field(default=None, description='Optional. If type is `INTEGER` or `NUMBER`, `maximum` specifies the maximum allowed value.')
    min_items: Optional[int] = Field(default=None, description='Optional. If type is `ARRAY`, `min_items` specifies the minimum number of items in an array.')
    min_length: Optional[int] = Field(default=None, description='Optional. If type is `STRING`, `min_length` specifies the minimum length of the string.')
    min_properties: Optional[int] = Field(default=None, description='Optional. If type is `OBJECT`, `min_properties` specifies the minimum number of properties that can be provided.')
    minimum: Optional[float] = Field(default=None, description='Optional. If type is `INTEGER` or `NUMBER`, `minimum` specifies the minimum allowed value.')
    nullable: Optional[bool] = Field(default=None, description='Optional. Indicates if the value of this field can be null.')
    pattern: Optional[str] = Field(default=None, description='Optional. If type is `STRING`, `pattern` specifies a regular expression that the string must match.')
    properties: Optional[dict[str, 'Schema']] = Field(default=None, description='Optional. If type is `OBJECT`, `properties` is a map of property names to schema definitions for each property of the object.')
    property_ordering: Optional[list[str]] = Field(default=None, description='Optional. Order of properties displayed or used where order matters. This is not a standard field in OpenAPI specification, but can be used to control the order of properties.')
    required: Optional[list[str]] = Field(default=None, description='Optional. If type is `OBJECT`, `required` lists the names of properties that must be present.')
    title: Optional[str] = Field(default=None, description='Optional. Title for the schema.')
    type: Optional[Type] = Field(default=None, description='Optional. Data type of the schema field.')

class ModelSelectionConfig(_common.BaseModel):
    """Config for model selection."""
    feature_selection_preference: Optional[FeatureSelectionPreference] = Field(default=None, description='Options for feature selection preference.')

class ApiKeyConfig(_common.BaseModel):
    """Config for authentication with API key.

  This data type is not supported in Gemini API.
  """
    api_key_secret: Optional[str] = Field(default=None, description='Optional. The name of the SecretManager secret version resource storing the API key. Format: `projects/{project}/secrets/{secrete}/versions/{version}` - If both `api_key_secret` and `api_key_string` are specified, this field takes precedence over `api_key_string`. - If specified, the `secretmanager.versions.access` permission should be granted to Vertex AI Extension Service Agent (https://cloud.google.com/vertex-ai/docs/general/access-control#service-agents) on the specified resource.')
    api_key_string: Optional[str] = Field(default=None, description='Optional. The API key to be used in the request directly.')
    http_element_location: Optional[HttpElementLocation] = Field(default=None, description='Optional. The location of the API key.')
    name: Optional[str] = Field(default=None, description='Optional. The parameter name of the API key. E.g. If the API request is "https://example.com/act?api_key=", "api_key" would be the parameter name.')

class AuthConfigGoogleServiceAccountConfig(_common.BaseModel):
    """Config for Google Service Account Authentication.

  This data type is not supported in Gemini API.
  """
    service_account: Optional[str] = Field(default=None, description='Optional. The service account that the extension execution service runs as. - If the service account is specified, the `iam.serviceAccounts.getAccessToken` permission should be granted to Vertex AI Extension Service Agent (https://cloud.google.com/vertex-ai/docs/general/access-control#service-agents) on the specified service account. - If not specified, the Vertex AI Extension Service Agent will be used to execute the Extension.')

class AuthConfigHttpBasicAuthConfig(_common.BaseModel):
    """Config for HTTP Basic Authentication.

  This data type is not supported in Gemini API.
  """
    credential_secret: Optional[str] = Field(default=None, description='Required. The name of the SecretManager secret version resource storing the base64 encoded credentials. Format: `projects/{project}/secrets/{secrete}/versions/{version}` - If specified, the `secretmanager.versions.access` permission should be granted to Vertex AI Extension Service Agent (https://cloud.google.com/vertex-ai/docs/general/access-control#service-agents) on the specified resource.')

class AuthConfigOauthConfig(_common.BaseModel):
    """Config for user oauth. This data type is not supported in Gemini API."""
    access_token: Optional[str] = Field(default=None, description='Access token for extension endpoint. Only used to propagate token from [[ExecuteExtensionRequest.runtime_auth_config]] at request time.')
    service_account: Optional[str] = Field(default=None, description='The service account used to generate access tokens for executing the Extension. - If the service account is specified, the `iam.serviceAccounts.getAccessToken` permission should be granted to Vertex AI Extension Service Agent (https://cloud.google.com/vertex-ai/docs/general/access-control#service-agents) on the provided service account.')

class AuthConfigOidcConfig(_common.BaseModel):
    """Config for user OIDC auth.

  This data type is not supported in Gemini API.
  """
    id_token: Optional[str] = Field(default=None, description='OpenID Connect formatted ID token for extension endpoint. Only used to propagate token from [[ExecuteExtensionRequest.runtime_auth_config]] at request time.')
    service_account: Optional[str] = Field(default=None, description='The service account used to generate an OpenID Connect (OIDC)-compatible JWT token signed by the Google OIDC Provider (accounts.google.com) for extension endpoint (https://cloud.google.com/iam/docs/create-short-lived-credentials-direct#sa-credentials-oidc). - The audience for the token will be set to the URL in the server url defined in the OpenApi spec. - If the service account is provided, the service account should grant `iam.serviceAccounts.getOpenIdToken` permission to Vertex AI Extension Service Agent (https://cloud.google.com/vertex-ai/docs/general/access-control#service-agents).')

class AuthConfig(_common.BaseModel):
    """The authentication config to access the API."""
    api_key: Optional[str] = Field(default=None, description='The authentication config to access the API. Only API key is supported. This field is not supported in Gemini API.')
    api_key_config: Optional[ApiKeyConfig] = Field(default=None, description='Config for API key auth.')
    auth_type: Optional[AuthType] = Field(default=None, description='Type of auth scheme.')
    google_service_account_config: Optional[AuthConfigGoogleServiceAccountConfig] = Field(default=None, description='Config for Google Service Account auth.')
    http_basic_auth_config: Optional[AuthConfigHttpBasicAuthConfig] = Field(default=None, description='Config for HTTP Basic auth.')
    oauth_config: Optional[AuthConfigOauthConfig] = Field(default=None, description='Config for user oauth.')
    oidc_config: Optional[AuthConfigOidcConfig] = Field(default=None, description='Config for user OIDC auth.')

class GoogleMapsPlaces(_common.BaseModel):
    """Grounding with Google Maps Places data (e.g.

  QueryPlaces). This is the default Google Maps grounding type when no other
  type is specified. This data type is not supported in Gemini API.
  """
    pass

class GoogleMapsRouting(_common.BaseModel):
    """Grounding with Google Maps Routing APIs (ComputeRoutes and SearchAlongRoute).

  This data type is not supported in Gemini API.
  """
    pass

class GoogleMapsGroundingTypes(_common.BaseModel):
    """Defines the types of Google Maps grounding that can be enabled and their configurations.

  This data type is not supported in Gemini API.
  """
    places: Optional[GoogleMapsPlaces] = Field(default=None, description='Optional. Enables grounding with Google Maps Places. This is the default grounding type when no `GroundingTypes` are specified.')
    routing: Optional[GoogleMapsRouting] = Field(default=None, description='Optional. Enables grounding with Google Maps Routing APIs (ComputeRoutes and SearchAlongRoute).')

class GoogleMaps(_common.BaseModel):
    """Tool to retrieve knowledge from Google Maps."""
    auth_config: Optional[AuthConfig] = Field(default=None, description='The authentication config to access the API. Only API key is supported. This field is not supported in Gemini API.')
    enable_widget: Optional[bool] = Field(default=None, description='Deprecated. The Google Maps contextual widget behavior in Grounding with Google Maps is being deprecated; this field is planned for removal and no longer has any effect once removed. Optional. Whether to return a widget context token in the GroundingMetadata of the response.')
    grounding_types: Optional[GoogleMapsGroundingTypes] = Field(default=None, description='Optional. Specifies the types of Google Maps grounding to enable. Defaults to `places` when unset. This field is not supported in Gemini API.')

class ApiAuthApiKeyConfig(_common.BaseModel):
    """The API secret. This data type is not supported in Gemini API."""
    api_key_secret_version: Optional[str] = Field(default=None, description='Required. The SecretManager secret version resource name storing API key. e.g. projects/{project}/secrets/{secret}/versions/{version}')
    api_key_string: Optional[str] = Field(default=None, description='The API key string. Either this or `api_key_secret_version` must be set.')

class ApiAuth(_common.BaseModel):
    """The generic reusable api auth config.

  Deprecated. Please use AuthConfig (google/cloud/aiplatform/master/auth.proto)
  instead. This data type is not supported in Gemini API.
  """
    api_key_config: Optional[ApiAuthApiKeyConfig] = Field(default=None, description='The API secret.')

class ExternalApiElasticSearchParams(_common.BaseModel):
    """The search parameters to use for the ELASTIC_SEARCH spec.

  This data type is not supported in Gemini API.
  """
    index: Optional[str] = Field(default=None, description='The ElasticSearch index to use.')
    num_hits: Optional[int] = Field(default=None, description='Optional. Number of hits (chunks) to request. When specified, it is passed to Elasticsearch as the `num_hits` param.')
    search_template: Optional[str] = Field(default=None, description='The ElasticSearch search template to use.')

class ExternalApiSimpleSearchParams(_common.BaseModel):
    """The search parameters to use for SIMPLE_SEARCH spec.

  This data type is not supported in Gemini API.
  """
    pass

class ExternalApi(_common.BaseModel):
    """Retrieve from data source powered by external API for grounding.

  The external API is not owned by Google, but need to follow the pre-defined
  API spec. This data type is not supported in Gemini API.
  """
    api_auth: Optional[ApiAuth] = Field(default=None, description='The authentication config to access the API. Deprecated. Please use auth_config instead.')
    api_spec: Optional[ApiSpec] = Field(default=None, description='The API spec that the external API implements.')
    auth_config: Optional[AuthConfig] = Field(default=None, description='The authentication config to access the API.')
    elastic_search_params: Optional[ExternalApiElasticSearchParams] = Field(default=None, description='Parameters for the elastic search API.')
    endpoint: Optional[str] = Field(default=None, description='The endpoint of the external API. The system will call the API at this endpoint to retrieve the data for grounding. Example: https://acme.com:443/search')
    simple_search_params: Optional[ExternalApiSimpleSearchParams] = Field(default=None, description='Parameters for the simple search API.')

class VertexAISearchDataStoreSpec(_common.BaseModel):
    """Define data stores within engine to filter on in a search call and configurations for those data stores.

  For more information, see
  https://cloud.google.com/generative-ai-app-builder/docs/reference/rpc/google.cloud.discoveryengine.v1#datastorespec.
  This data type is not supported in Gemini API.
  """
    data_store: Optional[str] = Field(default=None, description='Full resource name of DataStore, such as Format: `projects/{project}/locations/{location}/collections/{collection}/dataStores/{dataStore}`')
    filter: Optional[str] = Field(default=None, description='Optional. Filter specification to filter documents in the data store specified by data_store field. For more information on filtering, see [Filtering](https://cloud.google.com/generative-ai-app-builder/docs/filter-search-metadata)')

class VertexAISearch(_common.BaseModel):
    """Retrieve from Vertex AI Search datastore or engine for grounding.

  datastore and engine are mutually exclusive. See
  https://cloud.google.com/products/agent-builder. This data type is not
  supported in Gemini API.
  """
    data_store_specs: Optional[list[VertexAISearchDataStoreSpec]] = Field(default=None, description='Specifications that define the specific DataStores to be searched, along with configurations for those data stores. This is only considered for Engines with multiple data stores. It should only be set if engine is used.')
    datastore: Optional[str] = Field(default=None, description='Optional. Fully-qualified Vertex AI Search data store resource ID. Format: `projects/{project}/locations/{location}/collections/{collection}/dataStores/{dataStore}`')
    engine: Optional[str] = Field(default=None, description='Optional. Fully-qualified Vertex AI Search engine resource ID. Format: `projects/{project}/locations/{location}/collections/{collection}/engines/{engine}`')
    filter: Optional[str] = Field(default=None, description='Optional. Filter strings to be passed to the search API.')
    max_results: Optional[int] = Field(default=None, description='Optional. Number of search results to return per query. The default value is 10. The maximumm allowed value is 10.')

class VertexRagStoreRagResource(_common.BaseModel):
    """The definition of the Rag resource.

  This data type is not supported in Gemini API.
  """
    rag_corpus: Optional[str] = Field(default=None, description='Optional. RagCorpora resource name. Format: `projects/{project}/locations/{location}/ragCorpora/{rag_corpus}`')
    rag_file_ids: Optional[list[str]] = Field(default=None, description='Optional. rag_file_id. The files should be in the same rag_corpus set in rag_corpus field.')

class RagRetrievalConfigFilter(_common.BaseModel):
    """Config for filters. This data type is not supported in Gemini API."""
    metadata_filter: Optional[str] = Field(default=None, description='Optional. String for metadata filtering.')
    vector_distance_threshold: Optional[float] = Field(default=None, description='Optional. Only returns contexts with vector distance smaller than the threshold.')
    vector_similarity_threshold: Optional[float] = Field(default=None, description='Optional. Only returns contexts with vector similarity larger than the threshold.')

class RagRetrievalConfigHybridSearch(_common.BaseModel):
    """Config for Hybrid Search. This data type is not supported in Gemini API."""
    alpha: Optional[float] = Field(default=None, description='Optional. Alpha value controls the weight between dense and sparse vector search results. The range is [0, 1], while 0 means sparse vector search only and 1 means dense vector search only. The default value is 0.5 which balances sparse and dense vector search equally.')

class RagRetrievalConfigRankingLlmRanker(_common.BaseModel):
    """Config for LlmRanker. This data type is not supported in Gemini API."""
    model_name: Optional[str] = Field(default=None, description='Optional. The model name used for ranking. See [Supported models](https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/inference#supported-models).')

class RagRetrievalConfigRankingRankService(_common.BaseModel):
    """Config for Rank Service. This data type is not supported in Gemini API."""
    model_name: Optional[str] = Field(default=None, description='Optional. The model name of the rank service. Format: `semantic-ranker-512@latest`')

class RagRetrievalConfigRanking(_common.BaseModel):
    """Config for ranking and reranking.

  This data type is not supported in Gemini API.
  """
    llm_ranker: Optional[RagRetrievalConfigRankingLlmRanker] = Field(default=None, description='Optional. Config for LlmRanker.')
    rank_service: Optional[RagRetrievalConfigRankingRankService] = Field(default=None, description='Optional. Config for Rank Service.')

class RagRetrievalConfig(_common.BaseModel):
    """Specifies the context retrieval config.

  This data type is not supported in Gemini API.
  """
    filter: Optional[RagRetrievalConfigFilter] = Field(default=None, description='Optional. Config for filters.')
    hybrid_search: Optional[RagRetrievalConfigHybridSearch] = Field(default=None, description='Optional. Config for Hybrid Search.')
    ranking: Optional[RagRetrievalConfigRanking] = Field(default=None, description='Optional. Config for ranking and reranking.')
    top_k: Optional[int] = Field(default=None, description='Optional. The number of contexts to retrieve.')

class VertexRagStore(_common.BaseModel):
    """Retrieve from Vertex RAG Store for grounding.

  This data type is not supported in Gemini API.
  """
    rag_corpora: Optional[list[str]] = Field(default=None, description='Optional. Deprecated. Please use rag_resources instead.')
    rag_resources: Optional[list[VertexRagStoreRagResource]] = Field(default=None, description='Optional. The representation of the rag source. It can be used to specify corpus only or ragfiles. Currently only support one corpus or multiple files from one corpus. In the future we may open up multiple corpora support.')
    rag_retrieval_config: Optional[RagRetrievalConfig] = Field(default=None, description='Optional. The retrieval config for the Rag query.')
    similarity_top_k: Optional[int] = Field(default=None, description='Optional. Number of top k results to return from the selected corpora.')
    store_context: Optional[bool] = Field(default=None, description="Optional. Currently only supported for Gemini Multimodal Live API. In Gemini Multimodal Live API, if `store_context` bool is specified, Gemini will leverage it to automatically memorize the interactions between the client and Gemini, and retrieve context when needed to augment the response generation for users' ongoing and future interactions.")
    vector_distance_threshold: Optional[float] = Field(default=None, description='Optional. Only return results with vector distance smaller than the threshold.')

class Retrieval(_common.BaseModel):
    """Defines a retrieval tool that model can call to access external knowledge.

  This data type is not supported in Gemini API.
  """
    disable_attribution: Optional[bool] = Field(default=None, description='Optional. Deprecated. This option is no longer supported.')
    external_api: Optional[ExternalApi] = Field(default=None, description='Use data source powered by external API for grounding.')
    vertex_ai_search: Optional[VertexAISearch] = Field(default=None, description='Set to use data source powered by Vertex AI Search.')
    vertex_rag_store: Optional[VertexRagStore] = Field(default=None, description='Set to use data source powered by Vertex RAG store. User data is uploaded via the VertexRagDataService.')

class ComputerUse(_common.BaseModel):
    """A tool that enables the model to interact directly with a computer environment."""
    environment: Optional[Environment] = Field(default=None, description='Required. The target environment where the computer use tool operates.')
    excluded_predefined_functions: Optional[list[str]] = Field(default=None, description='Optional. A list of predefined functions to explicitly exclude from the model call. By default, [predefined functions](https://cloud.google.com/vertex-ai/generative-ai/docs/computer-use#supported-actions) are included. Excluding functions allows for a more restricted action space or custom definitions for predefined functions.')
    enable_prompt_injection_detection: Optional[bool] = Field(default=None, description='Optional. Whether to enable the prompt injection detection check on the computer use request.')
    disabled_safety_policies: Optional[list[SafetyPolicy]] = Field(default=None, description='Optional. A list of safety policies to disable for the computer use tool.')

class FileSearch(_common.BaseModel):
    """The FileSearch tool that retrieves knowledge from Semantic Retrieval corpora.

  Files are imported to Semantic Retrieval corpora using the ImportFile API.
  This data type is not supported in Vertex AI.
  """
    file_search_store_names: Optional[list[str]] = Field(default=None, description='Required. The names of the file_search_stores to retrieve from. Example: `fileSearchStores/my-file-search-store-123`')
    top_k: Optional[int] = Field(default=None, description='Optional. The number of semantic retrieval chunks to retrieve.')
    metadata_filter: Optional[str] = Field(default=None, description='Optional. Metadata filter to apply to the semantic retrieval documents and chunks.')

class WebSearch(_common.BaseModel):
    """Standard web search for grounding and related configurations.

  Only text results are returned.
  """
    pass

class ImageSearch(_common.BaseModel):
    """Image search for grounding and related configurations."""
    pass

class SearchTypes(_common.BaseModel):
    """Different types of search that can be enabled on the GoogleSearch tool."""
    web_search: Optional[WebSearch] = Field(default=None, description='Optional. Setting this field enables web search. Only text results are returned.')
    image_search: Optional[ImageSearch] = Field(default=None, description='Optional. Setting this field enables image search. Image bytes are returned.')

class Interval(_common.BaseModel):
    """Represents a time interval, encoded as a Timestamp start (inclusive) and a Timestamp end (exclusive).

  The start must be less than or equal to the end. When the start equals the
  end, the interval is empty (matches no time). When both start and end are
  unspecified, the interval matches any time.
  """
    end_time: Optional[datetime.datetime] = Field(default=None, description='Optional. Exclusive end of the interval. If specified, a Timestamp matching this interval will have to be before the end.')
    start_time: Optional[datetime.datetime] = Field(default=None, description='Optional. Inclusive start of the interval. If specified, a Timestamp matching this interval will have to be the same or after the start.')

class GoogleSearch(_common.BaseModel):
    """GoogleSearch tool type.

  Tool to support Google Search in Model. Powered by Google.
  """
    search_types: Optional[SearchTypes] = Field(default=None, description='Optional. The set of search types to enable. If not set, web search is enabled by default.')
    blocking_confidence: Optional[PhishBlockThreshold] = Field(default=None, description='Optional. Sites with confidence level chosen & above this value will be blocked from the search results. This field is not supported in Gemini API.')
    exclude_domains: Optional[list[str]] = Field(default=None, description='Optional. List of domains to be excluded from the search results. The default limit is 2000 domains. Example: ["amazon.com", "facebook.com"]. This field is not supported in Gemini API.')
    time_range_filter: Optional[Interval] = Field(default=None, description='Optional. Filter search results to a specific time range. If customers set a start time, they must set an end time (and vice versa). This field is not supported in Vertex AI.')

class ToolCodeExecution(_common.BaseModel):
    """Tool that executes code generated by the model, and automatically returns the result to the model.

  See also ExecutableCode and CodeExecutionResult, which are input and output to
  this tool. This data type is not supported in Gemini API.
  """
    pass

class EnterpriseWebSearch(_common.BaseModel):
    """Tool to search public web data, powered by Vertex AI Search and Sec4 compliance.

  This data type is not supported in Gemini API.
  """
    blocking_confidence: Optional[PhishBlockThreshold] = Field(default=None, description='Optional. Sites with confidence level chosen & above this value will be blocked from the search results.')
    exclude_domains: Optional[list[str]] = Field(default=None, description='Optional. List of domains to be excluded from the search results. The default limit is 2000 domains.')

class FunctionDeclaration(_common.BaseModel):
    """Structured representation of a function declaration as defined by the [OpenAPI 3.0 specification](https://spec.openapis.org/oas/v3.0.3).

  Included in this declaration are the function name, description, parameters
  and response type. This FunctionDeclaration is a representation of a block of
  code that can be used as a `Tool` by the model and executed by the client.
  """
    description: Optional[str] = Field(default=None, description='Optional. Description and purpose of the function. Model uses it to decide how and whether to call the function.')
    name: Optional[str] = Field(default=None, description='Required. The name of the function to call. Must start with a letter or an underscore. Must be a-z, A-Z, 0-9, or contain underscores, dots, colons and dashes, with a maximum length of 128.')
    parameters: Optional[Schema] = Field(default=None, description='Optional. Describes the parameters to this function in JSON Schema Object format. Reflects the Open API 3.03 Parameter Object. string Key: the name of the parameter. Parameter names are case sensitive. Schema Value: the Schema defining the type used for the parameter. For function with no parameters, this can be left unset. Parameter names must start with a letter or an underscore and must only contain chars a-z, A-Z, 0-9, or underscores with a maximum length of 64. Example with 1 required and 1 optional parameter: type: OBJECT properties: param1: type: STRING param2: type: INTEGER required: - param1')
    parameters_json_schema: Optional[Any] = Field(default=None, description='Optional. Describes the parameters to the function in JSON Schema format. The schema must describe an object where the properties are the parameters to the function. For example: ``` { "type": "object", "properties": { "name": { "type": "string" }, "age": { "type": "integer" } }, "additionalProperties": false, "required": ["name", "age"], "propertyOrdering": ["name", "age"] } ``` This field is mutually exclusive with `parameters`.')
    response: Optional[Schema] = Field(default=None, description='Optional. Describes the output from this function in JSON Schema format. Reflects the Open API 3.03 Response Object. The Schema defines the type used for the response value of the function.')
    response_json_schema: Optional[Any] = Field(default=None, description='Optional. Describes the output from this function in JSON Schema format. The value specified by the schema is the response value of the function. This field is mutually exclusive with `response`.')
    behavior: Optional[Behavior] = Field(default=None, description='Optional. Specifies the function Behavior. If not specified, the system keeps the current function call behavior. This field is currently only supported by the BidiGenerateContent method.')

class DynamicRetrievalConfig(_common.BaseModel):
    """Describes the options to customize dynamic retrieval."""
    dynamic_threshold: Optional[float] = Field(default=None, description='Optional. The threshold to be used in dynamic retrieval. If not set, a system default value is used.')
    mode: Optional[DynamicRetrievalConfigMode] = Field(default=None, description='The mode of the predictor to be used in dynamic retrieval.')

class GoogleSearchRetrieval(_common.BaseModel):
    """Tool to retrieve public web data for grounding, powered by Google."""
    dynamic_retrieval_config: Optional[DynamicRetrievalConfig] = Field(default=None, description='Specifies the dynamic retrieval configuration for the given source.')

class ToolParallelAiSearch(_common.BaseModel):
    """ParallelAiSearch tool type.

  A tool that uses the Parallel.ai search engine for grounding. This data type
  is not supported in Gemini API.
  """
    api_key: Optional[str] = Field(default=None, description='Optional. The API key for ParallelAiSearch. If an API key is not provided, the system will attempt to verify access by checking for an active Parallel.ai subscription through the Google Cloud Marketplace. See https://docs.parallel.ai/search/search-quickstart for more details.')
    custom_configs: Optional[dict[str, Any]] = Field(default=None, description='Optional. Custom configs for ParallelAiSearch. This field can be used to pass any parameter from the Parallel.ai Search API. See the Parallel.ai documentation for the full list of available parameters and their usage: https://docs.parallel.ai/api-reference/search-beta/search Currently only `source_policy`, `excerpts`, `max_results`, `mode`, `fetch_policy` can be set via this field. For example: { "source_policy": { "include_domains": ["google.com", "wikipedia.org"], "exclude_domains": ["example.com"] }, "fetch_policy": { "max_age_seconds": 3600 } }')
    enable_data_retention: Optional[bool] = Field(default=None, description='Optional. Deprecated: Use `enable_zero_data_retention` instead. Instructs Vertex Grounding to use Parallel\'s Zero Data Retention Marketplace product. If this value is "false" or omitted, the Parallel Web Search for Grounding standard subscription will be used. If this value is "true", the Parallel Web Search for Grounding - ZDR subscription will be used.')
    enable_zero_data_retention: Optional[bool] = Field(default=None, description='Optional. Instructs Vertex Grounding to use Parallel\'s Zero Data Retention Marketplace product. If this value is "false" or omitted, the Parallel Web Search for Grounding standard subscription will be used. If this value is "true", the Parallel Web Search for Grounding - ZDR subscription will be used.')

class UrlContext(_common.BaseModel):
    """Tool to support URL context."""
    pass

class StreamableHttpTransport(_common.BaseModel):
    """A transport that can stream HTTP requests and responses.

  This data type is not supported in Vertex AI.
  """
    headers: Optional[dict[str, str]] = Field(default=None, description='Optional: Fields for authentication headers, timeouts, etc., if needed.')
    sse_read_timeout: Optional[str] = Field(default=None, description='Timeout for SSE read operations.')
    terminate_on_close: Optional[bool] = Field(default=None, description='Whether to close the client session when the transport closes.')
    timeout: Optional[str] = Field(default=None, description='HTTP timeout for regular operations.')
    url: Optional[str] = Field(default=None, description='The full URL for the MCPServer endpoint. Example: "https://api.example.com/mcp".')

class McpServer(_common.BaseModel):
    """A MCPServer is a server that can be called by the model to perform actions.

  It is a server that implements the MCP protocol. This data type is not
  supported in Vertex AI.
  """
    name: Optional[str] = Field(default=None, description='The name of the MCPServer.')
    streamable_http_transport: Optional[StreamableHttpTransport] = Field(default=None, description='A transport that can stream HTTP requests and responses.')

class ToolExaAiSearch(_common.BaseModel):
    """ExaAiSearch tool type.

  A tool that uses the Exa.ai search engine for grounding. This data type is not
  supported in Gemini API.
  """
    api_key: Optional[str] = Field(default=None, description='Required. The API key for ExaAiSearch.')
    custom_configs: Optional[dict[str, Any]] = Field(default=None, description='Optional. This field can be used to pass any parameter from the Exa.ai Search API.')

class Tool(_common.BaseModel):
    """Tool details of a tool that the model may use to generate a response."""
    retrieval: Optional[Retrieval] = Field(default=None, description='Optional. Retrieval tool type. System will always execute the provided retrieval tool(s) to get external knowledge to answer the prompt. Retrieval results are presented to the model for generation. This field is not supported in Gemini API.')
    computer_use: Optional[ComputerUse] = Field(default=None, description='Optional. Tool to support the model interacting directly with the computer. If enabled, it automatically populates computer-use specific Function Declarations.')
    file_search: Optional[FileSearch] = Field(default=None, description='Optional. FileSearch tool type. Tool to retrieve knowledge from Semantic Retrieval corpora. This field is not supported in Vertex AI.')
    google_search: Optional[GoogleSearch] = Field(default=None, description='Optional. GoogleSearch tool type. Tool to support Google Search in Model. Powered by Google.')
    google_maps: Optional[GoogleMaps] = Field(default=None, description="Optional. Tool that allows grounding the model's response with\n      geospatial context related to the user's query.")
    code_execution: Optional[ToolCodeExecution] = Field(default=None, description='Optional. CodeExecution tool type. Enables the model to execute code as part of generation.')
    enterprise_web_search: Optional[EnterpriseWebSearch] = Field(default=None, description='Optional. Tool to support searching public web data, powered by Vertex AI Search and Sec4 compliance. This field is not supported in Gemini API.')
    function_declarations: Optional[list[FunctionDeclaration]] = Field(default=None, description='Optional. Function tool type. One or more function declarations to be passed to the model along with the current user query. Model may decide to call a subset of these functions by populating FunctionCall in the response. User should provide a FunctionResponse for each function call in the next turn. Based on the function responses, Model will generate the final response back to the user. Maximum 512 function declarations can be provided.')
    google_search_retrieval: Optional[GoogleSearchRetrieval] = Field(default=None, description='Optional. Specialized retrieval tool that is powered by Google Search.')
    parallel_ai_search: Optional[ToolParallelAiSearch] = Field(default=None, description='Optional. If specified, Vertex AI will use Parallel.ai to search for information to answer user queries. The search results will be grounded on Parallel.ai and presented to the model for response generation. This field is not supported in Gemini API.')
    url_context: Optional[UrlContext] = Field(default=None, description='Optional. Tool to support URL context retrieval.')
    mcp_servers: Optional[list[McpServer]] = Field(default=None, description='Optional. MCP Servers to connect to. This field is not supported in Vertex AI.')
    exa_ai_search: Optional[ToolExaAiSearch] = Field(default=None, description='Optional. Uses Exa.ai to search for information to answer user queries. The search results will be grounded on Exa.ai and presented to the model for response generation. This field is not supported in Gemini API.')

def _validate_tool_list(v: object, handler: Any) -> Any:
    if v is None:
        return None
    if not isinstance(v, list):
        return handler(v)
    out = []
    for item in v:
        if isinstance(item, dict):
            out.append(Tool.model_validate(item))
        else:
            out.append(item)
    return out
ToolListUnion = Annotated[list, WrapValidator(_validate_tool_list)]
SchemaUnion = Union[dict[Any, Any], type, Schema, builtin_types.GenericAlias, VersionedUnionType]

class VoiceConsentSignature(_common.BaseModel):
    """The signature of the voice consent check."""
    signature: Optional[str] = Field(default=None, description='The signature string.\n      ')

class ReplicatedVoiceConfig(_common.BaseModel):
    """The configuration for the replicated voice to use."""
    mime_type: Optional[str] = Field(default=None, description='The mimetype of the voice sample. The only currently supported\n      value is `audio/wav`. This represents 16-bit signed little-endian wav\n      data, with a 24kHz sampling rate.\n      ')
    voice_sample_audio: Optional[bytes] = Field(default=None, description='The sample of the custom voice.\n      ')
    consent_audio: Optional[bytes] = Field(default=None, description='Recorded consent verifying ownership of the voice. This\n      represents 16-bit signed little-endian wav data, with a 24kHz sampling\n      rate.')
    voice_consent_signature: Optional[VoiceConsentSignature] = Field(default=None, description='Signature of a previously verified consent audio. This should be\n      populated with a signature generated by the server for a previous\n      request containing the consent_audio field. When provided, the\n      signature is verified instead of the consent_audio field to reduce\n      latency. Requests will fail if the signature is invalid or expired.')

class PrebuiltVoiceConfig(_common.BaseModel):
    """Configuration for a prebuilt voice."""
    voice_name: Optional[str] = Field(default=None, description='The name of the prebuilt voice to use.')

class VoiceConfig(_common.BaseModel):
    """The configuration for the voice to use."""
    replicated_voice_config: Optional[ReplicatedVoiceConfig] = Field(default=None, description="The configuration for a replicated voice, which is a clone of a\n      user's voice that can be used for speech synthesis. If this is unset, a\n      default voice is used.")
    prebuilt_voice_config: Optional[PrebuiltVoiceConfig] = Field(default=None, description='The configuration for a prebuilt voice.')
    voice: Optional[str] = Field(default=None, description='The speaker identifier for synthesis.')

class SpeakerVoiceConfig(_common.BaseModel):
    """Configuration for a single speaker in a multi-speaker setup."""
    speaker: Optional[str] = Field(default=None, description='Required. The name of the speaker. This should be the same as the speaker name used in the prompt.')
    voice_config: Optional[VoiceConfig] = Field(default=None, description='Required. The configuration for the voice of this speaker.')

class MultiSpeakerVoiceConfig(_common.BaseModel):
    """Configuration for a multi-speaker text-to-speech request."""
    speaker_voice_configs: Optional[list[SpeakerVoiceConfig]] = Field(default=None, description='Required. A list of configurations for the voices of the speakers. Exactly two speaker voice configurations must be provided.')

class SpeechConfig(_common.BaseModel):
    """Config for speech generation and transcription."""
    voice_config: Optional[VoiceConfig] = Field(default=None, description='The configuration in case of single-voice output.')
    language_code: Optional[str] = Field(default=None, description='Optional. The language code (ISO 639-1) for the speech synthesis.')
    multi_speaker_voice_config: Optional[MultiSpeakerVoiceConfig] = Field(default=None, description='The configuration for a multi-speaker text-to-speech request. This field is mutually exclusive with `voice_config`.')

class AutomaticFunctionCallingConfig(_common.BaseModel):
    """The configuration for automatic function calling."""
    disable: Optional[bool] = Field(default=None, description='Whether to disable automatic function calling.\n      If not set or set to False, will enable automatic function calling.\n      If set to True, will disable automatic function calling.\n      ')
    maximum_remote_calls: Optional[int] = Field(default=10, description='If automatic function calling is enabled,\n      maximum number of remote calls for automatic function calling.\n      This number should be a positive integer.\n      If not set, SDK will set maximum number of remote calls to 10.\n      ')
    ignore_call_history: Optional[bool] = Field(default=None, description='If automatic function calling is enabled,\n      whether to ignore call history to the response.\n      If not set, SDK will set ignore_call_history to false,\n      and will append the call history to\n      GenerateContentResponse.automatic_function_calling_history.\n      ')

class ThinkingConfig(_common.BaseModel):
    """The thinking features configuration."""
    include_thoughts: Optional[bool] = Field(default=None, description='Indicates whether to include thoughts in the response. If true, thoughts are returned only if the model supports thought and thoughts are available.\n      ')
    thinking_budget: Optional[int] = Field(default=None, description='Indicates the thinking budget in tokens. 0 is DISABLED. -1 is AUTOMATIC. The default values and allowed ranges are model dependent.\n      ')
    thinking_level: Optional[ThinkingLevel] = Field(default=None, description='Optional. The number of thoughts tokens that the model should generate.')

class ImageConfigImageOutputOptions(_common.BaseModel):
    """The image output format for generated images.

  This data type is not supported in Gemini API.
  """
    compression_quality: Optional[int] = Field(default=None, description='Optional. The compression quality of the output image.')
    mime_type: Optional[str] = Field(default=None, description='Optional. The image format that the output should be saved as.')

class ImageConfig(_common.BaseModel):
    """The image generation configuration to be used in GenerateContentConfig."""
    aspect_ratio: Optional[str] = Field(default=None, description='Aspect ratio of the generated images. Supported values are\n      "1:1", "2:3", "3:2", "3:4", "4:3", "9:16", "16:9", and "21:9".')
    image_size: Optional[str] = Field(default=None, description='Optional. Specifies the size of generated images. Supported\n      values are `1K`, `2K`, `4K`. If not specified, the model will use default\n      value `1K`.')
    person_generation: Optional[str] = Field(default=None, description='Controls the generation of people. Supported values are:\n      ALLOW_ALL, ALLOW_ADULT, ALLOW_NONE.')
    prominent_people: Optional[ProminentPeople] = Field(default=None, description='Optional. Controls whether prominent people (celebrities) generation is allowed. If used with personGeneration, personGeneration enum would take precedence. For instance, if ALLOW_NONE is set, all person generation would be blocked. If this field is unspecified, the default behavior is to allow prominent people. This field is not supported in Gemini API.')
    output_mime_type: Optional[str] = Field(default=None, description='MIME type of the generated image. This field is not\n      supported in Gemini API.')
    output_compression_quality: Optional[int] = Field(default=None, description='Compression quality of the generated image (for\n      ``image/jpeg`` only). This field is not supported in Gemini API.')
    image_output_options: Optional[ImageConfigImageOutputOptions] = Field(default=None, description='Optional. The image output format for generated images. This field is not supported in Gemini API.')

class GenerationOutputConfig(_common.BaseModel):
    """Configuration for persisting output assets to external storage."""
    output_uri_prefix: Optional[str] = Field(default=None, description='Optional. The Cloud Storage URI prefix or directory where\n      generated media assets should be written (e.g. "gs://my-bucket/prefix/").\n      Supported URI schemes: "gs://". When set, media bytes are written directly\n      to this location and returned as FileData with a file_uri instead of raw\n      inline bytes.\n      ')

class FileStatus(_common.BaseModel):
    """Status of a File that uses a common error model."""
    details: Optional[list[dict[str, Any]]] = Field(default=None, description='A list of messages that carry the error details. There is a common set of message types for APIs to use.')
    message: Optional[str] = Field(default=None, description='A list of messages that carry the error details. There is a common set of message types for APIs to use.')
    code: Optional[int] = Field(default=None, description='The status code. 0 for OK, 1 for CANCELLED')

class FileStatusDict(TypedDict, total=False):
    """Status of a File that uses a common error model."""
    details: Optional[list[dict[str, Any]]]
    message: Optional[str]
    code: Optional[int]

class File(_common.BaseModel):
    """A file uploaded to the API."""
    name: Optional[str] = Field(default=None, description='The `File` resource name. The ID (name excluding the "files/" prefix) can contain up to 40 characters that are lowercase alphanumeric or dashes (-). The ID cannot start or end with a dash. If the name is empty on create, a unique name will be generated. Example: `files/123-456`')
    display_name: Optional[str] = Field(default=None, description="Optional. The human-readable display name for the `File`. The display name must be no more than 512 characters in length, including spaces. Example: 'Welcome Image'")
    mime_type: Optional[str] = Field(default=None, description='Output only. MIME type of the file.')
    size_bytes: Optional[int] = Field(default=None, description='Output only. Size of the file in bytes.')
    create_time: Optional[datetime.datetime] = Field(default=None, description='Output only. The timestamp of when the `File` was created.')
    expiration_time: Optional[datetime.datetime] = Field(default=None, description='Output only. The timestamp of when the `File` will be deleted. Only set if the `File` is scheduled to expire.')
    update_time: Optional[datetime.datetime] = Field(default=None, description='Output only. The timestamp of when the `File` was last updated.')
    sha256_hash: Optional[str] = Field(default=None, description='Output only. SHA-256 hash of the uploaded bytes. The hash value is encoded in base64 format.')
    uri: Optional[str] = Field(default=None, description='Output only. The URI of the `File`.')
    download_uri: Optional[str] = Field(default=None, description='Output only. The URI of the `File`, only set for downloadable (generated) files.')
    state: Optional[FileState] = Field(default=None, description='Output only. Processing state of the File.')
    source: Optional[FileSource] = Field(default=None, description='Output only. The source of the `File`.')
    video_metadata: Optional[dict[str, Any]] = Field(default=None, description='Output only. Metadata for a video.')
    error: Optional[FileStatus] = Field(default=None, description='Output only. Error status if File processing failed.')

class FileDict(TypedDict, total=False):
    """A file uploaded to the API."""
    name: Optional[str]
    display_name: Optional[str]
    mime_type: Optional[str]
    size_bytes: Optional[int]
    create_time: Optional[datetime.datetime]
    expiration_time: Optional[datetime.datetime]
    update_time: Optional[datetime.datetime]
    sha256_hash: Optional[str]
    uri: Optional[str]
    download_uri: Optional[str]
    state: Optional[FileState]
    source: Optional[FileSource]
    video_metadata: Optional[dict[str, Any]]
    error: Optional[FileStatusDict]
if _is_pillow_image_imported:
    PartUnion = Union[str, PIL_Image, File, Part]
else:
    PartUnion = Union[str, File, Part]
if _is_pillow_image_imported:
    PartUnionDict = Union[str, PIL_Image, File, FileDict, Part, PartDict]
else:
    PartUnionDict = Union[str, File, FileDict, Part, PartDict]
ContentUnion = Union[Content, PartUnion, list[PartUnion]]

class GenerationConfigRoutingConfigAutoRoutingMode(_common.BaseModel):
    """The configuration for automated routing.

  When automated routing is specified, the routing will be determined by the
  pretrained routing model and customer provided model routing preference. This
  data type is not supported in Gemini API.
  """
    model_routing_preference: Optional[Literal['UNKNOWN', 'PRIORITIZE_QUALITY', 'BALANCED', 'PRIORITIZE_COST']] = Field(default=None, description='The model routing preference.')

class GenerationConfigRoutingConfigManualRoutingMode(_common.BaseModel):
    """The configuration for manual routing.

  When manual routing is specified, the model will be selected based on the
  model name provided. This data type is not supported in Gemini API.
  """
    model_name: Optional[str] = Field(default=None, description='The name of the model to use. Only public LLM models are accepted.')

class GenerationConfigRoutingConfig(_common.BaseModel):
    """The configuration for routing the request to a specific model.

  This can be used to control which model is used for the generation, either
  automatically or by specifying a model name. This data type is not supported
  in Gemini API.
  """
    auto_mode: Optional[GenerationConfigRoutingConfigAutoRoutingMode] = Field(default=None, description='In this mode, the model is selected automatically based on the content of the request.')
    manual_mode: Optional[GenerationConfigRoutingConfigManualRoutingMode] = Field(default=None, description='In this mode, the model is specified manually.')

class SafetySetting(_common.BaseModel):
    """A safety setting that affects the safety-blocking behavior.

  A SafetySetting consists of a harm category and a threshold for that category.
  """
    category: Optional[HarmCategory] = Field(default=None, description='Required. The harm category to be blocked.')
    method: Optional[HarmBlockMethod] = Field(default=None, description='Optional. The method for blocking content. If not specified, the default behavior is to use the probability score. This field is not supported in Gemini API.')
    threshold: Optional[HarmBlockThreshold] = Field(default=None, description='Required. The threshold for blocking content. If the harm probability exceeds this threshold, the content will be blocked.')

class LatLng(_common.BaseModel):
    """An object that represents a latitude/longitude pair.

  This is expressed as a pair of doubles to represent degrees latitude and
  degrees longitude. Unless specified otherwise, this object must conform to the
  WGS84 standard. Values must be within normalized ranges.
  """
    latitude: Optional[float] = Field(default=None, description='The latitude in degrees. It must be in the range [-90.0, +90.0].')
    longitude: Optional[float] = Field(default=None, description='The longitude in degrees. It must be in the range [-180.0, +180.0].')

class RetrievalConfig(_common.BaseModel):
    """Retrieval config."""
    lat_lng: Optional[LatLng] = Field(default=None, description='The location of the user.')
    language_code: Optional[str] = Field(default=None, description='The language code of the user.')

class FunctionCallingConfig(_common.BaseModel):
    """Function calling config."""
    allowed_function_names: Optional[list[str]] = Field(default=None, description='Optional. Function names to call. Only set when the Mode is ANY. Function names should match FunctionDeclaration.name. With mode set to ANY, model will predict a function call from the set of function names provided.')
    mode: Optional[FunctionCallingConfigMode] = Field(default=None, description='Optional. Function calling mode.')
    stream_function_call_arguments: Optional[bool] = Field(default=None, description='Optional. When set to true, arguments of a single function call will be streamed out in multiple parts/contents/responses. Partial parameter results will be returned in the `FunctionCall.partial_args` field. This field is not supported in Gemini API.')

class ToolConfig(_common.BaseModel):
    """Tool config.

  This config is shared for all tools provided in the request.
  """
    retrieval_config: Optional[RetrievalConfig] = Field(default=None, description='Optional. Retrieval config.')
    function_calling_config: Optional[FunctionCallingConfig] = Field(default=None, description='Optional. Function calling config.')
    include_server_side_tool_invocations: Optional[bool] = Field(default=None, description="Optional. If true, the API response will include the server-side tool calls and responses within the `Content` message. This allows clients to observe the server's tool interactions. This field is not supported in Vertex AI.")
SpeechConfigUnion = Union[str, SpeechConfig]

class ModelArmorConfig(_common.BaseModel):
    """Configuration for Model Armor.

  Model Armor is a Google Cloud service that provides safety and security
  filtering for prompts and responses. It helps protect your AI applications
  from risks such as harmful content, sensitive data leakage, and prompt
  injection attacks. This data type is not supported in Gemini API.
  """
    prompt_template_name: Optional[str] = Field(default=None, description="Optional. The resource name of the Model Armor template to use for prompt screening. A Model Armor template is a set of customized filters and thresholds that define how Model Armor screens content. If specified, Model Armor will use this template to check the user's prompt for safety and security risks before it is sent to the model. The name must be in the format `projects/{project}/locations/{location}/templates/{template}`.")
    response_template_name: Optional[str] = Field(default=None, description="Optional. The resource name of the Model Armor template to use for response screening. A Model Armor template is a set of customized filters and thresholds that define how Model Armor screens content. If specified, Model Armor will use this template to check the model's response for safety and security risks before it is returned to the user. The name must be in the format `projects/{project}/locations/{location}/templates/{template}`.")

class LanguageAuto(_common.BaseModel):
    """Deprecated: Language auto-detection is now the default when language_codes is omitted."""
    pass

class LanguageHints(_common.BaseModel):
    """Deprecated: Use AudioTranscriptionConfig.language_codes instead."""
    language_codes: Optional[list[str]] = Field(default=None, description='Deprecated. BCP-47 language codes.')

class AudioTranscriptionConfig(_common.BaseModel):
    """The audio transcription configuration in Setup."""
    language_codes: Optional[list[str]] = Field(default=None, description='Optional. BCP-47 language codes providing hints about the languages present in the audio. If omitted or empty, defaults to automatic language detection.')
    language_auto: Optional[LanguageAuto] = Field(default=None, description='Deprecated: Auto-detection is now the default when language_codes is omitted. This field will be removed in a future version.')
    language_hints: Optional[LanguageHints] = Field(default=None, description='Deprecated: Use top-level language_codes instead. This field will be removed in a future version.')
    custom_vocabulary: Optional[list[str]] = Field(default=None, description='A list of custom vocabulary phrases, which biases the ASR model to improve recognition of these specific terms.')
    adaptation_phrases: Optional[list[str]] = Field(default=None, description='Deprecated. A list of phrases used for speech adaptation, which biases the ASR model to improve recognition of these specific terms.')
    word_timestamp: Optional[bool] = Field(default=None, description='Configures word-level timestamp generation.\n      ')
    diarization: Optional[bool] = Field(default=None, description='Configures speaker diarization.\n      ')
    mode: Optional[AudioTranscriptionConfigMode] = Field(default=None, description='Optional. Configures transcription mode. Supported values: `VERBATIM`, `SMART`. If unspecified, defaults to `VERBATIM` transcription. In `SMART` mode, the model performs disfluency removal (eliminating filler words, repetitions, and false starts), light grammatical cleanup, automatic formatting (paragraphs, bullet points, numbered lists), and minor user edits (inline self-corrections). Timestamps and diarization are incompatible with mode `SMART`.')

class GenerateContentConfig(_common.BaseModel):
    """Optional model configuration parameters.

  For more information, see `Content generation parameters
  <https://cloud.google.com/vertex-ai/generative-ai/docs/multimodal/content-generation-parameters>`_.
  """
    http_options: Optional[HttpOptions] = Field(default=None, description='Used to override HTTP request options.')
    should_return_http_response: Optional[bool] = Field(default=None, description=" If true, the raw HTTP response will be returned in the 'sdk_http_response' field.")
    system_instruction: Optional[ContentUnion] = Field(default=None, description='Instructions for the model to steer it toward better performance.\n      For example, "Answer as concisely as possible" or "Don\'t use technical\n      terms in your response".\n      ')
    temperature: Optional[float] = Field(default=None, description='Value that controls the degree of randomness in token selection.\n      Lower temperatures are good for prompts that require a less open-ended or\n      creative response, while higher temperatures can lead to more diverse or\n      creative results.\n      ')
    top_p: Optional[float] = Field(default=None, description='Tokens are selected from the most to least probable until the sum\n      of their probabilities equals this value. Use a lower value for less\n      random responses and a higher value for more random responses.\n      ')
    top_k: Optional[float] = Field(default=None, description='For each token selection step, the ``top_k`` tokens with the\n      highest probabilities are sampled. Then tokens are further filtered based\n      on ``top_p`` with the final token selected using temperature sampling. Use\n      a lower number for less random responses and a higher number for more\n      random responses.\n      ')
    candidate_count: Optional[int] = Field(default=None, description='Number of response variations to return.\n      ')
    max_output_tokens: Optional[int] = Field(default=None, description='Maximum number of tokens that can be generated in the response.\n      ')
    stop_sequences: Optional[list[str]] = Field(default=None, description='List of strings that tells the model to stop generating text if one\n      of the strings is encountered in the response.\n      ')
    response_logprobs: Optional[bool] = Field(default=None, description='Whether to return the log probabilities of the tokens that were\n      chosen by the model at each step.\n      ')
    logprobs: Optional[int] = Field(default=None, description='Number of top candidate tokens to return the log probabilities for\n      at each generation step.\n      ')
    presence_penalty: Optional[float] = Field(default=None, description='Positive values penalize tokens that already appear in the\n      generated text, increasing the probability of generating more diverse\n      content.\n      ')
    frequency_penalty: Optional[float] = Field(default=None, description='Positive values penalize tokens that repeatedly appear in the\n      generated text, increasing the probability of generating more diverse\n      content.\n      ')
    seed: Optional[int] = Field(default=None, description='When ``seed`` is fixed to a specific number, the model makes a best\n      effort to provide the same response for repeated requests. By default, a\n      random number is used.\n      ')
    response_mime_type: Optional[str] = Field(default=None, description='Output response mimetype of the generated candidate text.\n      Supported mimetype:\n        - `text/plain`: (default) Text output.\n        - `application/json`: JSON response in the candidates.\n      The model needs to be prompted to output the appropriate response type,\n      otherwise the behavior is undefined.\n      ')
    response_schema: Optional[SchemaUnion] = Field(default=None, description="The `Schema` object allows the definition of input and output data types.\n      These types can be objects, but also primitives and arrays.\n      Represents a select subset of an [OpenAPI 3.0 schema\n      object](https://spec.openapis.org/oas/v3.0.3#schema).\n      If set, a compatible response_mime_type must also be set.\n      Compatible mimetypes: `application/json`: Schema for JSON response.\n\n      If `response_schema` doesn't process your schema correctly, try using\n      `response_json_schema` instead.\n      ")
    response_json_schema: Optional[Any] = Field(default=None, description='Optional. Output schema of the generated response.\n      This is an alternative to `response_schema` that accepts [JSON\n      Schema](https://json-schema.org/). If set, `response_schema` must be\n      omitted, but `response_mime_type` is required. While the full JSON Schema\n      may be sent, not all features are supported. Specifically, only the\n      following properties are supported: - `$id` - `$defs` - `$ref` - `$anchor`\n      - `type` - `format` - `title` - `description` - `enum` (for strings and\n      numbers) - `items` - `prefixItems` - `minItems` - `maxItems` - `minimum` -\n      `maximum` - `anyOf` - `oneOf` (interpreted the same as `anyOf`) -\n      `properties` - `additionalProperties` - `required` The non-standard\n      `propertyOrdering` property may also be set. Cyclic references are\n      unrolled to a limited degree and, as such, may only be used within\n      non-required properties. (Nullable properties are not sufficient.) If\n      `$ref` is set on a sub-schema, no other properties, except for than those\n      starting as a `$`, may be set.')
    routing_config: Optional[GenerationConfigRoutingConfig] = Field(default=None, description='Configuration for model router requests.\n      ')
    model_selection_config: Optional[ModelSelectionConfig] = Field(default=None, description='Configuration for model selection.\n      ')
    safety_settings: Optional[list[SafetySetting]] = Field(default=None, description='Safety settings in the request to block unsafe content in the\n      response.\n      ')
    tools: Optional[ToolListUnion] = Field(default=None, description='Code that enables the system to interact with external systems to\n      perform an action outside of the knowledge and scope of the model.\n      ')
    tool_config: Optional[ToolConfig] = Field(default=None, description='Associates model output to a specific function call.\n      ')
    labels: Optional[dict[str, str]] = Field(default=None, description='Labels with user-defined metadata for the request.')
    cached_content: Optional[str] = Field(default=None, description='Resource name of a context cache that can be used in subsequent\n      requests.\n      ')
    response_modalities: Optional[list[str]] = Field(default=None, description='The requested modalities of the response. Represents the set of\n      modalities that the model can return.\n      ')
    media_resolution: Optional[MediaResolution] = Field(default=None, description='If specified, the media resolution specified will be used.\n    ')
    speech_config: Optional[SpeechConfigUnion] = Field(default=None, description='The speech generation configuration.\n      ')
    audio_timestamp: Optional[bool] = Field(default=None, description='If enabled, audio timestamp will be included in the request to the\n       model.\n      ')
    automatic_function_calling: Optional[AutomaticFunctionCallingConfig] = Field(default=None, description='The configuration for automatic function calling.\n      ')
    thinking_config: Optional[ThinkingConfig] = Field(default=None, description='The thinking features configuration.\n      ')
    image_config: Optional[ImageConfig] = Field(default=None, description='The image generation configuration.\n      ')
    enable_enhanced_civic_answers: Optional[bool] = Field(default=None, description='Enables enhanced civic answers. It may not be available for all\n      models. This field is not supported in Gemini Enterprise Agent Platform.\n      ')
    model_armor_config: Optional[ModelArmorConfig] = Field(default=None, description='Settings for prompt and response sanitization using the Model Armor\n      service. If supplied, safety_settings must not be supplied.\n      ')
    service_tier: Optional[ServiceTier] = Field(default=None, description='The service tier to use for the request. For example, ServiceTier.FLEX.')
    audio_transcription_config: Optional[AudioTranscriptionConfig] = Field(default=None, description='Optional. Configuration for audio transcription (speech recognition).\n      ')
    continuation_token: Optional[bytes] = Field(default=None, description='An opaque continuation token used to resume generation from a\n      previous response that stopped with `finish_reason` set to\n      `CONTINUATION`.\n      ')
    automatic_continuation: Optional[bool] = Field(default=None, description="Defaults to true. When a response ends with finish reason\n      `CONTINUATION`, the SDK sends the same request again with the response's\n      continuation token until the model finishes. Timeouts, retries and\n      billing apply to each request. Set to false to turn this off.\n      ")
    generation_output_config: Optional[GenerationOutputConfig] = Field(default=None, description='Optional. Configuration for persisting output assets to external\n      storage.\n      ')
    store: Optional[bool] = Field(default=None, description='Configures the logging behavior for a given request. If set, it\n      takes precedence over the project-level logging config. This field is not\n      supported in Gemini Enterprise Agent Platform.\n      ')

    @pydantic.field_validator('response_schema', mode='before')
    @classmethod
    def _convert_literal_to_enum(cls, value: Any) -> Union[Any, EnumMeta]:
        if typing.get_origin(value) is typing.Literal:
            enum_vals = typing.get_args(value)
            if not all((isinstance(arg, str) for arg in enum_vals)):
                raise ValueError(f'Literal type {value} must be a list of strings.')
            return Enum('PlaceholderLiteralEnum', {s: s for s in enum_vals})
        return value

    @pydantic.field_validator('image_config', mode='before')
    @classmethod
    def _check_image_config_type(cls, value: Any) -> Any:
        if isinstance(value, GenerateImagesConfig):
            raise ValueError('image_config must be an instance of ImageConfig or compatible dict.')
        return value
ContentListUnion = Union[ContentUnion, list[ContentUnion], list[Content]]

class _GenerateContentParameters(_common.BaseModel):
    """Config for models.generate_content parameters."""
    model: Optional[str] = Field(default=None, description='ID of the model to use. For a list of models, see `Google models\n    <https://cloud.google.com/vertex-ai/generative-ai/docs/learn/models>`_.')
    contents: Optional[ContentListUnion] = Field(default=None, description='Content of the request.\n      ')
    config: Optional[GenerateContentConfig] = Field(default=None, description='Configuration that contains optional model parameters.\n      ')

class HttpResponse(_common.BaseModel):
    """A wrapper class for the http response."""
    headers: Optional[dict[str, str]] = Field(default=None, description='Used to retain the processed HTTP headers in the response.')
    body: Optional[str] = Field(default=None, description='The raw HTTP response body, in JSON format.')

class GoogleTypeDate(_common.BaseModel):
    """Represents a whole or partial calendar date, such as a birthday.

  The time of day and time zone are either specified elsewhere or are
  insignificant. The date is relative to the Gregorian Calendar. This can
  represent one of the following: * A full date, with non-zero year, month, and
  day values. * A month and day, with a zero year (for example, an anniversary).
  * A year on its own, with a zero month and a zero day. * A year and month,
  with a zero day (for example, a credit card expiration date). Related types: *
  google.type.TimeOfDay * google.type.DateTime * google.protobuf.Timestamp. This
  data type is not supported in Gemini API.
  """
    day: Optional[int] = Field(default=None, description="Day of a month. Must be from 1 to 31 and valid for the year and month, or 0 to specify a year by itself or a year and month where the day isn't significant.")
    month: Optional[int] = Field(default=None, description='Month of a year. Must be from 1 to 12, or 0 to specify a year without a month and day.')
    year: Optional[int] = Field(default=None, description='Year of the date. Must be from 1 to 9999, or 0 to specify a date without a year.')

class Citation(_common.BaseModel):
    """A citation for a piece of generatedcontent.

  This data type is not supported in Gemini API.
  """
    end_index: Optional[int] = Field(default=None, description='Output only. The end index of the citation in the content.')
    license: Optional[str] = Field(default=None, description='Output only. The license of the source of the citation.')
    publication_date: Optional[GoogleTypeDate] = Field(default=None, description='Output only. The publication date of the source of the citation.')
    start_index: Optional[int] = Field(default=None, description='Output only. The start index of the citation in the content.')
    title: Optional[str] = Field(default=None, description='Output only. The title of the source of the citation.')
    uri: Optional[str] = Field(default=None, description='Output only. The URI of the source of the citation.')

class CitationMetadata(_common.BaseModel):
    """Citation information when the model quotes another source."""
    citations: Optional[list[Citation]] = Field(default=None, description='Contains citation information when the model directly quotes, at\n      length, from another source. Can include traditional websites and code\n      repositories.\n      ')

    @model_validator(mode='before')
    @classmethod
    def _rename_citation_sources(cls, data: Any) -> Any:
        if isinstance(data, dict) and 'citationSources' in data:
            data['citations'] = data.pop('citationSources')
        return data
MetricUnion = Union['Metric', 'UnifiedMetric']

class GroundingChunkMapsPlaceAnswerSourcesAuthorAttribution(_common.BaseModel):
    """Author attribution for a photo or review."""
    display_name: Optional[str] = Field(default=None, description='Name of the author of the Photo or Review.')
    photo_uri: Optional[str] = Field(default=None, description='Profile photo URI of the author of the Photo or Review.')
    uri: Optional[str] = Field(default=None, description='URI of the author of the Photo or Review.')

class GroundingChunkMapsPlaceAnswerSourcesReviewSnippet(_common.BaseModel):
    """Encapsulates a review snippet."""
    author_attribution: Optional[GroundingChunkMapsPlaceAnswerSourcesAuthorAttribution] = Field(default=None, description="This review's author.")
    flag_content_uri: Optional[str] = Field(default=None, description='A link where users can flag a problem with the review.')
    google_maps_uri: Optional[str] = Field(default=None, description='A link to show the review on Google Maps.')
    relative_publish_time_description: Optional[str] = Field(default=None, description='A string of formatted recent time, expressing the review time relative to the current time in a form appropriate for the language and country.')
    review: Optional[str] = Field(default=None, description='A reference representing this place review which may be used to look up this place review again.')
    review_id: Optional[str] = Field(default=None, description='Id of the review referencing the place.')
    title: Optional[str] = Field(default=None, description='Title of the review.')

class GroundingChunkMapsPlaceAnswerSources(_common.BaseModel):
    """The sources that were used to generate the place answer.

  This includes review snippets and photos that were used to generate the
  answer, as well as URIs to flag content.
  """
    review_snippet: Optional[list[GroundingChunkMapsPlaceAnswerSourcesReviewSnippet]] = Field(default=None, description='Snippets of reviews that were used to generate the answer.')
    flag_content_uri: Optional[str] = Field(default=None, description='A link where users can flag a problem with the generated answer.')
    review_snippets: Optional[list[GroundingChunkMapsPlaceAnswerSourcesReviewSnippet]] = Field(default=None, description='Snippets of reviews that were used to generate the answer.')

class GroundingChunkMapsRoute(_common.BaseModel):
    """Route information from Google Maps.

  This data type is not supported in Gemini API.
  """
    distance_meters: Optional[int] = Field(default=None, description='The total distance of the route, in meters.')
    duration: Optional[str] = Field(default=None, description='The total duration of the route.')
    encoded_polyline: Optional[str] = Field(default=None, description='An encoded polyline of the route. See https://developers.google.com/maps/documentation/utilities/polylinealgorithm')

class GroundingChunkMaps(_common.BaseModel):
    """A `Maps` chunk is a piece of evidence that comes from Google Maps.

  It contains information about a place, such as its name, address, and reviews.
  This is used to provide the user with rich, location-based information.
  """
    place_answer_sources: Optional[GroundingChunkMapsPlaceAnswerSources] = Field(default=None, description='The sources that were used to generate the place answer.\n\n      This includes review snippets and photos that were used to generate the\n      answer, as well as URIs to flag content.')
    place_id: Optional[str] = Field(default=None, description="This Place's resource name, in `places/{place_id}` format.\n\n      This can be used to look up the place in the Google Maps API.")
    text: Optional[str] = Field(default=None, description='The text of the place answer.')
    title: Optional[str] = Field(default=None, description='The title of the place.')
    uri: Optional[str] = Field(default=None, description='The URI of the place.')
    route: Optional[GroundingChunkMapsRoute] = Field(default=None, description='Output only. Route information.')

class GroundingChunkImage(_common.BaseModel):
    """An `Image` chunk is a piece of evidence that comes from an image search result.

  It contains the URI of the image search result and the URI of the image. This
  is used to provide the user with a link to the source of the information.
  """
    source_uri: Optional[str] = Field(default=None, description='The URI of the image search result page.')
    image_uri: Optional[str] = Field(default=None, description='The URI of the image.')
    title: Optional[str] = Field(default=None, description='The title of the image search result page.')
    domain: Optional[str] = Field(default=None, description='The domain of the image search result page.')

class RagChunkPageSpan(_common.BaseModel):
    """Represents where the chunk starts and ends in the document.

  This data type is not supported in Gemini API.
  """
    first_page: Optional[int] = Field(default=None, description='Page where chunk starts in the document. Inclusive. 1-indexed.')
    last_page: Optional[int] = Field(default=None, description='Page where chunk ends in the document. Inclusive. 1-indexed.')

class RagChunk(_common.BaseModel):
    """A RagChunk includes the content of a chunk of a RagFile, and associated metadata.

  This data type is not supported in Gemini API.
  """
    page_span: Optional[RagChunkPageSpan] = Field(default=None, description='If populated, represents where the chunk starts and ends in the document.')
    text: Optional[str] = Field(default=None, description='The content of the chunk.')
    chunk_id: Optional[str] = Field(default=None, description='The ID of the chunk.')
    file_id: Optional[str] = Field(default=None, description='The ID of the file that the chunk belongs to.')

class GroundingChunkStringList(_common.BaseModel):
    """A list of string values. This data type is not supported in Vertex AI."""
    values: Optional[list[str]] = Field(default=None, description='The string values of the list.')

class GroundingChunkCustomMetadata(_common.BaseModel):
    """User provided metadata about the GroundingFact.

  This data type is not supported in Vertex AI.
  """
    key: Optional[str] = Field(default=None, description='The key of the metadata.')
    numeric_value: Optional[float] = Field(default=None, description='Optional. The numeric value of the metadata. The expected range for this value depends on the specific `key` used.')
    string_list_value: Optional[GroundingChunkStringList] = Field(default=None, description='Optional. A list of string values for the metadata.')
    string_value: Optional[str] = Field(default=None, description='Optional. The string value of the metadata.')

class GroundingChunkRetrievedContext(_common.BaseModel):
    """Context retrieved from a data source to ground the model's response.

  This is used when a retrieval tool fetches information from a user-provided
  corpus or a public dataset.
  """
    document_name: Optional[str] = Field(default=None, description='Output only. The full resource name of the referenced Vertex AI Search document. This is used to identify the specific document that was retrieved. The format is `projects/{project}/locations/{location}/collections/{collection}/dataStores/{data_store}/branches/{branch}/documents/{document}`. This field is not supported in Gemini API.')
    rag_chunk: Optional[RagChunk] = Field(default=None, description='Additional context for a Retrieval-Augmented Generation (RAG) retrieval result. This is populated only when the RAG retrieval tool is used. This field is not supported in Gemini API.')
    text: Optional[str] = Field(default=None, description='The content of the retrieved data source.')
    title: Optional[str] = Field(default=None, description='The title of the retrieved data source.')
    uri: Optional[str] = Field(default=None, description='The URI of the retrieved data source.')
    custom_metadata: Optional[list[GroundingChunkCustomMetadata]] = Field(default=None, description='Optional. User-provided metadata about the retrieved context. This field is not supported in Vertex AI.')
    file_search_store: Optional[str] = Field(default=None, description='Optional. Name of the `FileSearchStore` containing the document. Example: `fileSearchStores/123`. This field is not supported in Vertex AI.')
    page_number: Optional[int] = Field(default=None, description='Optional. Page number of the retrieved context, if applicable. This field is not supported in Vertex AI.')
    media_id: Optional[str] = Field(default=None, description='Optional. The media blob resource name for multimodal file search results. Format: fileSearchStores/{file_search_store_id}/media/{blob_id}. This field is not supported in Vertex AI.')

class GroundingChunkWeb(_common.BaseModel):
    """A `Web` chunk is a piece of evidence that comes from a web page.

  It contains the URI of the web page, the title of the page, and the domain of
  the page. This is used to provide the user with a link to the source of the
  information.
  """
    domain: Optional[str] = Field(default=None, description='The domain of the web page that contains the evidence. This can be used to filter out low-quality sources. This field is not supported in Gemini API.')
    title: Optional[str] = Field(default=None, description='The title of the web page that contains the evidence.')
    uri: Optional[str] = Field(default=None, description='The URI of the web page that contains the evidence.')

class GroundingChunk(_common.BaseModel):
    """A piece of evidence that supports a claim made by the model.

  This is used to show a citation for a claim made by the model. When grounding
  is enabled, the model returns a `GroundingChunk` that contains a reference to
  the source of the information.
  """
    image: Optional[GroundingChunkImage] = Field(default=None, description='A grounding chunk from an image search result. See the `Image` message for details.')
    maps: Optional[GroundingChunkMaps] = Field(default=None, description='A `Maps` chunk is a piece of evidence that comes from Google Maps.\n\n      It contains information about a place, such as its name, address, and\n      reviews. This is used to provide the user with rich, location-based\n      information.')
    retrieved_context: Optional[GroundingChunkRetrievedContext] = Field(default=None, description='A grounding chunk from a data source retrieved by a retrieval tool, such as Vertex AI Search. See the `RetrievedContext` message for details')
    web: Optional[GroundingChunkWeb] = Field(default=None, description='A grounding chunk from a web page, typically from Google Search. See the `Web` message for details.')

class Segment(_common.BaseModel):
    """Segment of the content this support belongs to."""
    start_index: Optional[int] = Field(default=None, description='Output only. Start index in the given Part, measured in bytes.\n\n      Offset from the start of the Part, inclusive, starting at zero.')
    end_index: Optional[int] = Field(default=None, description='Output only. End index in the given Part, measured in bytes.\n\n      Offset from the start of the Part, exclusive, starting at zero.')
    part_index: Optional[int] = Field(default=None, description='Output only. The index of a Part object within its parent\n      Content object.')
    text: Optional[str] = Field(default=None, description='Output only. The text corresponding to the segment from the\n      response.')

class GroundingSupport(_common.BaseModel):
    """Grounding support."""
    confidence_scores: Optional[list[float]] = Field(default=None, description='Confidence score of the support references.\n\n      Ranges from 0 to 1. 1 is the most confident. This list must have the\n      same size as the grounding_chunk_indices.')
    grounding_chunk_indices: Optional[list[int]] = Field(default=None, description="A list of indices (into 'grounding_chunk') specifying the\n      citations associated with the claim. For instance [1,3,4] means that\n      grounding_chunk[1], grounding_chunk[3], grounding_chunk[4] are the\n      retrieved content attributed to the claim.")
    segment: Optional[Segment] = Field(default=None, description='Segment of the content this support belongs to.')
    rendered_parts: Optional[list[int]] = Field(default=None, description='Indices into the `rendered_parts` field of the `GroundingMetadata` message. These indices specify which rendered parts are associated with this support message.')

class RetrievalMetadata(_common.BaseModel):
    """Metadata returned to client when grounding is enabled."""
    google_search_dynamic_retrieval_score: Optional[float] = Field(default=None, description='Optional. Score indicating how likely information from google\n      search could help answer the prompt. The score is in the range [0, 1],\n      where 0 is the least likely and 1 is the most likely. This score is only\n      populated when google search grounding and dynamic retrieval is enabled.\n      It will be compared to the threshold to determine whether to trigger\n      Google search.')

class SearchEntryPoint(_common.BaseModel):
    """The entry point used to search for grounding sources."""
    rendered_content: Optional[str] = Field(default=None, description='Optional. Web content snippet that can be embedded in a web page\n      or an app webview.')
    sdk_blob: Optional[bytes] = Field(default=None, description='Optional. JSON representing array of tuples.')

class GroundingMetadataSourceFlaggingUri(_common.BaseModel):
    """A URI that can be used to flag a place or review for inappropriate content.

  This is populated only when the grounding source is Google Maps. This data
  type is not supported in Gemini API.
  """
    flag_content_uri: Optional[str] = Field(default=None, description='The URI that can be used to flag the content.')
    source_id: Optional[str] = Field(default=None, description='The ID of the place or review.')

class GroundingMetadata(_common.BaseModel):
    """Information for various kinds of grounding."""
    image_search_queries: Optional[list[str]] = Field(default=None, description='Optional. The image search queries that were used to generate the content. This field is populated only when the grounding source is Google Search with the Image Search search_type enabled.')
    grounding_chunks: Optional[list[GroundingChunk]] = Field(default=None, description='A list of supporting references retrieved from the grounding\n      source. This field is populated when the grounding source is Google\n      Search, Vertex AI Search, or Google Maps.\n      ')
    grounding_supports: Optional[list[GroundingSupport]] = Field(default=None, description='List of grounding support.')
    retrieval_metadata: Optional[RetrievalMetadata] = Field(default=None, description='Metadata related to retrieval in the grounding flow.')
    search_entry_point: Optional[SearchEntryPoint] = Field(default=None, description='Optional. Google search entry for the following-up web\n      searches.')
    web_search_queries: Optional[list[str]] = Field(default=None, description='Web search queries for the following-up web search.')
    google_maps_widget_context_token: Optional[str] = Field(default=None, description='Optional. Output only. Deprecated: The Google Maps contextual widget behavior in Grounding with Google Maps is being deprecated; this field is planned for removal and will no longer be populated once removed. A token that can be used to render a Google Maps widget with the contextual data. This field is populated only when the grounding source is Google Maps.')
    retrieval_queries: Optional[list[str]] = Field(default=None, description='Optional. The queries that were executed by the retrieval tools. This field is populated only when the grounding source is a retrieval tool, such as Vertex AI Search. This field is not supported in Gemini API.')
    source_flagging_uris: Optional[list[GroundingMetadataSourceFlaggingUri]] = Field(default=None, description='Optional. Output only. A list of URIs that can be used to flag a place or review for inappropriate content. This field is populated only when the grounding source is Google Maps. This field is not supported in Gemini API.')

class LogprobsResultCandidate(_common.BaseModel):
    """A single token and its associated log probability."""
    log_probability: Optional[float] = Field(default=None, description='The log probability of this token. A higher value indicates that the model was more confident in this token. The log probability can be used to assess the relative likelihood of different tokens and to identify when the model is uncertain.')
    token: Optional[str] = Field(default=None, description="The token's string representation.")
    token_id: Optional[int] = Field(default=None, description="The token's numerical ID. While the `token` field provides the string representation of the token, the `token_id` is the numerical representation that the model uses internally. This can be useful for developers who want to build custom logic based on the model's vocabulary.")

class LogprobsResultTopCandidates(_common.BaseModel):
    """A list of the top candidate tokens and their log probabilities at each decoding step.

  This can be used to see what other tokens the model considered.
  """
    candidates: Optional[list[LogprobsResultCandidate]] = Field(default=None, description='The list of candidate tokens, sorted by log probability in descending order.')

class LogprobsResult(_common.BaseModel):
    """The log probabilities of the tokens generated by the model.

  This is useful for understanding the model's confidence in its predictions and
  for debugging. For example, you can use log probabilities to identify when the
  model is making a less confident prediction or to explore alternative
  responses that the model considered. A low log probability can also indicate
  that the model is "hallucinating" or generating factually incorrect
  information.
  """
    chosen_candidates: Optional[list[LogprobsResultCandidate]] = Field(default=None, description='A list of the chosen candidate tokens at each decoding step. The length of this list is equal to the total number of decoding steps. Note that the chosen candidate might not be in `top_candidates`.')
    top_candidates: Optional[list[LogprobsResultTopCandidates]] = Field(default=None, description='A list of the top candidate tokens at each decoding step. The length of this list is equal to the total number of decoding steps.')
    log_probability_sum: Optional[float] = Field(default=None, description='Sum of log probabilities for all tokens. This field is not supported in Vertex AI.')

class SafetyRating(_common.BaseModel):
    """A safety rating for a piece of content.

  The safety rating contains the harm category and the harm probability level.
  """
    blocked: Optional[bool] = Field(default=None, description='Output only. Indicates whether the content was blocked because of this rating.')
    category: Optional[HarmCategory] = Field(default=None, description='Output only. The harm category of this rating.')
    overwritten_threshold: Optional[HarmBlockThreshold] = Field(default=None, description='Output only. The overwritten threshold for the safety category of Gemini 2.0 image out. If minors are detected in the output image, the threshold of each safety category will be overwritten if user sets a lower threshold. This field is not supported in Gemini API.')
    probability: Optional[HarmProbability] = Field(default=None, description='Output only. The probability of harm for this category.')
    probability_score: Optional[float] = Field(default=None, description='Output only. The probability score of harm for this category. This field is not supported in Gemini API.')
    severity: Optional[HarmSeverity] = Field(default=None, description='Output only. The severity of harm for this category. This field is not supported in Gemini API.')
    severity_score: Optional[float] = Field(default=None, description='Output only. The severity score of harm for this category. This field is not supported in Gemini API.')

class UrlMetadata(_common.BaseModel):
    """The metadata for a single URL retrieval."""
    retrieved_url: Optional[str] = Field(default=None, description='The URL retrieved by the tool.')
    url_retrieval_status: Optional[UrlRetrievalStatus] = Field(default=None, description='The status of the URL retrieval.')

class UrlContextMetadata(_common.BaseModel):
    """Metadata returned when the model uses the `url_context` tool to get information from a user-provided URL."""
    url_metadata: Optional[list[UrlMetadata]] = Field(default=None, description='Output only. A list of URL metadata, with one entry for each URL retrieved by the tool.')

class Candidate(_common.BaseModel):
    """A response candidate generated from the model."""
    content: Optional[Content] = Field(default=None, description='Contains the multi-part content of the response.\n      ')
    citation_metadata: Optional[CitationMetadata] = Field(default=None, description='Source attribution of the generated content.\n      ')
    finish_message: Optional[str] = Field(default=None, description='Describes the reason the model stopped generating tokens.\n      ')
    token_count: Optional[int] = Field(default=None, description='Number of tokens for this candidate.\n      ')
    finish_reason: Optional[FinishReason] = Field(default=None, description='The reason why the model stopped generating tokens.\n      If empty, the model has not stopped generating the tokens.\n      ')
    grounding_metadata: Optional[GroundingMetadata] = Field(default=None, description='Output only. Metadata returned when grounding is enabled. It\n      contains the sources used to ground the generated content.\n      ')
    avg_logprobs: Optional[float] = Field(default=None, description='Output only. The average log probability of the tokens in this candidate. This is a length-normalized score that can be used to compare the quality of candidates of different lengths. A higher average log probability suggests a more confident and coherent response.')
    index: Optional[int] = Field(default=None, description='Output only. The 0-based index of this candidate in the list of generated responses. This is useful for distinguishing between multiple candidates when `candidate_count` > 1.')
    logprobs_result: Optional[LogprobsResult] = Field(default=None, description='Output only. The detailed log probability information for the tokens in this candidate. This is useful for debugging, understanding model uncertainty, and identifying potential "hallucinations".')
    safety_ratings: Optional[list[SafetyRating]] = Field(default=None, description='Output only. A list of ratings for the safety of a response candidate. There is at most one rating per category.')
    url_context_metadata: Optional[UrlContextMetadata] = Field(default=None, description='Output only. Metadata returned when the model uses the `url_context` tool to get information from a user-provided URL.')
    continuation_token: Optional[bytes] = Field(default=None, description='Output only. An optional opaque continuation token returned when `finish_reason` is `CONTINUATION`. Clients can pass this token in a subsequent `GenerateContentRequest` to continue generation.')

class GenerateContentResponsePromptFeedback(_common.BaseModel):
    """Content filter results for a prompt sent in the request.

  Note: This is sent only in the first stream chunk and only if no candidates
  were generated due to content violations.
  """
    block_reason: Optional[BlockedReason] = Field(default=None, description='Output only. The reason why the prompt was blocked.')
    block_reason_message: Optional[str] = Field(default=None, description='Output only. A readable message that explains the reason why the prompt was blocked. This field is not supported in Gemini API.')
    safety_ratings: Optional[list[SafetyRating]] = Field(default=None, description='Output only. A list of safety ratings for the prompt. There is one rating per category.')

class ModalityTokenCount(_common.BaseModel):
    """Represents a breakdown of token usage by modality.

  This message is used in CountTokensResponse and
  GenerateContentResponse.UsageMetadata to provide a detailed view of how many
  tokens are used by each modality (e.g., text, image, video) in a request. This
  is particularly useful for multimodal models, allowing you to track and manage
  token consumption for billing and quota purposes.
  """
    modality: Optional[MediaModality] = Field(default=None, description='The modality that this token count applies to.')
    token_count: Optional[int] = Field(default=None, description='The number of tokens counted for this modality.')

class GenerateContentResponseUsageMetadata(_common.BaseModel):
    """Usage metadata about the content generation request and response.

  This message provides a detailed breakdown of token usage and other relevant
  metrics. This data type is not supported in Gemini API.
  """
    cache_tokens_details: Optional[list[ModalityTokenCount]] = Field(default=None, description='Output only. A detailed breakdown of the token count for each modality in the cached content.')
    cached_content_token_count: Optional[int] = Field(default=None, description='Output only. The number of tokens in the cached content that was used for this request.')
    candidates_token_count: Optional[int] = Field(default=None, description='The total number of tokens in the generated candidates.')
    candidates_tokens_details: Optional[list[ModalityTokenCount]] = Field(default=None, description='Output only. A detailed breakdown of the token count for each modality in the generated candidates.')
    prompt_token_count: Optional[int] = Field(default=None, description='The total number of tokens in the prompt. This includes any text, images, or other media provided in the request. When `cached_content` is set, this also includes the number of tokens in the cached content.')
    prompt_tokens_details: Optional[list[ModalityTokenCount]] = Field(default=None, description='Output only. A detailed breakdown of the token count for each modality in the prompt.')
    thoughts_token_count: Optional[int] = Field(default=None, description='Output only. The number of tokens that were part of the model\'s generated "thoughts" output, if applicable.')
    tool_use_prompt_token_count: Optional[int] = Field(default=None, description='Output only. The number of tokens in the results from tool executions, which are provided back to the model as input, if applicable.')
    tool_use_prompt_tokens_details: Optional[list[ModalityTokenCount]] = Field(default=None, description='Output only. A detailed breakdown by modality of the token counts from the results of tool executions, which are provided back to the model as input.')
    total_token_count: Optional[int] = Field(default=None, description='The total number of tokens for the entire request. This is the sum of `prompt_token_count`, `candidates_token_count`, `tool_use_prompt_token_count`, and `thoughts_token_count`.')
    traffic_type: Optional[TrafficType] = Field(default=None, description='Output only. The traffic type for this request.')
    _initial_prompt_token_count: Optional[int] = pydantic.PrivateAttr(default=None)

class ModelStatus(_common.BaseModel):
    """The status of the underlying model.

  This is used to indicate the stage of the underlying model and the retirement
  time if applicable. This data type is not supported in Vertex AI.
  """
    message: Optional[str] = Field(default=None, description='A message explaining the model status.')
    model_stage: Optional[ModelStage] = Field(default=None, description='The stage of the underlying model.')
    retirement_time: Optional[datetime.datetime] = Field(default=None, description='The time at which the model will be retired.')

class GenerateContentResponse(_common.BaseModel):
    """Response message for PredictionService.GenerateContent."""
    sdk_http_response: Optional[HttpResponse] = Field(default=None, description='Used to retain the full HTTP response.')
    candidates: Optional[list[Candidate]] = Field(default=None, description='Response variations returned by the model.\n      ')
    create_time: Optional[datetime.datetime] = Field(default=None, description='Timestamp when the request is made to the server.\n      ')
    model_version: Optional[str] = Field(default=None, description='Output only. The model version used to generate the response.')
    prompt_feedback: Optional[GenerateContentResponsePromptFeedback] = Field(default=None, description='Output only. Content filter results for a prompt sent in the request. Note: Sent only in the first stream chunk. Only happens when no candidates were generated due to content violations.')
    response_id: Optional[str] = Field(default=None, description='Output only. response_id is used to identify each response. It is the encoding of the event_id.')
    usage_metadata: Optional[GenerateContentResponseUsageMetadata] = Field(default=None, description='Usage metadata about the response(s).')
    model_status: Optional[ModelStatus] = Field(default=None, description='Output only. The current model status of this model. This field is not supported in Vertex AI.')
    automatic_function_calling_history: Optional[list[Content]] = None
    parsed: Optional[Union[pydantic.BaseModel, dict[Any, Any], Enum]] = Field(default=None, description='First candidate from the parsed response if response_schema is provided. Not available for streaming.')

class EmbedContentConfig(_common.BaseModel):
    """Optional parameters for the embed_content method."""
    task_type: Optional[str] = Field(default=None, description='Type of task for which the embedding will be used.\n      ')
    title: Optional[str] = Field(default=None, description='Title for the text. Only applicable when TaskType is\n      `RETRIEVAL_DOCUMENT`.\n      ')
    output_dimensionality: Optional[int] = Field(default=None, description='Reduced dimension for the output embedding. If set,\n      excessive values in the output embedding are truncated from the end.\n      Supported by newer models since 2024 only. You cannot set this value if\n      using the earlier model (`models/embedding-001`).\n      ')
    mime_type: Optional[str] = Field(default=None, description='Gemini Enterprise Agent Platform only. The MIME type of the input.\n      ')
    auto_truncate: Optional[bool] = Field(default=None, description='Gemini Enterprise Agent Platform only. Whether to silently truncate inputs longer than\n      the max sequence length. If this option is set to false, oversized inputs\n      will lead to an INVALID_ARGUMENT error, similar to other text APIs.\n      ')
    document_ocr: Optional[bool] = Field(default=None, description='Gemini Enterprise Agent Platform only. Whether to enable OCR for document content.\n      Only applicable to Gemini Embedding 2 models.\n      ')
    audio_track_extraction: Optional[bool] = Field(default=None, description='Gemini Enterprise Agent Platform only. Whether to extract audio from video content.\n      Only applicable to Gemini Embedding 2 models.\n      ')
    http_options: Optional[HttpOptions] = Field(default=None, description='Used to override HTTP request options.')

class _EmbedContentParametersPrivate(_common.BaseModel):
    """Parameters for the _embed_content method."""
    model: Optional[str] = Field(default=None, description='ID of the model to use. For a list of models, see `Google models\n    <https://cloud.google.com/vertex-ai/generative-ai/docs/learn/models>`_.')
    contents: Optional[ContentListUnion] = Field(default=None, description='The content to embed. Only the `parts.text` fields will be counted.\n      ')
    content: Optional[ContentUnion] = Field(default=None, description='The single content to embed. Only the `parts.text` fields will be counted.\n      ')
    embedding_api_type: Optional[EmbeddingApiType] = Field(default=None, description='The Gemini Enterprise Agent Platform embedding API to use.\n      ')
    config: Optional[EmbedContentConfig] = Field(default=None, description='Configuration that contains optional parameters.\n      ')

class ContentEmbeddingStatistics(_common.BaseModel):
    """Statistics of the input text associated with the result of content embedding."""
    truncated: Optional[bool] = Field(default=None, description='Gemini Enterprise Agent Platform only. If the input text was truncated due to having\n      a length longer than the allowed maximum input.\n      ')
    token_count: Optional[float] = Field(default=None, description='Gemini Enterprise Agent Platform only. Number of tokens of the input text.\n      ')
    tokens_details: Optional[list[ModalityTokenCount]] = Field(default=None, description='Gemini Enterprise Agent Platform only. List of modalities and their token count for the input content.\n      ')

class ContentEmbedding(_common.BaseModel):
    """The embedding generated from an input content."""
    values: Optional[list[float]] = Field(default=None, description='A list of floats representing an embedding.\n      ')
    statistics: Optional[ContentEmbeddingStatistics] = Field(default=None, description='Gemini Enterprise Agent Platform only. Statistics of the input text associated with this\n      embedding.\n      ')

class EmbedContentMetadata(_common.BaseModel):
    """Request-level metadata for the Gemini Enterprise Agent Platform Embed Content API."""
    billable_character_count: Optional[int] = Field(default=None, description='Gemini Enterprise Agent Platform only. The total number of billable characters included\n      in the request.\n      ')

class EmbedContentResponse(_common.BaseModel):
    """Response for the embed_content method."""
    sdk_http_response: Optional[HttpResponse] = Field(default=None, description='Used to retain the full HTTP response.')
    embeddings: Optional[list[ContentEmbedding]] = Field(default=None, description='The embeddings for each request, in the same order as provided in\n      the batch request.\n      ')
    metadata: Optional[EmbedContentMetadata] = Field(default=None, description='Gemini Enterprise Agent Platform only. Metadata about the request.\n      ')

class GenerateImagesConfig(_common.BaseModel):
    """The config for generating an images."""
    http_options: Optional[HttpOptions] = Field(default=None, description='Used to override HTTP request options.')
    output_gcs_uri: Optional[str] = Field(default=None, description='Cloud Storage URI used to store the generated images.')
    negative_prompt: Optional[str] = Field(default=None, description='Description of what to discourage in the generated images.')
    number_of_images: Optional[int] = Field(default=None, description='Number of images to generate.')
    aspect_ratio: Optional[str] = Field(default=None, description='Aspect ratio of the generated images. Supported values are\n      "1:1", "3:4", "4:3", "9:16", and "16:9".')
    guidance_scale: Optional[float] = Field(default=None, description='Controls how much the model adheres to the text prompt. Large\n      values increase output and prompt alignment, but may compromise image\n      quality.')
    seed: Optional[int] = Field(default=None, description='Random seed for image generation. This is not available when\n      ``add_watermark`` is set to true.')
    safety_filter_level: Optional[SafetyFilterLevel] = Field(default=None, description='Filter level for safety filtering.')
    person_generation: Optional[PersonGeneration] = Field(default=None, description='Allows generation of people by the model.')
    include_safety_attributes: Optional[bool] = Field(default=None, description='Whether to report the safety scores of each generated image and\n      the positive prompt in the response.')
    include_rai_reason: Optional[bool] = Field(default=None, description='Whether to include the Responsible AI filter reason if the image\n      is filtered out of the response.')
    language: Optional[ImagePromptLanguage] = Field(default=None, description='Language of the text in the prompt.')
    output_mime_type: Optional[str] = Field(default=None, description='MIME type of the generated image.')
    output_compression_quality: Optional[int] = Field(default=None, description='Compression quality of the generated image (for ``image/jpeg``\n      only).')
    add_watermark: Optional[bool] = Field(default=None, description='Whether to add a watermark to the generated images.')
    labels: Optional[dict[str, str]] = Field(default=None, description='User specified labels to track billing usage.')
    image_size: Optional[str] = Field(default=None, description='The size of the largest dimension of the generated image.\n      Supported sizes are 1K and 2K (not supported for Imagen 3 models).')
    enhance_prompt: Optional[bool] = Field(default=None, description='Whether to use the prompt rewriting logic.')

class _GenerateImagesParameters(_common.BaseModel):
    """The parameters for generating images."""
    model: Optional[str] = Field(default=None, description='ID of the model to use. For a list of models, see `Google models\n    <https://cloud.google.com/vertex-ai/generative-ai/docs/learn/models>`_.')
    prompt: Optional[str] = Field(default=None, description='Text prompt that typically describes the images to output.\n      ')
    config: Optional[GenerateImagesConfig] = Field(default=None, description='Configuration for generating images.\n      ')

class Image(_common.BaseModel):
    """An image."""
    gcs_uri: Optional[str] = Field(default=None, description='The Cloud Storage URI of the image. ``Image`` can contain a value\n      for this field or the ``image_bytes`` field but not both.')
    image_bytes: Optional[bytes] = Field(default=None, description='The image bytes data. ``Image`` can contain a value for this field\n      or the ``gcs_uri`` field but not both.')
    mime_type: Optional[str] = Field(default=None, description='The MIME type of the image.')
    _loaded_image: Optional['PIL_Image'] = None

class SafetyAttributes(_common.BaseModel):
    """Safety attributes of a GeneratedImage or the user-provided prompt."""
    categories: Optional[list[str]] = Field(default=None, description='List of RAI categories.')
    scores: Optional[list[float]] = Field(default=None, description='List of scores of each categories.')
    content_type: Optional[str] = Field(default=None, description='Internal use only.')

class GeneratedImage(_common.BaseModel):
    """An output image."""
    image: Optional[Image] = Field(default=None, description='The output image data.')
    rai_filtered_reason: Optional[str] = Field(default=None, description='Responsible AI filter reason if the image is filtered out of the\n      response.')
    safety_attributes: Optional[SafetyAttributes] = Field(default=None, description='Safety attributes of the image. Lists of RAI categories and their\n      scores of each content.')
    enhanced_prompt: Optional[str] = Field(default=None, description='The rewritten prompt used for the image generation if the prompt\n      enhancer is enabled.')

class GenerateImagesResponse(_common.BaseModel):
    """The output images response."""
    sdk_http_response: Optional[HttpResponse] = Field(default=None, description='Used to retain the full HTTP response.')
    generated_images: Optional[list[GeneratedImage]] = Field(default=None, description='List of generated images.')
    positive_prompt_safety_attributes: Optional[SafetyAttributes] = Field(default=None, description='Safety attributes of the positive prompt. Only populated if\n      ``include_safety_attributes`` is set to True.')

class MaskReferenceConfig(_common.BaseModel):
    """Configuration for a Mask reference image."""
    mask_mode: Optional[MaskReferenceMode] = Field(default=None, description='Prompts the model to generate a mask instead of you needing to\n      provide one (unless MASK_MODE_USER_PROVIDED is used).')
    segmentation_classes: Optional[list[int]] = Field(default=None, description='A list of up to 5 class ids to use for semantic segmentation.\n      Automatically creates an image mask based on specific objects.')
    mask_dilation: Optional[float] = Field(default=None, description='Dilation percentage of the mask provided.\n      Float between 0 and 1.')

class ControlReferenceConfig(_common.BaseModel):
    """Configuration for a Control reference image."""
    control_type: Optional[ControlReferenceType] = Field(default=None, description='The type of control reference image to use.')
    enable_control_image_computation: Optional[bool] = Field(default=None, description='Defaults to False. When set to True, the control image will be\n      computed by the model based on the control type. When set to False,\n      the control image must be provided by the user.')

class StyleReferenceConfig(_common.BaseModel):
    """Configuration for a Style reference image."""
    style_description: Optional[str] = Field(default=None, description='A text description of the style to use for the generated image.')

class SubjectReferenceConfig(_common.BaseModel):
    """Configuration for a Subject reference image."""
    subject_type: Optional[SubjectReferenceType] = Field(default=None, description='The subject type of a subject reference image.')
    subject_description: Optional[str] = Field(default=None, description='Subject description for the image.')

class _ReferenceImageAPI(_common.BaseModel):
    """Private class that represents a Reference image that is sent to API."""
    reference_image: Optional[Image] = Field(default=None, description='The reference image for the editing operation.')
    reference_id: Optional[int] = Field(default=None, description='The id of the reference image.')
    reference_type: Optional[str] = Field(default=None, description='The type of the reference image. Only set by the SDK.')
    mask_image_config: Optional[MaskReferenceConfig] = Field(default=None, description='Configuration for the mask reference image.')
    control_image_config: Optional[ControlReferenceConfig] = Field(default=None, description='Configuration for the control reference image.')
    style_image_config: Optional[StyleReferenceConfig] = Field(default=None, description='Configuration for the style reference image.')
    subject_image_config: Optional[SubjectReferenceConfig] = Field(default=None, description='Configuration for the subject reference image.')

class EditImageConfig(_common.BaseModel):
    """Configuration for editing an image."""
    http_options: Optional[HttpOptions] = Field(default=None, description='Used to override HTTP request options.')
    output_gcs_uri: Optional[str] = Field(default=None, description='Cloud Storage URI used to store the generated images.')
    negative_prompt: Optional[str] = Field(default=None, description='Description of what to discourage in the generated images.')
    number_of_images: Optional[int] = Field(default=None, description='Number of images to generate.')
    aspect_ratio: Optional[str] = Field(default=None, description='Aspect ratio of the generated images. Supported values are\n      "1:1", "3:4", "4:3", "9:16", and "16:9".')
    guidance_scale: Optional[float] = Field(default=None, description='Controls how much the model adheres to the text prompt. Large\n      values increase output and prompt alignment, but may compromise image\n      quality.')
    seed: Optional[int] = Field(default=None, description='Random seed for image generation. This is not available when\n      ``add_watermark`` is set to true.')
    safety_filter_level: Optional[SafetyFilterLevel] = Field(default=None, description='Filter level for safety filtering.')
    person_generation: Optional[PersonGeneration] = Field(default=None, description='Allows generation of people by the model.')
    include_safety_attributes: Optional[bool] = Field(default=None, description='Whether to report the safety scores of each generated image and\n      the positive prompt in the response.')
    include_rai_reason: Optional[bool] = Field(default=None, description='Whether to include the Responsible AI filter reason if the image\n      is filtered out of the response.')
    language: Optional[ImagePromptLanguage] = Field(default=None, description='Language of the text in the prompt.')
    output_mime_type: Optional[str] = Field(default=None, description='MIME type of the generated image.')
    output_compression_quality: Optional[int] = Field(default=None, description='Compression quality of the generated image (for ``image/jpeg``\n      only).')
    add_watermark: Optional[bool] = Field(default=None, description='Whether to add a watermark to the generated images.')
    labels: Optional[dict[str, str]] = Field(default=None, description='User specified labels to track billing usage.')
    edit_mode: Optional[EditMode] = Field(default=None, description='Describes the editing mode for the request.')
    base_steps: Optional[int] = Field(default=None, description='The number of sampling steps. A higher value has better image\n      quality, while a lower value has better latency.')

class _EditImageParameters(_common.BaseModel):
    """Parameters for the request to edit an image."""
    model: Optional[str] = Field(default=None, description='The model to use.')
    prompt: Optional[str] = Field(default=None, description='A text description of the edit to apply to the image.')
    reference_images: Optional[list[_ReferenceImageAPI]] = Field(default=None, description='The reference images for editing.')
    config: Optional[EditImageConfig] = Field(default=None, description='Configuration for editing.')

class EditImageResponse(_common.BaseModel):
    """Response for the request to edit an image."""
    sdk_http_response: Optional[HttpResponse] = Field(default=None, description='Used to retain the full HTTP response.')
    generated_images: Optional[list[GeneratedImage]] = Field(default=None, description='Generated images.')

class _UpscaleImageAPIConfig(_common.BaseModel):
    """Internal API config for UpscaleImage.

  These fields require default values sent to the API which are not intended
  to be modifiable or exposed to users in the SDK method.
  """
    http_options: Optional[HttpOptions] = Field(default=None, description='Used to override HTTP request options.')
    output_gcs_uri: Optional[str] = Field(default=None, description='Cloud Storage URI used to store the generated images.')
    safety_filter_level: Optional[SafetyFilterLevel] = Field(default=None, description='Filter level for safety filtering.')
    person_generation: Optional[PersonGeneration] = Field(default=None, description='Allows generation of people by the model.')
    include_rai_reason: Optional[bool] = Field(default=None, description='Whether to include a reason for filtered-out images in the\n      response.')
    output_mime_type: Optional[str] = Field(default=None, description='The image format that the output should be saved as.')
    output_compression_quality: Optional[int] = Field(default=None, description='The level of compression. Only applicable if the\n      ``output_mime_type`` is ``image/jpeg``.')
    enhance_input_image: Optional[bool] = Field(default=None, description='Whether to add an image enhancing step before upscaling.\n      It is expected to suppress the noise and JPEG compression artifacts\n      from the input image.')
    image_preservation_factor: Optional[float] = Field(default=None, description='With a higher image preservation factor, the original image\n      pixels are more respected. With a lower image preservation factor, the\n      output image will have be more different from the input image, but\n      with finer details and less noise.')
    labels: Optional[dict[str, str]] = Field(default=None, description='User specified labels to track billing usage.')
    number_of_images: Optional[int] = Field(default=None, description='')
    mode: Optional[str] = Field(default=None, description='')

class _UpscaleImageAPIParameters(_common.BaseModel):
    """API parameters for UpscaleImage."""
    model: Optional[str] = Field(default=None, description='The model to use.')
    image: Optional[Image] = Field(default=None, description='The input image to upscale.')
    upscale_factor: Optional[str] = Field(default=None, description='The factor to upscale the image (x2 or x4).')
    config: Optional[_UpscaleImageAPIConfig] = Field(default=None, description='Configuration for upscaling.')

class UpscaleImageResponse(_common.BaseModel):
    sdk_http_response: Optional[HttpResponse] = Field(default=None, description='Used to retain the full HTTP response.')
    generated_images: Optional[list[GeneratedImage]] = Field(default=None, description='Generated images.')

class ProductImage(_common.BaseModel):
    """An image of the product."""
    product_image: Optional[Image] = Field(default=None, description='An image of the product to be recontextualized.')

class RecontextImageSource(_common.BaseModel):
    """A set of source input(s) for image recontextualization."""
    prompt: Optional[str] = Field(default=None, description='A text prompt for guiding the model during image\n      recontextualization. Not supported for Virtual Try-On.')
    person_image: Optional[Image] = Field(default=None, description='Image of the person or subject who will be wearing the\n      product(s).')
    product_images: Optional[list[ProductImage]] = Field(default=None, description='A list of product images.')

class RecontextImageConfig(_common.BaseModel):
    """Configuration for recontextualizing an image."""
    http_options: Optional[HttpOptions] = Field(default=None, description='Used to override HTTP request options.')
    number_of_images: Optional[int] = Field(default=None, description='Number of images to generate.')
    base_steps: Optional[int] = Field(default=None, description='The number of sampling steps. A higher value has better image\n      quality, while a lower value has better latency.')
    output_gcs_uri: Optional[str] = Field(default=None, description='Cloud Storage URI used to store the generated images.')
    seed: Optional[int] = Field(default=None, description='Random seed for image generation.')
    safety_filter_level: Optional[SafetyFilterLevel] = Field(default=None, description='Filter level for safety filtering.')
    person_generation: Optional[PersonGeneration] = Field(default=None, description='Whether allow to generate person images, and restrict to specific\n      ages.')
    add_watermark: Optional[bool] = Field(default=None, description='Whether to add a SynthID watermark to the generated images.')
    output_mime_type: Optional[str] = Field(default=None, description='MIME type of the generated image.')
    output_compression_quality: Optional[int] = Field(default=None, description='Compression quality of the generated image (for ``image/jpeg``\n      only).')
    enhance_prompt: Optional[bool] = Field(default=None, description='Whether to use the prompt rewriting logic.')
    labels: Optional[dict[str, str]] = Field(default=None, description='User specified labels to track billing usage.')

class _RecontextImageParameters(_common.BaseModel):
    """The parameters for recontextualizing an image."""
    model: Optional[str] = Field(default=None, description='ID of the model to use. For a list of models, see `Google models\n    <https://cloud.google.com/vertex-ai/generative-ai/docs/learn/models>`_.')
    source: Optional[RecontextImageSource] = Field(default=None, description='A set of source input(s) for image recontextualization.')
    config: Optional[RecontextImageConfig] = Field(default=None, description='Configuration for image recontextualization.')

class RecontextImageResponse(_common.BaseModel):
    """The output images response."""
    generated_images: Optional[list[GeneratedImage]] = Field(default=None, description='List of generated images.')

class ScribbleImage(_common.BaseModel):
    """An image mask representing a brush scribble."""
    image: Optional[Image] = Field(default=None, description='The brush scribble to guide segmentation. Valid for the interactive mode.')

class SegmentImageSource(_common.BaseModel):
    """A set of source input(s) for image segmentation."""
    prompt: Optional[str] = Field(default=None, description='A text prompt for guiding the model during image segmentation.\n      Required for prompt mode and semantic mode, disallowed for other modes.')
    image: Optional[Image] = Field(default=None, description='The image to be segmented.')
    scribble_image: Optional[ScribbleImage] = Field(default=None, description='The brush scribble to guide segmentation.\n      Required for the interactive mode, disallowed for other modes.')

class SegmentImageConfig(_common.BaseModel):
    """Configuration for segmenting an image."""
    http_options: Optional[HttpOptions] = Field(default=None, description='Used to override HTTP request options.')
    mode: Optional[SegmentMode] = Field(default=None, description='The segmentation mode to use.')
    max_predictions: Optional[int] = Field(default=None, description='The maximum number of predictions to return up to, by top\n      confidence score.')
    confidence_threshold: Optional[float] = Field(default=None, description='The confidence score threshold for the detections as a decimal\n      value. Only predictions with a confidence score higher than this\n      threshold will be returned.')
    mask_dilation: Optional[float] = Field(default=None, description='A decimal value representing how much dilation to apply to the\n      masks. 0 for no dilation. 1.0 means the masked area covers the whole\n      image.')
    binary_color_threshold: Optional[float] = Field(default=None, description='The binary color threshold to apply to the masks. The threshold\n      can be set to a decimal value between 0 and 255 non-inclusive.\n      Set to -1 for no binary color thresholding.')
    labels: Optional[dict[str, str]] = Field(default=None, description='User specified labels to track billing usage.')

class _SegmentImageParameters(_common.BaseModel):
    """The parameters for segmenting an image."""
    model: Optional[str] = Field(default=None, description='ID of the model to use. For a list of models, see `Google models\n    <https://cloud.google.com/vertex-ai/generative-ai/docs/learn/models>`_.')
    source: Optional[SegmentImageSource] = Field(default=None, description='A set of source input(s) for image segmentation.')
    config: Optional[SegmentImageConfig] = Field(default=None, description='Configuration for image segmentation.')

class EntityLabel(_common.BaseModel):
    """An entity representing the segmented area."""
    label: Optional[str] = Field(default=None, description='The label of the segmented entity.')
    score: Optional[float] = Field(default=None, description='The confidence score of the detected label.')

class GeneratedImageMask(_common.BaseModel):
    """A generated image mask."""
    mask: Optional[Image] = Field(default=None, description='The generated image mask.')
    labels: Optional[list[EntityLabel]] = Field(default=None, description='The detected entities on the segmented area.')

class SegmentImageResponse(_common.BaseModel):
    """The output images response."""
    generated_masks: Optional[list[GeneratedImageMask]] = Field(default=None, description='List of generated image masks.\n      ')

class GetModelConfig(_common.BaseModel):
    """Optional parameters for models.get method."""
    http_options: Optional[HttpOptions] = Field(default=None, description='Used to override HTTP request options.')

class _GetModelParameters(_common.BaseModel):
    model: Optional[str] = Field(default=None, description='')
    config: Optional[GetModelConfig] = Field(default=None, description='Optional parameters for the request.')

class Endpoint(_common.BaseModel):
    """An endpoint where you deploy models."""
    name: Optional[str] = Field(default=None, description='Resource name of the endpoint.')
    deployed_model_id: Optional[str] = Field(default=None, description="ID of the model that's deployed to the endpoint.")

class TunedModelInfo(_common.BaseModel):
    """A tuned machine learning model."""
    base_model: Optional[str] = Field(default=None, description='ID of the base model that you want to tune.')
    create_time: Optional[datetime.datetime] = Field(default=None, description='Date and time when the base model was created.')
    update_time: Optional[datetime.datetime] = Field(default=None, description='Date and time when the base model was last updated.')

class Checkpoint(_common.BaseModel):
    """Describes the machine learning model version checkpoint."""
    checkpoint_id: Optional[str] = Field(default=None, description='The ID of the checkpoint.\n      ')
    epoch: Optional[int] = Field(default=None, description='The epoch of the checkpoint.\n      ')
    step: Optional[int] = Field(default=None, description='The step of the checkpoint.\n      ')

class Model(_common.BaseModel):
    """A trained machine learning model."""
    name: Optional[str] = Field(default=None, description='Resource name of the model.')
    display_name: Optional[str] = Field(default=None, description='Display name of the model.')
    description: Optional[str] = Field(default=None, description='Description of the model.')
    version: Optional[str] = Field(default=None, description='Version ID of the model. A new version is committed when a new\n      model version is uploaded or trained under an existing model ID. The\n      version ID is an auto-incrementing decimal number in string\n      representation.')
    endpoints: Optional[list[Endpoint]] = Field(default=None, description='List of deployed models created from this base model. Note that a\n      model could have been deployed to endpoints in different locations.')
    labels: Optional[dict[str, str]] = Field(default=None, description='Labels with user-defined metadata to organize your models.')
    tuned_model_info: Optional[TunedModelInfo] = Field(default=None, description='Information about the tuned model from the base model.')
    input_token_limit: Optional[int] = Field(default=None, description='The maximum number of input tokens that the model can handle.')
    output_token_limit: Optional[int] = Field(default=None, description='The maximum number of output tokens that the model can generate.')
    supported_actions: Optional[list[str]] = Field(default=None, description='List of actions that are supported by the model.')
    default_checkpoint_id: Optional[str] = Field(default=None, description='The default checkpoint id of a model version.\n      ')
    checkpoints: Optional[list[Checkpoint]] = Field(default=None, description='The checkpoints of the model.')
    temperature: Optional[float] = Field(default=None, description='Temperature value used for sampling set when the dataset was saved.\n      This value is used to tune the degree of randomness.')
    max_temperature: Optional[float] = Field(default=None, description='The maximum temperature value used for sampling set when the\n      dataset was saved. This value is used to tune the degree of randomness.')
    top_p: Optional[float] = Field(default=None, description="Optional. Specifies the nucleus sampling threshold. The model\n      considers only the smallest set of tokens whose cumulative probability is\n      at least `top_p`. This helps generate more diverse and less repetitive\n      responses. For example, a `top_p` of 0.9 means the model considers tokens\n      until the cumulative probability of the tokens to select from reaches 0.9.\n      It's recommended to adjust either temperature or `top_p`, but not both.")
    top_k: Optional[int] = Field(default=None, description='Optional. Specifies the top-k sampling threshold. The model\n      considers only the top k most probable tokens for the next token. This can\n      be useful for generating more coherent and less random text. For example,\n      a `top_k` of 40 means the model will choose the next word from the 40 most\n      likely words.')
    thinking: Optional[bool] = Field(default=None, description='Whether the model supports thinking features. If true, thoughts are\n      returned only if the model supports thought and thoughts are available.')

class ListModelsConfig(_common.BaseModel):
    http_options: Optional[HttpOptions] = Field(default=None, description='Used to override HTTP request options.')
    page_size: Optional[int] = Field(default=None, description='')
    page_token: Optional[str] = Field(default=None, description='')
    filter: Optional[str] = Field(default=None, description='')
    query_base: Optional[bool] = Field(default=None, description='Set true to list base models, false to list tuned models.')

class _ListModelsParameters(_common.BaseModel):
    config: Optional[ListModelsConfig] = Field(default=None, description='')

class ListModelsResponse(_common.BaseModel):
    sdk_http_response: Optional[HttpResponse] = Field(default=None, description='Used to retain the full HTTP response.')
    next_page_token: Optional[str] = Field(default=None, description='')
    models: Optional[list[Model]] = Field(default=None, description='')

class UpdateModelConfig(_common.BaseModel):
    """Configuration for updating a tuned model."""
    http_options: Optional[HttpOptions] = Field(default=None, description='Used to override HTTP request options.')
    display_name: Optional[str] = Field(default=None, description='')
    description: Optional[str] = Field(default=None, description='')
    default_checkpoint_id: Optional[str] = Field(default=None, description='')

class _UpdateModelParameters(_common.BaseModel):
    """Configuration for updating a tuned model."""
    model: Optional[str] = Field(default=None, description='')
    config: Optional[UpdateModelConfig] = Field(default=None, description='')

class DeleteModelConfig(_common.BaseModel):
    """Configuration for deleting a tuned model."""
    http_options: Optional[HttpOptions] = Field(default=None, description='Used to override HTTP request options.')

class _DeleteModelParameters(_common.BaseModel):
    """Parameters for deleting a tuned model."""
    model: Optional[str] = Field(default=None, description='')
    config: Optional[DeleteModelConfig] = Field(default=None, description='Optional parameters for the request.')

class DeleteModelResponse(_common.BaseModel):
    sdk_http_response: Optional[HttpResponse] = Field(default=None, description='Used to retain the full HTTP response.')

class AudioResponseFormat(_common.BaseModel):
    """Configuration for audio-specific output formatting."""
    bit_rate: Optional[int] = Field(default=None, description='Optional. Bit rate in bits per second (bps). Only applicable for compressed formats (MP3, Opus).')
    delivery: Optional[Delivery] = Field(default=None, description='Optional. Delivery mode for the generated content.')
    mime_type: Optional[str] = Field(default=None, description='Optional. The MIME type of the audio output.')
    sample_rate: Optional[int] = Field(default=None, description='Optional. Sample rate for the generated audio in Hertz.')

class ImageResponseFormat(_common.BaseModel):
    """Configuration for image-specific output formatting."""
    aspect_ratio: Optional[AspectRatio] = Field(default=None, description='Optional. The aspect ratio for the image output.')
    delivery: Optional[Delivery] = Field(default=None, description='Optional. Delivery mode for the generated content.')
    image_size: Optional[ImageSize] = Field(default=None, description='Optional. The size of the image output.')
    mime_type: Optional[str] = Field(default=None, description='Optional. The MIME type of the image output.')

class TextResponseFormat(_common.BaseModel):
    """Configuration for text-specific output formatting."""
    mime_type: Optional[str] = Field(default=None, description='Optional. The IANA standard MIME type of the response.')
    jsonSchema: Optional[Any] = Field(alias='schema', default=None, description='Optional. The JSON schema that the output should conform to. Only applicable when mime_type is APPLICATION_JSON.')

class VideoResponseFormat(_common.BaseModel):
    """Configuration for video-specific output formatting.

  This data type is not supported in Gemini API.
  """
    aspect_ratio: Optional[AspectRatio] = Field(default=None, description='The aspect ratio for the video output.')
    delivery: Optional[Delivery] = Field(default=None, description='Optional. Delivery mode for the generated content.')
    duration: Optional[str] = Field(default=None, description='Optional. The duration for the video output.')
    gcs_uri: Optional[str] = Field(default=None, description='Optional. The Google Cloud Storage URI to store the video output. Required for Vertex if delivery is URI.')
    resolution: Optional[str] = Field(default=None, description='Optional. The video output resolution. Supported values: "360p", "720p", "1080p", "4k".')

class ResponseFormat(_common.BaseModel):
    """Configuration for the model to configure output formatting and delivery.

  This data type is not supported in Gemini API.
  """
    audio: Optional[AudioResponseFormat] = Field(default=None, description='Audio output format.')
    image: Optional[ImageResponseFormat] = Field(default=None, description='Image output format.')
    text: Optional[TextResponseFormat] = Field(default=None, description='Text output format.')
    video: Optional[VideoResponseFormat] = Field(default=None, description='Video output format.')

class TranslationConfig(_common.BaseModel):
    """Config for stream translation."""
    echo_target_language: Optional[bool] = Field(default=None, description='If true, the model will generate audio when the target language is spoken, essentially it will parrot the input. If false, we will not produce audio for the target language.')
    target_language_code: Optional[str] = Field(default=None, description='The target language for translation. Supported values are BCP-47 language codes (e.g. "en", "es", "fr").')

class GenerationConfig(_common.BaseModel):
    """Generation config."""
    model_selection_config: Optional[ModelSelectionConfig] = Field(default=None, description='Optional. Config for model selection.')
    response_json_schema: Optional[Any] = Field(default=None, description='Output schema of the generated response. This is an alternative to\n      `response_schema` that accepts [JSON Schema](https://json-schema.org/).\n      ')
    audio_timestamp: Optional[bool] = Field(default=None, description='Optional. If enabled, audio timestamps will be included in the request to the model. This can be useful for synchronizing audio with other modalities in the response. This field is not supported in Gemini API.')
    candidate_count: Optional[int] = Field(default=None, description='Optional. The number of candidate responses to generate. A higher `candidate_count` can provide more options to choose from, but it also consumes more resources. This can be useful for generating a variety of responses and selecting the best one.')
    enable_affective_dialog: Optional[bool] = Field(default=None, description='Optional. If enabled, the model will detect emotions and adapt its responses accordingly. For example, if the model detects that the user is frustrated, it may provide a more empathetic response.')
    frequency_penalty: Optional[float] = Field(default=None, description='Optional. Penalizes tokens based on their frequency in the generated text. A positive value helps to reduce the repetition of words and phrases. Valid values can range from [-2.0, 2.0].')
    logprobs: Optional[int] = Field(default=None, description='Optional. The number of top log probabilities to return for each token. This can be used to see which other tokens were considered likely candidates for a given position. A higher value will return more options, but it will also increase the size of the response.')
    max_output_tokens: Optional[int] = Field(default=None, description='Optional. The maximum number of tokens to generate in the response. A token is approximately four characters. The default value varies by model. This parameter can be used to control the length of the generated text and prevent overly long responses.')
    media_resolution: Optional[MediaResolution] = Field(default=None, description='Optional. The token resolution at which input media content is sampled. This is used to control the trade-off between the quality of the response and the number of tokens used to represent the media. A higher resolution allows the model to perceive more detail, which can lead to a more nuanced response, but it will also use more tokens. This does not affect the image dimensions sent to the model.')
    presence_penalty: Optional[float] = Field(default=None, description='Optional. Penalizes tokens that have already appeared in the generated text. A positive value encourages the model to generate more diverse and less repetitive text. Valid values can range from [-2.0, 2.0].')
    response_logprobs: Optional[bool] = Field(default=None, description="Optional. If set to true, the log probabilities of the output tokens are returned. Log probabilities are the logarithm of the probability of a token appearing in the output. A higher log probability means the token is more likely to be generated. This can be useful for analyzing the model's confidence in its own output and for debugging.")
    response_mime_type: Optional[str] = Field(default=None, description="Optional. The IANA standard MIME type of the response. The model will generate output that conforms to this MIME type. Supported values include 'text/plain' (default) and 'application/json'. The model needs to be prompted to output the appropriate response type, otherwise the behavior is undefined. Deprecated: Use `response_format` instead.")
    response_modalities: Optional[list[Modality]] = Field(default=None, description='Optional. The modalities of the response. The model will generate a response that includes all the specified modalities. For example, if this is set to `[TEXT, IMAGE]`, the response will include both text and an image.')
    response_schema: Optional[Schema] = Field(default=None, description="Optional. Lets you to specify a schema for the model's response, ensuring that the output conforms to a particular structure. This is useful for generating structured data such as JSON. The schema is a subset of the [OpenAPI 3.0 schema object](https://spec.openapis.org/oas/v3.0.3#schema) object. When this field is set, you must also set the `response_mime_type` to `application/json`. Deprecated: Use `response_format` instead.")
    routing_config: Optional[GenerationConfigRoutingConfig] = Field(default=None, description='Optional. Routing configuration. This field is not supported in Gemini API.')
    seed: Optional[int] = Field(default=None, description='Optional. A seed for the random number generator. By setting a seed, you can make the model\'s output mostly deterministic. For a given prompt and parameters (like temperature, top_p, etc.), the model will produce the same response every time. However, it\'s not a guaranteed absolute deterministic behavior. This is different from parameters like `temperature`, which control the *level* of randomness. `seed` ensures that the "random" choices the model makes are the same on every run, making it essential for testing and ensuring reproducible results.')
    speech_config: Optional[SpeechConfig] = Field(default=None, description='Optional. The speech generation config.')
    stop_sequences: Optional[list[str]] = Field(default=None, description='Optional. A list of character sequences that will stop the model from generating further tokens. If a stop sequence is generated, the output will end at that point. This is useful for controlling the length and structure of the output. For example, you can use ["\n", "###"] to stop generation at a new line or a specific marker.')
    temperature: Optional[float] = Field(default=None, description='Optional. Controls the randomness of the output. A higher temperature results in more creative and diverse responses, while a lower temperature makes the output more predictable and focused. The valid range is (0.0, 2.0].')
    thinking_config: Optional[ThinkingConfig] = Field(default=None, description="Optional. Configuration for thinking features. An error will be returned if this field is set for models that don't support thinking.")
    top_k: Optional[float] = Field(default=None, description='Optional. Specifies the top-k sampling threshold. The model considers only the top k most probable tokens for the next token. This can be useful for generating more coherent and less random text. For example, a `top_k` of 40 means the model will choose the next word from the 40 most likely words.')
    top_p: Optional[float] = Field(default=None, description="Optional. Specifies the nucleus sampling threshold. The model considers only the smallest set of tokens whose cumulative probability is at least `top_p`. This helps generate more diverse and less repetitive responses. For example, a `top_p` of 0.9 means the model considers tokens until the cumulative probability of the tokens to select from reaches 0.9. It's recommended to adjust either temperature or `top_p`, but not both.")
    enable_enhanced_civic_answers: Optional[bool] = Field(default=None, description='Optional. Enables enhanced civic answers. It may not be available for all models. This field is not supported in Vertex AI.')
    response_format: Optional[list[ResponseFormat]] = Field(default=None, description='Optional. New response format field for the model to configure output formatting and delivery.')
    translation_config: Optional[TranslationConfig] = Field(default=None, description='Optional. Config for translation.')
    audio_transcription_config: Optional[AudioTranscriptionConfig] = Field(default=None, description='Optional. Configuration for audio transcription (speech recognition).\n      ')

class CountTokensConfig(_common.BaseModel):
    """Config for the count_tokens method."""
    http_options: Optional[HttpOptions] = Field(default=None, description='Used to override HTTP request options.')
    system_instruction: Optional[ContentUnion] = Field(default=None, description='Instructions for the model to steer it toward better performance.\n      ')
    tools: Optional[list[Tool]] = Field(default=None, description='Code that enables the system to interact with external systems to\n      perform an action outside of the knowledge and scope of the model.\n      ')
    generation_config: Optional[GenerationConfig] = Field(default=None, description='Configuration that the model uses to generate the response. Not\n      supported by the Gemini Developer API.\n      ')

class _CountTokensParameters(_common.BaseModel):
    """Parameters for counting tokens."""
    model: Optional[str] = Field(default=None, description='ID of the model to use. For a list of models, see `Google models\n    <https://cloud.google.com/vertex-ai/generative-ai/docs/learn/models>`_.')
    contents: Optional[ContentListUnion] = Field(default=None, description='Input content.')
    config: Optional[CountTokensConfig] = Field(default=None, description='Configuration for counting tokens.')

class CountTokensResponse(_common.BaseModel):
    """Response for counting tokens."""
    sdk_http_response: Optional[HttpResponse] = Field(default=None, description='Used to retain the full HTTP response.')
    total_tokens: Optional[int] = Field(default=None, description='Total number of tokens.')
    cached_content_token_count: Optional[int] = Field(default=None, description='Number of tokens in the cached part of the prompt (the cached content).')

class ComputeTokensConfig(_common.BaseModel):
    """Optional parameters for computing tokens."""
    http_options: Optional[HttpOptions] = Field(default=None, description='Used to override HTTP request options.')

class _ComputeTokensParameters(_common.BaseModel):
    """Parameters for computing tokens."""
    model: Optional[str] = Field(default=None, description='ID of the model to use. For a list of models, see `Google models\n    <https://cloud.google.com/vertex-ai/generative-ai/docs/learn/models>`_.')
    contents: Optional[ContentListUnion] = Field(default=None, description='Input content.')
    config: Optional[ComputeTokensConfig] = Field(default=None, description='Optional parameters for the request.\n      ')

class TokensInfo(_common.BaseModel):
    """Tokens info with a list of tokens and the corresponding list of token ids."""
    role: Optional[str] = Field(default=None, description='Optional fields for the role from the corresponding Content.')
    token_ids: Optional[list[int]] = Field(default=None, description='A list of token ids from the input.')
    tokens: Optional[list[bytes]] = Field(default=None, description='A list of tokens from the input.')

class ComputeTokensResponse(_common.BaseModel):
    """Response for computing tokens."""
    sdk_http_response: Optional[HttpResponse] = Field(default=None, description='Used to retain the full HTTP response.')
    tokens_info: Optional[list[TokensInfo]] = Field(default=None, description='Lists of tokens info from the input. A ComputeTokensRequest could have multiple instances with a prompt in each instance. We also need to return lists of tokens info for the request with multiple instances.')

class Video(_common.BaseModel):
    """A generated video."""
    uri: Optional[str] = Field(default=None, description='Path to another storage.')
    video_bytes: Optional[bytes] = Field(default=None, description='Video bytes.')
    mime_type: Optional[str] = Field(default=None, description='Video encoding, for example ``video/mp4``.')

class GenerateVideosSource(_common.BaseModel):
    """A set of source input(s) for video generation."""
    prompt: Optional[str] = Field(default=None, description='The text prompt for generating the videos.\n      Optional if image or video is provided.')
    image: Optional[Image] = Field(default=None, description='The input image for generating the videos.\n      Optional if prompt is provided. Not allowed if video is provided.')
    video: Optional[Video] = Field(default=None, description='The input video for video extension use cases.\n      Optional if prompt is provided. Not allowed if image is provided.')

class VideoGenerationReferenceImage(_common.BaseModel):
    """A reference image for video generation."""
    image: Optional[Image] = Field(default=None, description='The reference image.')
    reference_type: Optional[VideoGenerationReferenceType] = Field(default=None, description='The type of the reference image, which defines how the reference\n      image will be used to generate the video.')

class VideoGenerationMask(_common.BaseModel):
    """A mask for video generation."""
    image: Optional[Image] = Field(default=None, description='The image mask to use for generating videos.')
    mask_mode: Optional[VideoGenerationMaskMode] = Field(default=None, description='Describes how the mask will be used. Inpainting masks must\n      match the aspect ratio of the input video. Outpainting masks can be\n      either 9:16 or 16:9.')

class WebhookConfig(_common.BaseModel):
    """Configuration for webhook notifications.

  Used to configure webhook endpoints that will receive notifications
  when long-running operations (e.g., batch jobs, video generation) complete.
  """
    uris: Optional[list[str]] = Field(default=None, description='The webhook URIs to receive notifications. If set, these\n      webhook URIs will be used instead of the registered webhooks.')
    user_metadata: Optional[dict[str, Any]] = Field(default=None, description='User metadata that will be included in each webhook event\n      notification. Use this to attach custom key-value data to correlate\n      webhook events with your internal systems.')

class GenerateVideosConfig(_common.BaseModel):
    """Configuration for generating videos."""
    http_options: Optional[HttpOptions] = Field(default=None, description='Used to override HTTP request options.')
    number_of_videos: Optional[int] = Field(default=None, description='Number of output videos.')
    output_gcs_uri: Optional[str] = Field(default=None, description='The gcs bucket where to save the generated videos.')
    fps: Optional[int] = Field(default=None, description='Frames per second for video generation.')
    duration_seconds: Optional[int] = Field(default=None, description='Duration of the clip for video generation in seconds.')
    seed: Optional[int] = Field(default=None, description='The RNG seed. If RNG seed is exactly same for each request with\n      unchanged inputs, the prediction results will be consistent. Otherwise,\n      a random RNG seed will be used each time to produce a different\n      result.')
    aspect_ratio: Optional[str] = Field(default=None, description='The aspect ratio for the generated video. 16:9 (landscape) and\n      9:16 (portrait) are supported.')
    resolution: Optional[str] = Field(default=None, description='The resolution for the generated video. 720p and 1080p are\n      supported.')
    person_generation: Optional[str] = Field(default=None, description='Whether allow to generate person videos, and restrict to specific\n      ages. Supported values are: dont_allow, allow_adult.')
    pubsub_topic: Optional[str] = Field(default=None, description='The pubsub topic where to publish the video generation\n      progress.')
    negative_prompt: Optional[str] = Field(default=None, description='Explicitly state what should not be included in the generated\n      videos.')
    enhance_prompt: Optional[bool] = Field(default=None, description='Whether to use the prompt rewriting logic.')
    generate_audio: Optional[bool] = Field(default=None, description='Whether to generate audio along with the video.')
    last_frame: Optional[Image] = Field(default=None, description='Image to use as the last frame of generated videos.\n      Only supported for image to video use cases.')
    reference_images: Optional[list[VideoGenerationReferenceImage]] = Field(default=None, description='The images to use as the references to generate the videos.\n      If this field is provided, the text prompt field must also be provided.\n      The image, video, or last_frame field are not supported. Each image must\n      be associated with a type. Veo 2 supports up to 3 asset images *or* 1\n      style image.')
    mask: Optional[VideoGenerationMask] = Field(default=None, description='The mask to use for generating videos.')
    compression_quality: Optional[VideoCompressionQuality] = Field(default=None, description='Compression quality of the generated videos.')
    labels: Optional[dict[str, str]] = Field(default=None, description='User specified labels to track billing usage.')
    webhook_config: Optional[WebhookConfig] = Field(default=None, description='Webhook configuration for receiving notifications when the\n      video generation operation completes.')
    resize_mode: Optional[ImageResizeMode] = Field(default=None, description='Resize mode of the image input for video generation.')

class _GenerateVideosParameters(_common.BaseModel):
    """Class that represents the parameters for generating videos."""
    model: Optional[str] = Field(default=None, description='ID of the model to use. For a list of models, see `Google models\n    <https://cloud.google.com/vertex-ai/generative-ai/docs/learn/models>`_.')
    prompt: Optional[str] = Field(default=None, description='The text prompt for generating the videos.\n      Optional if image or video is provided.')
    image: Optional[Image] = Field(default=None, description='The input image for generating the videos.\n      Optional if prompt is provided. Not allowed if video is provided.')
    video: Optional[Video] = Field(default=None, description='The input video for video extension use cases.\n      Optional if prompt is provided. Not allowed if image is provided.')
    source: Optional[GenerateVideosSource] = Field(default=None, description='A set of source input(s) for video generation.')
    config: Optional[GenerateVideosConfig] = Field(default=None, description='Configuration for generating videos.')

class GeneratedVideo(_common.BaseModel):
    """A generated video."""
    video: Optional[Video] = Field(default=None, description='The output video')

class GenerateVideosResponse(_common.BaseModel):
    """Response with generated videos."""
    generated_videos: Optional[list[GeneratedVideo]] = Field(default=None, description='List of the generated videos')
    rai_media_filtered_count: Optional[int] = Field(default=None, description='Returns if any videos were filtered due to RAI policies.')
    rai_media_filtered_reasons: Optional[list[str]] = Field(default=None, description='Returns rai failure reasons if any.')

class Operation(ABC):
    """A long-running operation."""
    name: Optional[str] = Field(default=None, description='The server-assigned name, which is only unique within the same service that originally returns it. If you use the default HTTP mapping, the `name` should be a resource name ending with `operations/{unique_id}`.')
    metadata: Optional[dict[str, Any]] = Field(default=None, description='Service-specific metadata associated with the operation. It typically contains progress information and common metadata such as create time. Some services might not provide such metadata.  Any method that returns a long-running operation should document the metadata type, if any.')
    done: Optional[bool] = Field(default=None, description='If the value is `false`, it means the operation is still in progress. If `true`, the operation is completed, and either `error` or `response` is available.')
    error: Optional[dict[str, Any]] = Field(default=None, description='The error result of the operation in case of failure or cancellation.')

class GenerateVideosOperation(_common.BaseModel, Operation):
    """A video generation operation."""
    response: Optional[GenerateVideosResponse] = Field(default=None, description='The generated videos.')
    result: Optional[GenerateVideosResponse] = Field(default=None, description='The generated videos.')

class GetTuningJobConfig(_common.BaseModel):
    """Optional parameters for tunings.get method."""
    http_options: Optional[HttpOptions] = Field(default=None, description='Used to override HTTP request options.')

class _GetTuningJobParameters(_common.BaseModel):
    """Parameters for the get method."""
    name: Optional[str] = Field(default=None, description='')
    config: Optional[GetTuningJobConfig] = Field(default=None, description='Optional parameters for the request.')

class TunedModelCheckpoint(_common.BaseModel):
    """TunedModelCheckpoint for the Tuned Model of a Tuning Job."""
    checkpoint_id: Optional[str] = Field(default=None, description='The ID of the checkpoint.\n      ')
    epoch: Optional[int] = Field(default=None, description='The epoch of the checkpoint.\n      ')
    step: Optional[int] = Field(default=None, description='The step of the checkpoint.\n      ')
    endpoint: Optional[str] = Field(default=None, description='The Endpoint resource name that the checkpoint is deployed to.\n      Format: `projects/{project}/locations/{location}/endpoints/{endpoint}`.\n      ')

class TunedModel(_common.BaseModel):
    """TunedModel for the Tuned Model of a Tuning Job."""
    model: Optional[str] = Field(default=None, description='Output only. The resource name of the TunedModel.\n      Format: `projects/{project}/locations/{location}/models/{model}@{version_id}`\n      When tuning from a base model, the version_id will be 1.\n      For continuous tuning, the version id will be incremented by 1 from the\n      last version id in the parent model. E.g., `projects/{project}/locations/{location}/models/{model}@{last_version_id + 1}`\n      ')
    endpoint: Optional[str] = Field(default=None, description='Output only. A resource name of an Endpoint.\n      Format: `projects/{project}/locations/{location}/endpoints/{endpoint}`.\n      ')
    checkpoints: Optional[list[TunedModelCheckpoint]] = Field(default=None, description='The checkpoints associated with this TunedModel.\n      This field is only populated for tuning jobs that enable intermediate\n      checkpoints.')

class SupervisedHyperParameters(_common.BaseModel):
    """Hyperparameters for SFT. This data type is not supported in Gemini API."""
    adapter_size: Optional[AdapterSize] = Field(default=None, description='Optional. Adapter size for tuning.')
    batch_size: Optional[int] = Field(default=None, description='Optional. Batch size for tuning. This feature is only available for open source models.')
    epoch_count: Optional[int] = Field(default=None, description='Optional. Number of complete passes the model makes over the entire training dataset during training.')
    learning_rate: Optional[float] = Field(default=None, description='Optional. Learning rate for tuning. Mutually exclusive with `learning_rate_multiplier`. This feature is only available for open source models.')
    learning_rate_multiplier: Optional[float] = Field(default=None, description='Optional. Multiplier for adjusting the default learning rate. Mutually exclusive with `learning_rate`. This feature is only available for 1P models.')

class SupervisedTuningSpec(_common.BaseModel):
    """Supervised tuning spec for tuning."""
    export_last_checkpoint_only: Optional[bool] = Field(default=None, description='Optional. If set to true, disable intermediate checkpoints for SFT and only the last checkpoint will be exported. Otherwise, enable intermediate checkpoints for SFT. Default is false.')
    hyper_parameters: Optional[SupervisedHyperParameters] = Field(default=None, description='Optional. Hyperparameters for SFT.')
    training_dataset_uri: Optional[str] = Field(default=None, description='Required. Training dataset used for tuning. The dataset can be specified as either a Cloud Storage path to a JSONL file or as the resource name of a Vertex Multimodal Dataset.')
    tuning_mode: Optional[TuningMode] = Field(default=None, description='Tuning mode.')
    validation_dataset_uri: Optional[str] = Field(default=None, description='Optional. Validation dataset used for tuning. The dataset can be specified as either a Cloud Storage path to a JSONL file or as the resource name of a Vertex Multimodal Dataset.')

class PreferenceOptimizationHyperParameters(_common.BaseModel):
    """Hyperparameters for Preference Optimization.

  This data type is not supported in Gemini API.
  """
    adapter_size: Optional[AdapterSize] = Field(default=None, description='Optional. Adapter size for preference optimization.')
    beta: Optional[float] = Field(default=None, description='Optional. Weight for KL Divergence regularization.')
    epoch_count: Optional[int] = Field(default=None, description='Optional. Number of complete passes the model makes over the entire training dataset during training.')
    learning_rate_multiplier: Optional[float] = Field(default=None, description='Optional. Multiplier for adjusting the default learning rate.')

class PreferenceOptimizationSpec(_common.BaseModel):
    """Preference optimization tuning spec for tuning."""
    export_last_checkpoint_only: Optional[bool] = Field(default=None, description='Optional. If set to true, disable intermediate checkpoints for Preference Optimization and only the last checkpoint will be exported. Otherwise, enable intermediate checkpoints for Preference Optimization. Default is false.')
    hyper_parameters: Optional[PreferenceOptimizationHyperParameters] = Field(default=None, description='Optional. Hyperparameters for Preference Optimization.')
    training_dataset_uri: Optional[str] = Field(default=None, description='Required. Cloud Storage path to file containing training dataset for preference optimization tuning. The dataset must be formatted as a JSONL file.')
    validation_dataset_uri: Optional[str] = Field(default=None, description='Optional. Cloud Storage path to file containing validation dataset for preference optimization tuning. The dataset must be formatted as a JSONL file.')

class DistillationHyperParameters(_common.BaseModel):
    """Distillation hyperparameters for tuning."""
    adapter_size: Optional[AdapterSize] = Field(default=None, description="The size of the adapter. Can be 'small', 'medium', or 'large'.")
    epoch_count: Optional[int] = Field(default=None, description='Number of complete passes the model makes over the entire training dataset\n      during training.')
    learning_rate_multiplier: Optional[float] = Field(default=None, description='Multiplier for adjusting the default learning rate.')
    generation_config: Optional[GenerationConfig] = Field(default=None, description='Generation config for Distillation teacher model sampling. Only the\n      following fields are supported for distillation teacher samplings:\n      - temperature\n      - top_p\n      - top_k\n      - candidate_count\n      - thinking_config')
    learning_rate: Optional[float] = Field(default=None, description='The learning rate for distillation tuning.')
    batch_size: Optional[int] = Field(default=None, description='Batch size for tuning. This feature is only available for open\n      source models.')

class DistillationSamplingSpec(_common.BaseModel):
    """Distillation sampling spec for tuning."""
    base_teacher_model: Optional[str] = Field(default=None, description='The base teacher model that is being distilled. See [Supported\n       models](https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/tuning#supported_models).')
    tuned_teacher_model_source: Optional[str] = Field(default=None, description='The resource name of the Tuned teacher model. Format:\n      `projects/{project}/locations/{location}/models/{model}`.')
    validation_dataset_uri: Optional[str] = Field(default=None, description='Cloud Storage path to file containing validation dataset for distillation.\n     The dataset must be formatted as a JSONL file.')
    prompt_dataset_uri: Optional[str] = Field(default=None, description='Cloud Storage path to file containing prompt dataset for distillation.\n      The dataset must be formatted as a JSONL file.')
    hyperparameters: Optional[DistillationHyperParameters] = Field(default=None, description='Hyperparameters for distillation tuning.')

class DistillationSpec(_common.BaseModel):
    """Distillation tuning spec for tuning."""
    prompt_dataset_uri: Optional[str] = Field(default=None, description='Optional. Cloud Storage path to file containing prompt dataset for distillation. The dataset must be formatted as a JSONL file.')
    base_teacher_model: Optional[str] = Field(default=None, description='The base teacher model that is being distilled. See [Supported models](https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/tuning#supported_models).')
    hyper_parameters: Optional[DistillationHyperParameters] = Field(default=None, description='Optional. Hyperparameters for Distillation.')
    pipeline_root_directory: Optional[str] = Field(default=None, description='Deprecated. A path in a Cloud Storage bucket, which will be treated as the root output directory of the distillation pipeline. It is used by the system to generate the paths of output artifacts.')
    student_model: Optional[str] = Field(default=None, description='The student model that is being tuned, e.g., "google/gemma-2b-1.1-it". Deprecated. Use base_model instead.')
    training_dataset_uri: Optional[str] = Field(default=None, description='Deprecated. Cloud Storage path to file containing training dataset for tuning. The dataset must be formatted as a JSONL file.')
    tuned_teacher_model_source: Optional[str] = Field(default=None, description='The resource name of the Tuned teacher model. Format: `projects/{project}/locations/{location}/models/{model}`.')
    validation_dataset_uri: Optional[str] = Field(default=None, description='Optional. Cloud Storage path to file containing validation dataset for tuning. The dataset must be formatted as a JSONL file.')
    tuning_mode: Optional[TuningMode] = Field(default=None, description='Optional. Specifies the tuning mode for distillation (sft part). This feature is only available for open source models.')

class AutoraterConfig(_common.BaseModel):
    """Autorater config used for evaluation."""
    sampling_count: Optional[int] = Field(default=None, description='Number of samples for each instance in the dataset.\n  If not specified, the default is 4. Minimum value is 1, maximum value\n  is 32.')
    flip_enabled: Optional[bool] = Field(default=None, description='Optional. Default is true. Whether to flip the candidate and baseline\n  responses. This is only applicable to the pairwise metric. If enabled, also\n  provide PairwiseMetricSpec.candidate_response_field_name and\n  PairwiseMetricSpec.baseline_response_field_name. When rendering\n  PairwiseMetricSpec.metric_prompt_template, the candidate and baseline\n  fields will be flipped for half of the samples to reduce bias.')
    autorater_model: Optional[str] = Field(default=None, description='The fully qualified name of the publisher model or tuned autorater\n  endpoint to use.\n\n  Publisher model format:\n  `projects/{project}/locations/{location}/publishers/{publisher}/models/{model}`\n\n  Tuned model endpoint format:\n  `projects/{project}/locations/{location}/endpoints/{endpoint}`')
    generation_config: Optional[GenerationConfig] = Field(default=None, description='Configuration options for model generation and outputs.')

class ReinforcementTuningParseResponseConfig(_common.BaseModel):
    """Defines how to parse sample response config for reinforcement tuning.

  The parsed response (i.e., substring) will be passed to the reward functions.
  For example, the input prompt might be: > "Perform step-by-step thoughts first
  to problem A, finally output answer in the <ans> </ans> block." The sample
  response from the model under tuning might look like: > "<ans>Yes</ans>" Here,
  users can define the following parse config: ``` { "parseType":
  "REGEX_EXTRACT", "regexExtractExpression": ".*(.*?)" } ``` The resulting
  parsed response would be `"Yes"` and will be passed to the reward functions
  for evaluating rewards. This data type is not supported in Gemini API.
  """
    parse_type: Optional[ResponseParseType] = Field(default=None, description='Defines the type for parsing sample response.')
    regex_extract_expression: Optional[str] = Field(default=None, description='Defines the regex for extracting the important part of sample response. This field is only used when parse_type is ResponseParseType.REGEX_EXTRACT.')

class ReinforcementTuningAutoraterScorerParsedResponseConversionScorer(_common.BaseModel):
    """Scores responses by directly converting the parsed autorater response to a float reward.

  Note: Reward is clipped to be within `[-1, 1]`, i.e., `reward =
  max(min(reward, 1.0), -1.0)`. This data type is not supported in Gemini API.
  """
    pass

class ReinforcementTuningAutoraterScorerExactMatchScorer(_common.BaseModel):
    """Scores autorater responses by using exact string match reward scorer.

  This data type is not supported in Gemini API.
  """
    correct_answer_reward: Optional[float] = Field(default=None, description='Assigns this reward score if the parsed response string equals the expression.')
    wrong_answer_reward: Optional[float] = Field(default=None, description='Assigns this reward score if the parsed reward value does not equal the expression.')
    expression: Optional[str] = Field(default=None, description='The string expression to match against for scoring. This field supports placeholders in the format of {{references.key}} that will be replaced before matching. Regex is not supported for this expression. For example, users can define an ExactMatchScorer as follows: { "correctAnswerReward": 1.0, "wrongAnswerReward": -1.0, "expression": "{{references.concise_answer}}" } When evaluating the reward for each parsed autorater response, if the prompt references in the training/validation dataset has the following fields: ``` { "example": ..., "references": { "concise_ansser": "Yes", "verbose_answer": "The answer is Yes" } } ``` The above ExactMatchScorer will be replaced as follows for scoring: ``` { "correctAnswerReward": 1.0, "wrongAnswerReward": -1.0, "expression": "Yes" } ``` If the *parsed* autorater response is equal to the string `"Yes"`, then the reward is `1.0`, otherwise the reward is `-1.0`.')

class ReinforcementTuningAutoraterScorer(_common.BaseModel):
    """Reinforcement tuning autorater scorer."""
    autorater_config: Optional[AutoraterConfig] = Field(default=None, description='Autorater config for evaluation.')
    autorater_prompt: Optional[str] = Field(default=None, description='The prompt for an autorater to scorer the parsed sample response. This field supports the following placeholders that will be replaced before scoring: - {{prompt}} - {{response}} - {{system_instruction}} - {{references.key}} ')
    autorater_response_parse_config: Optional[ReinforcementTuningParseResponseConfig] = Field(default=None, description='Parses autorater returned response for scoring. For example, if the autorater response has reward stored in the `2.0` block, defining a parsing response config using regex `".*(.*?)"` will return a score `"2.0"`.')
    parsed_response_conversion_scorer: Optional[ReinforcementTuningAutoraterScorerParsedResponseConversionScorer] = Field(default=None, description='Scores autorater responses by directly converting parsed autorater response to a float reward. Note: Reward is clipped to be within `[-1, 1]`, i.e., `reward = max(min(reward, 1.0), -1.0)`.')
    exact_match_scorer: Optional[ReinforcementTuningAutoraterScorerExactMatchScorer] = Field(default=None, description='Scores autorater responses by using string match reward scorer.')

class ReinforcementTuningCodeExecutionRewardScorer(_common.BaseModel):
    """ReinforcementTuningCodeExecutionRewardScorer allows users to implement a function to evaluate rewards for the sample response.

  The function signature is as follows: ``` def evaluate(example: dict[str,
  Any], response: dict[str, Any]) -> float: ... ``` `example` is a
  ReinforcementTuningExample in ProtoJSON format, (i.e., the format is the same
  as as one line in the training/validation dataset except that the keys must be
  in camel case). System instructions (i.e., `example.get("systemInstruction")`)
  and references (i.e., `example.get("references")`) are also included in the
  `example` provided that they are set in the training/validation dataset.
  `response` is a Content in ProtoJSON format (i.e., keys must be in camel
  case), which is the same as the Online Prediction response for Gemini models.
  Note: Reward output by the `evaluate` function is clipped to be within `[-1,
  1]`, i.e., `reward = max(min(reward, 1.0), -1.0)`. This data type is not
  supported in Gemini API.
  """
    python_code_snippet: Optional[str] = Field(default=None, description='The python code snippet as a string for evaluating rewards. The following is an example python code snippet that returns a reward `1.0` for a parsed response matching the user-provided reference answer in per prompt references map. ``` def evaluate(example, response) -> float: response_str = response.get("parts", [])0 references = example.get("references", {}) if response_str == references.get("concise_answer"): return 1.0 return -1.0 ``` Note: Reward output by the evaluate function is clipped to be within `[-1, 1]`, i.e., `reward = max(min(reward, 1.0), -1.0)`.')

class ReinforcementTuningStringMatchRewardScorerStringMatchExpression(_common.BaseModel):
    """Evaluates parsed response using match type against the expression.

  Returns `true` if `MatchOperation(target, expression)` evaluates to `true`,
  and `false` otherwise. This data type is not supported in Gemini API.
  """
    match_operation: Optional[MatchOperation] = Field(default=None, description='Match operation to use for evaluating rewards.')
    expression: Optional[str] = Field(default=None, description='A string or a regular expression to match against for evaluating rewards. Users can also provide a references map of `{key: value}` whose `value` will be used to replace the placeholder {{references.key}} in the expression. For example, if the following `references` are defined in the training / validation dataset: ``` { "systemInstruction": ..., "contents": ..., "references": { "concise_answer": "Yes", "verbose_answer": "The answer is Yes" } } ``` and if users define the following StringMatchExpression: { "matchOperation": "REGEX_CONTAINS", "expression": ".*{{references.concise_answer}}.*" } On evaluating the reward for each sample response, this StringMatchExpression will be substituted as: ``` { "matchOperation": "REGEX_CONTAINS", "expression": ".*Yes.*" } ```')

class ReinforcementTuningStringMatchRewardScorerJsonMatchExpression(_common.BaseModel):
    """JsonMatchExpression supports converting the parsed responses to JSON format, finding the value in the JSON response that matches the key_name in the first level, and performing StringMatchExpression operation on the matched JSON value.

  This data type is not supported in Gemini API.
  """
    key_name: Optional[str] = Field(default=None, description="The key name to find the value in the parsed response that's in JSON format. Only first-level key matching is supported.")
    value_string_match_expression: Optional[ReinforcementTuningStringMatchRewardScorerStringMatchExpression] = Field(default=None, description='String match expression to match against the extracted value from the JSON representation of the parsed response.')

class ReinforcementTuningStringMatchRewardScorer(_common.BaseModel):
    """ReinforcementTuningStringMatchRewardScorer is used to score parsed responses for string matching use cases.

  For example, for math problems, users can use string match scorer to check if
  the correct exact answer is generated. Note: Reward returned by the string
  match reward function is clipped to be within `[-1, 1]` if wrongAnswerReward
  or correctAnswerReward are beyond the range, i.e., `reward = max(min(reward,
  1.0), -1.0)`. This data type is not supported in Gemini API.
  """
    wrong_answer_reward: Optional[float] = Field(default=None, description='Wrong answer reward is returned if the parsed response is evaluated as `false`. All wrong answers get the same reward.')
    correct_answer_reward: Optional[float] = Field(default=None, description='Correct answer rewawrd is returned if the parsed response is evaluated as `true`. All correct answers get the same reward.')
    string_match_expression: Optional[ReinforcementTuningStringMatchRewardScorerStringMatchExpression] = Field(default=None, description='Uses string match expression to evaluate parsed response.')
    json_match_expression: Optional[ReinforcementTuningStringMatchRewardScorerJsonMatchExpression] = Field(default=None, description='Uses json match expression to evaluate parsed response.')

class ReinforcementTuningCloudRunRewardScorer(_common.BaseModel):
    """ReinforcementTuningCloudRunRewardScorer allows users to implement a reward function through GCP Cloud Run.

  Comparing with ReinforcementTuningCodeExecutionRewardScorer that runs in a
  Sandbox and has no internet access, Cloud Run reward scorer is fully
  controlled by users. The Cloud Run service should implement the following HTTP
  API: HTTP method: `POST` HTTP request body: ``` { "example":
  ReinforcementTuningExample, "response": Content, "metadata": { "step": int
  "tuning_job_id": int64 } } ``` * `example` is a ReinforcementTuningExample in
  ProtoJSON format, (i.e., the format is the same as as one line in the
  training/validation dataset except that the keys must be in camel case).
  System instructions (i.e., `example.get("systemInstruction")`) and references
  (i.e., `example.get("references")`) are also included in the `example`
  provided that they are set in the training/validation dataset. * `response` is
  a Content in ProtoJSON format (i.e., keys must be in camel case), which is the
  same as the Online Prediction response for Gemini models. HTTP response body:
  { "reward": float, "user_requested_aux_info": str // Optional } where the
  field "user_requested_aux_info" is any (optional) string provided by users for
  assisting debugging. It's in snake case. This field is mostly useful when
  calling the GenAiTuningService.ValidateReinforcementTuningReward API, where
  the proto field (not Cloud Run HTTP response body) userRequestedAuxInfo will
  be populated if the Cloud Run reward function sets this field in the HTTP
  response. The following are examples for the HTTP request and response body.
  Example HTTP request body: ``` { "example": { "contents": [ { "role": "user",
  "parts": [ { "text": "What is the capital of France?" } ] } ], "references": {
  "answer": "Paris" } }, "response": { "parts": [ { "text": "London" } ] },
  "metadata": { "step": 1, "tuning_job_id": 123456789 } } ``` Example HTTP
  response body: ``` { "reward": -1.0 } ``` Note: Reward output by Cloud Run
  reward function is clipped to be within `[-1, 1]`, i.e., `reward =
  max(min(reward, 1.0), -1.0)`. This data type is not supported in Gemini API.
  """
    cloud_run_uri: Optional[str] = Field(default=None, description='URI of the Cloud Run service that will be used to compute the reward. The [Vertex AI Secure Fine Tuning Service Agent](https://docs.cloud.google.com/iam/docs/service-agents#vertex-ai-secure-fine-tuning-service-agent) (`service-@gcp-sa-vertex-tune.iam.gserviceaccount.com`) must be granted the permission (e.g. by granting `roles/run.invoker` in IAM) to invoke the Cloud Run service.')

class SingleReinforcementTuningRewardConfig(_common.BaseModel):
    """Single reinforcement tuning reward config."""
    autorater_scorer: Optional[ReinforcementTuningAutoraterScorer] = Field(default=None, description='Scores parsed responses for autorater use cases by using a model to compute the reward.')
    reward_name: Optional[str] = Field(default=None, description='A unique reward name for identifying each single reinforcement tuning reward.')
    parse_response_config: Optional[ReinforcementTuningParseResponseConfig] = Field(default=None, description='Defines how to parse sample response. For example, given a sample response for evaluating the reward, users might want to extract the text only between `` and `` in the sample response, and keeps only the last one in case there are multiple such tags. To achieve such a purpose, they can define a regex `".*(.*?)"` using the ReinforcementTuningParseResponseConfig.ResponseParseType.REGEX_EXTRACT parse type.')
    code_execution_reward_scorer: Optional[ReinforcementTuningCodeExecutionRewardScorer] = Field(default=None, description='ReinforcementTuningCodeExecutionRewardScorer is used to score parsed responses for code execution use cases.')
    string_match_reward_scorer: Optional[ReinforcementTuningStringMatchRewardScorer] = Field(default=None, description='ReinforcementTuningStringMatchRewardScorer is used to score parsed responses for simple string matching use cases against reference answers.')
    cloud_run_reward_scorer: Optional[ReinforcementTuningCloudRunRewardScorer] = Field(default=None, description='ReinforcementTuningCloudRunRewardScorer is used to score parsed responses by calling a Cloud Run service.')

class CompositeReinforcementTuningRewardConfigWeightedRewardConfig(_common.BaseModel):
    """Composite reinforcement tuning reward config weighted reward config."""
    reward_config: Optional[SingleReinforcementTuningRewardConfig] = Field(default=None, description='Single reward configuration.')
    weight: Optional[float] = Field(default=None, description='How much this single reward contributes to the total overall reward. Total reward is a linear combination of single rewards with their corresponding weights, i.e., ``` total_reward = ( weight_a * reward_a + weight_b * reward_b + ... ) / (weight_a + weight_b + ...) ```')

class CompositeReinforcementTuningRewardConfig(_common.BaseModel):
    """Composite reinforcement tuning reward config."""
    weighted_reward_configs: Optional[list[CompositeReinforcementTuningRewardConfigWeightedRewardConfig]] = Field(default=None, description='List of reward function configurations with weights.')

class ReinforcementTuningHyperParameters(_common.BaseModel):
    """Hyperparameters for Reinforcement Tuning."""
    epoch_count: Optional[int] = Field(default=None, description='Optional. Number of training epoches for the tuning job.')
    learning_rate_multiplier: Optional[float] = Field(default=None, description='Learning rate multiplier for Reinforcement Learning.')
    adapter_size: Optional[AdapterSize] = Field(default=None, description='Optional. Adapter size for Reinforcement Tuning.')
    samples_per_prompt: Optional[int] = Field(default=None, description='Optional. Number of different responses to generate per prompt during tuning.')
    batch_size: Optional[int] = Field(default=None, description='Optional. Batch size for the tuning job. How many prompts to process at a train step. If not set, the batch size will be determined automatically.')
    evaluate_interval: Optional[int] = Field(default=None, description='Optional. How often at steps to evaluate the tuning job during training. If not set, evel will be run per epoch. `total_steps = epoch_count * samples_per_prompt / total_prompts_in_dataset`')
    checkpoint_interval: Optional[int] = Field(default=None, description='Optional. How often at steps to save checkpoints during training. If not set, one checkpoint per epoch will be set. ```total_steps = epoch_count * samples_per_prompt / total_prompts_in_dataset```')
    max_output_tokens: Optional[int] = Field(default=None, description='Optional. The maximum number of tokens to generate per prompt. Default to 32768.')
    thinking_level: Optional[ReinforcementTuningThinkingLevel] = Field(default=None, description='Indicates the maximum thinking depth during tuning. Starting from Gemini 3.5 models, the old thinking_budget will no longer be supported and will result in a user error if set. Instead, users should use the thinking_level parameter to control the maximum thinking depth.')
    thinking_budget: Optional[int] = Field(default=None, description='Optional. The thinking budget for the tuning job to optimize for (Gemini 2.5 only). * -1 means dynamic thinking * 0 means no thinking * > 0 means thinking budget in tokens If not set, default to -1 (dynamic thinking).')
    step_count: Optional[int] = Field(default=None, description='Optional. Number of steps for the tuning job (mutually exclusive with epoch_count).')

class ReinforcementTuningSpec(_common.BaseModel):
    """Reinforcement tuning spec for tuning."""
    composite_reward_config: Optional[CompositeReinforcementTuningRewardConfig] = Field(default=None, description='Composite reward function configuration for reinforcement tuning.')
    training_dataset_uri: Optional[str] = Field(default=None, description='Cloud Storage path to the file containing training dataset for tuning. The dataset must be formatted as a JSONL file.')
    validation_dataset_uri: Optional[str] = Field(default=None, description='Cloud Storage path to the file containing validation dataset for tuning. The dataset must be formatted as a JSONL file.')
    hyper_parameters: Optional[ReinforcementTuningHyperParameters] = Field(default=None, description='Additional hyper-parameters to use during tuning.')
    single_reward_config: Optional[SingleReinforcementTuningRewardConfig] = Field(default=None, description='Single reward function configuration for reinforcement tuning.')

class GcsDestination(_common.BaseModel):
    """The Google Cloud Storage location where the output is to be written to."""
    output_uri_prefix: Optional[str] = Field(default=None, description="Required. Google Cloud Storage URI to output directory. If the uri doesn't end with '/', a '/' will be automatically appended. The directory is created if it doesn't exist.")

    @pydantic.model_validator(mode='after')
    def _validate_gcs_path(self) -> 'GcsDestination':
        if self.output_uri_prefix and (not self.output_uri_prefix.startswith('gs://')):
            raise ValueError('output_uri_prefix must be a valid GCS path starting with "gs://".')
        return self

class OutputConfig(_common.BaseModel):
    """Config for evaluation output."""
    gcs_destination: Optional[GcsDestination] = Field(default=None, description='Cloud storage destination for evaluation output.')

class EvaluationConfig(_common.BaseModel):
    """Evaluation config for tuning."""
    metrics: Optional[list[MetricUnion]] = Field(default=None, description='The metrics used for evaluation.')
    output_config: Optional[OutputConfig] = Field(default=None, description='Config for evaluation output.')
    autorater_config: Optional[AutoraterConfig] = Field(default=None, description='Autorater config for evaluation.')
    inference_generation_config: Optional[GenerationConfig] = Field(default=None, description='Generation config for inference.')

class GoogleRpcStatus(_common.BaseModel):
    """The `Status` type defines a logical error model that is suitable for different programming environments, including REST APIs and RPC APIs.

  It is used by [gRPC](https://github.com/grpc). Each `Status` message contains
  three pieces of data: error code, error message, and error details. You can
  find out more about this error model and how to work with it in the [API
  Design Guide](https://cloud.google.com/apis/design/errors). This data type is
  not supported in Gemini API.
  """
    code: Optional[int] = Field(default=None, description='The status code, which should be an enum value of google.rpc.Code.')
    details: Optional[list[dict[str, Any]]] = Field(default=None, description='A list of messages that carry the error details. There is a common set of message types for APIs to use.')
    message: Optional[str] = Field(default=None, description='A developer-facing error message, which should be in English. Any user-facing error message should be localized and sent in the google.rpc.Status.details field, or localized by the client.')

class PreTunedModel(_common.BaseModel):
    """A pre-tuned model for continuous tuning.

  This data type is not supported in Gemini API.
  """
    base_model: Optional[str] = Field(default=None, description='Output only. The name of the base model this PreTunedModel was tuned from.')
    checkpoint_id: Optional[str] = Field(default=None, description='Optional. The source checkpoint id. If not specified, the default checkpoint will be used.')
    tuned_model_name: Optional[str] = Field(default=None, description='The resource name of the Model. E.g., a model resource name with a specified version id or alias: `projects/{project}/locations/{location}/models/{model}@{version_id}` `projects/{project}/locations/{location}/models/{model}@{alias}` Or, omit the version id to use the default version: `projects/{project}/locations/{location}/models/{model}`')

class DatasetDistributionDistributionBucket(_common.BaseModel):
    """Dataset bucket used to create a histogram for the distribution given a population of values.

  This data type is not supported in Gemini API.
  """
    count: Optional[int] = Field(default=None, description='Output only. Number of values in the bucket.')
    left: Optional[float] = Field(default=None, description='Output only. Left bound of the bucket.')
    right: Optional[float] = Field(default=None, description='Output only. Right bound of the bucket.')

class DatasetDistribution(_common.BaseModel):
    """Distribution computed over a tuning dataset.

  This data type is not supported in Gemini API.
  """
    buckets: Optional[list[DatasetDistributionDistributionBucket]] = Field(default=None, description='Output only. Defines the histogram bucket.')
    max: Optional[float] = Field(default=None, description='Output only. The maximum of the population values.')
    mean: Optional[float] = Field(default=None, description='Output only. The arithmetic mean of the values in the population.')
    median: Optional[float] = Field(default=None, description='Output only. The median of the values in the population.')
    min: Optional[float] = Field(default=None, description='Output only. The minimum of the population values.')
    p5: Optional[float] = Field(default=None, description='Output only. The 5th percentile of the values in the population.')
    p95: Optional[float] = Field(default=None, description='Output only. The 95th percentile of the values in the population.')
    sum: Optional[float] = Field(default=None, description='Output only. Sum of a given population of values.')

class ReinforcementTuningExample(_common.BaseModel):
    """User-facing format for Gemini Reinforcement Tuning examples on Vertex."""
    contents: Optional[list[Content]] = Field(default=None, description='Multi-turn contents that represents the Prompt.')
    references: Optional[dict[str, str]] = Field(default=None, description='References for the given prompt. The key is the name of the reference, and the value is the reference itself.')
    system_instruction: Optional[Content] = Field(default=None, description='Corresponds to system_instruction in user-facing GenerateContentRequest.')
    tools: Optional[list[Tool]] = Field(default=None, description='Optional. Corresponds to tools in user-facing GenerateContentRequest.')

class ReinforcementTuningUserDatasetExamples(_common.BaseModel):
    """Sample reinforcement tuning user data in the training dataset.

  The contents are truncated for better UI showing. This data type is not
  supported in Gemini API.
  """
    user_dataset_examples: Optional[list[ReinforcementTuningExample]] = Field(default=None, description='List of user datasset examples showing to user.')

class DatasetStats(_common.BaseModel):
    """Statistics computed over a tuning dataset.

  This data type is not supported in Gemini API.
  """
    dropped_example_indices: Optional[list[int]] = Field(default=None, description='Output only. A partial sample of the indices (starting from 1) of the dropped examples.')
    dropped_example_reasons: Optional[list[str]] = Field(default=None, description='Output only. For each index in `dropped_example_indices`, the user-facing reason why the example was dropped.')
    total_billable_character_count: Optional[int] = Field(default=None, description='Output only. Number of billable characters in the tuning dataset.')
    total_tuning_character_count: Optional[int] = Field(default=None, description='Output only. Number of tuning characters in the tuning dataset.')
    tuning_dataset_example_count: Optional[int] = Field(default=None, description='Output only. Number of examples in the tuning dataset.')
    tuning_step_count: Optional[int] = Field(default=None, description='Output only. Number of tuning steps for this Tuning Job.')
    user_dataset_examples: Optional[list[Content]] = Field(default=None, description='Output only. Sample user messages in the training dataset uri.')
    user_input_token_distribution: Optional[DatasetDistribution] = Field(default=None, description='Output only. Dataset distributions for the user input tokens.')
    user_message_per_example_distribution: Optional[DatasetDistribution] = Field(default=None, description='Output only. Dataset distributions for the messages per example.')
    user_output_token_distribution: Optional[DatasetDistribution] = Field(default=None, description='Output only. Dataset distributions for the user output tokens.')
    contents_per_example_distribution: Optional[DatasetDistribution] = Field(default=None, description='Output only. Dataset distributions for the number of contents per example.')
    reinforcement_tuning_user_dataset_examples: Optional[ReinforcementTuningUserDatasetExamples] = Field(default=None, description='Output only. Sample user dataset examples in the training dataset uri for Reinforcement Tuning.')
    total_billable_token_count: Optional[int] = Field(default=None, description='Output only. Number of billable tokens in the tuning dataset.')

class DistillationDataStats(_common.BaseModel):
    """Statistics for distillation prompt dataset.

  These statistics do not include the responses sampled from the teacher model.
  This data type is not supported in Gemini API.
  """
    training_dataset_stats: Optional[DatasetStats] = Field(default=None, description='Output only. Statistics computed for the training dataset.')

class GeminiPreferenceExampleCompletion(_common.BaseModel):
    """Completion and its preference score.

  This data type is not supported in Gemini API.
  """
    completion: Optional[Content] = Field(default=None, description='Single turn completion for the given prompt.')
    score: Optional[float] = Field(default=None, description='The score for the given completion.')

class GeminiPreferenceExample(_common.BaseModel):
    """Input example for preference optimization.

  This data type is not supported in Gemini API.
  """
    completions: Optional[list[GeminiPreferenceExampleCompletion]] = Field(default=None, description='List of completions for a given prompt.')
    contents: Optional[list[Content]] = Field(default=None, description='Multi-turn contents that represents the Prompt.')

class PreferenceOptimizationDataStats(_common.BaseModel):
    """Statistics computed for datasets used for preference optimization.

  This data type is not supported in Gemini API.
  """
    dropped_example_indices: Optional[list[int]] = Field(default=None, description='Output only. A partial sample of the indices (starting from 1) of the dropped examples.')
    dropped_example_reasons: Optional[list[str]] = Field(default=None, description='Output only. For each index in `dropped_example_indices`, the user-facing reason why the example was dropped.')
    score_variance_per_example_distribution: Optional[DatasetDistribution] = Field(default=None, description='Output only. Dataset distributions for scores variance per example.')
    scores_distribution: Optional[DatasetDistribution] = Field(default=None, description='Output only. Dataset distributions for scores.')
    total_billable_token_count: Optional[int] = Field(default=None, description='Output only. Number of billable tokens in the tuning dataset.')
    tuning_dataset_example_count: Optional[int] = Field(default=None, description='Output only. Number of examples in the tuning dataset.')
    tuning_step_count: Optional[int] = Field(default=None, description='Output only. Number of tuning steps for this Tuning Job.')
    user_dataset_examples: Optional[list[GeminiPreferenceExample]] = Field(default=None, description='Output only. Sample user examples in the training dataset.')
    user_input_token_distribution: Optional[DatasetDistribution] = Field(default=None, description='Output only. Dataset distributions for the user input tokens.')
    user_output_token_distribution: Optional[DatasetDistribution] = Field(default=None, description='Output only. Dataset distributions for the user output tokens.')

class SupervisedTuningDatasetDistributionDatasetBucket(_common.BaseModel):
    """Dataset bucket used to create a histogram for the distribution given a population of values.

  This data type is not supported in Gemini API.
  """
    count: Optional[float] = Field(default=None, description='Output only. Number of values in the bucket.')
    left: Optional[float] = Field(default=None, description='Output only. Left bound of the bucket.')
    right: Optional[float] = Field(default=None, description='Output only. Right bound of the bucket.')

class SupervisedTuningDatasetDistribution(_common.BaseModel):
    """Dataset distribution for Supervised Tuning.

  This data type is not supported in Gemini API.
  """
    billable_sum: Optional[int] = Field(default=None, description='Output only. Sum of a given population of values that are billable.')
    buckets: Optional[list[SupervisedTuningDatasetDistributionDatasetBucket]] = Field(default=None, description='Output only. Defines the histogram bucket.')
    max: Optional[float] = Field(default=None, description='Output only. The maximum of the population values.')
    mean: Optional[float] = Field(default=None, description='Output only. The arithmetic mean of the values in the population.')
    median: Optional[float] = Field(default=None, description='Output only. The median of the values in the population.')
    min: Optional[float] = Field(default=None, description='Output only. The minimum of the population values.')
    p5: Optional[float] = Field(default=None, description='Output only. The 5th percentile of the values in the population.')
    p95: Optional[float] = Field(default=None, description='Output only. The 95th percentile of the values in the population.')
    sum: Optional[int] = Field(default=None, description='Output only. Sum of a given population of values.')

class SupervisedTuningDataStats(_common.BaseModel):
    """Tuning data statistics for Supervised Tuning.

  This data type is not supported in Gemini API.
  """
    dropped_example_reasons: Optional[list[str]] = Field(default=None, description='Output only. For each index in `truncated_example_indices`, the user-facing reason why the example was dropped.')
    total_billable_character_count: Optional[int] = Field(default=None, description='Output only. Number of billable characters in the tuning dataset.')
    total_billable_token_count: Optional[int] = Field(default=None, description='Output only. Number of billable tokens in the tuning dataset.')
    total_truncated_example_count: Optional[int] = Field(default=None, description='Output only. The number of examples in the dataset that have been dropped. An example can be dropped for reasons including: too many tokens, contains an invalid image, contains too many images, etc.')
    total_tuning_character_count: Optional[int] = Field(default=None, description='Output only. Number of tuning characters in the tuning dataset.')
    truncated_example_indices: Optional[list[int]] = Field(default=None, description='Output only. A partial sample of the indices (starting from 1) of the dropped examples.')
    tuning_dataset_example_count: Optional[int] = Field(default=None, description='Output only. Number of examples in the tuning dataset.')
    tuning_step_count: Optional[int] = Field(default=None, description='Output only. Number of tuning steps for this Tuning Job.')
    user_dataset_examples: Optional[list[Content]] = Field(default=None, description='Output only. Sample user messages in the training dataset uri.')
    user_input_token_distribution: Optional[SupervisedTuningDatasetDistribution] = Field(default=None, description='Output only. Dataset distributions for the user input tokens.')
    user_message_per_example_distribution: Optional[SupervisedTuningDatasetDistribution] = Field(default=None, description='Output only. Dataset distributions for the messages per example.')
    user_output_token_distribution: Optional[SupervisedTuningDatasetDistribution] = Field(default=None, description='Output only. Dataset distributions for the user output tokens.')

class TuningDataStats(_common.BaseModel):
    """The tuning data statistic values for TuningJob.

  This data type is not supported in Gemini API.
  """
    distillation_data_stats: Optional[DistillationDataStats] = Field(default=None, description='Output only. Statistics for distillation prompt dataset. These statistics do not include the responses sampled from the teacher model.')
    preference_optimization_data_stats: Optional[PreferenceOptimizationDataStats] = Field(default=None, description='Output only. Statistics for preference optimization.')
    supervised_tuning_data_stats: Optional[SupervisedTuningDataStats] = Field(default=None, description='The SFT Tuning data stats.')
    reinforcement_tuning_data_stats: Optional[DatasetStats] = Field(default=None, description='Output only. Statistics for reinforcement tuning.')

class EncryptionSpec(_common.BaseModel):
    """Represents a customer-managed encryption key specification that can be applied to a Vertex AI resource.

  This data type is not supported in Gemini API.
  """
    kms_key_name: Optional[str] = Field(default=None, description='Required. Resource name of the Cloud KMS key used to protect the resource. The Cloud KMS key must be in the same region as the resource. It must have the format `projects/{project}/locations/{location}/keyRings/{key_ring}/cryptoKeys/{crypto_key}`.')

class PartnerModelTuningSpec(_common.BaseModel):
    """Tuning spec for Partner models.

  This data type is not supported in Gemini API.
  """
    hyper_parameters: Optional[dict[str, Any]] = Field(default=None, description='Hyperparameters for tuning. The accepted hyper_parameters and their valid range of values will differ depending on the base model.')
    training_dataset_uri: Optional[str] = Field(default=None, description='Required. Cloud Storage path to file containing training dataset for tuning. The dataset must be formatted as a JSONL file.')
    validation_dataset_uri: Optional[str] = Field(default=None, description='Optional. Cloud Storage path to file containing validation dataset for tuning. The dataset must be formatted as a JSONL file.')

class BleuMetricValue(_common.BaseModel):
    """Bleu metric value for an instance.

  This data type is not supported in Gemini API.
  """
    score: Optional[float] = Field(default=None, description='Output only. Bleu score.')

class CustomCodeExecutionResult(_common.BaseModel):
    """Result for custom code execution metric.

  This data type is not supported in Gemini API.
  """
    score: Optional[float] = Field(default=None, description='Output only. Custom code execution score.')

class ExactMatchMetricValue(_common.BaseModel):
    """Exact match metric value for an instance.

  This data type is not supported in Gemini API.
  """
    score: Optional[float] = Field(default=None, description='Output only. Exact match score.')

class RawOutput(_common.BaseModel):
    """Raw output. This data type is not supported in Gemini API."""
    raw_output: Optional[list[str]] = Field(default=None, description='Output only. Raw output string.')

class CustomOutput(_common.BaseModel):
    """Spec for custom output. This data type is not supported in Gemini API."""
    raw_outputs: Optional[RawOutput] = Field(default=None, description='Output only. List of raw output strings.')

class PairwiseMetricResult(_common.BaseModel):
    """Spec for pairwise metric result.

  This data type is not supported in Gemini API.
  """
    custom_output: Optional[CustomOutput] = Field(default=None, description='Output only. Spec for custom output.')
    explanation: Optional[str] = Field(default=None, description='Output only. Explanation for pairwise metric score.')
    pairwise_choice: Optional[PairwiseChoice] = Field(default=None, description='Output only. Pairwise metric choice.')

class PointwiseMetricResult(_common.BaseModel):
    """Spec for pointwise metric result.

  This data type is not supported in Gemini API.
  """
    custom_output: Optional[CustomOutput] = Field(default=None, description='Output only. Spec for custom output.')
    explanation: Optional[str] = Field(default=None, description='Output only. Explanation for pointwise metric score.')
    score: Optional[float] = Field(default=None, description='Output only. Pointwise metric score.')

class RougeMetricValue(_common.BaseModel):
    """Rouge metric value for an instance.

  This data type is not supported in Gemini API.
  """
    score: Optional[float] = Field(default=None, description='Output only. Rouge score.')

class AggregationResult(_common.BaseModel):
    """The aggregation result for a single metric.

  This data type is not supported in Gemini API.
  """
    aggregation_metric: Optional[AggregationMetric] = Field(default=None, description='Aggregation metric.')
    bleu_metric_value: Optional[BleuMetricValue] = Field(default=None, description='Results for bleu metric.')
    custom_code_execution_result: Optional[CustomCodeExecutionResult] = Field(default=None, description='Result for code execution metric.')
    exact_match_metric_value: Optional[ExactMatchMetricValue] = Field(default=None, description='Results for exact match metric.')
    pairwise_metric_result: Optional[PairwiseMetricResult] = Field(default=None, description='Result for pairwise metric.')
    pointwise_metric_result: Optional[PointwiseMetricResult] = Field(default=None, description='Result for pointwise metric.')
    rouge_metric_value: Optional[RougeMetricValue] = Field(default=None, description='Results for rouge metric.')

class BigQuerySource(_common.BaseModel):
    """The BigQuery location for the input content.

  This data type is not supported in Gemini API.
  """
    input_uri: Optional[str] = Field(default=None, description='Required. BigQuery URI to a table, up to 2000 characters long. Accepted forms: * BigQuery path. For example: `bq://projectId.bqDatasetId.bqTableId`.')

class GcsSource(_common.BaseModel):
    """The Google Cloud Storage location for the input content.

  This data type is not supported in Gemini API.
  """
    uris: Optional[list[str]] = Field(default=None, description='Required. Google Cloud Storage URI(-s) to the input file(s). May contain wildcards. For more information on wildcards, see https://cloud.google.com/storage/docs/wildcards.')

class EvaluationDataset(_common.BaseModel):
    """The dataset used for evaluation.

  This data type is not supported in Gemini API.
  """
    bigquery_source: Optional[BigQuerySource] = Field(default=None, description='BigQuery source holds the dataset.')
    gcs_source: Optional[GcsSource] = Field(default=None, description='Cloud storage source holds the dataset. Currently only one Cloud Storage file path is supported.')

class AggregationOutput(_common.BaseModel):
    """The aggregation result for the entire dataset and all metrics.

  This data type is not supported in Gemini API.
  """
    aggregation_results: Optional[list[AggregationResult]] = Field(default=None, description='One AggregationResult per metric.')
    dataset: Optional[EvaluationDataset] = Field(default=None, description='The dataset used for evaluation & aggregation.')

class OutputInfo(_common.BaseModel):
    """Describes the info for output of EvaluationService.

  This data type is not supported in Gemini API.
  """
    gcs_output_directory: Optional[str] = Field(default=None, description='Output only. The full path of the Cloud Storage directory created, into which the evaluation results and aggregation results are written.')

class EvaluateDatasetResponse(_common.BaseModel):
    """The results from an evaluation run performed by the EvaluationService.

  This data type is not supported in Gemini API.
  """
    aggregation_output: Optional[AggregationOutput] = Field(default=None, description='Output only. Aggregation statistics derived from results of EvaluationService.')
    output_info: Optional[OutputInfo] = Field(default=None, description='Output only. Output info for EvaluationService.')

class EvaluateDatasetRun(_common.BaseModel):
    """Evaluate Dataset Run Result for Tuning Job.

  This data type is not supported in Gemini API.
  """
    checkpoint_id: Optional[str] = Field(default=None, description='Output only. The checkpoint id used in the evaluation run. Only populated when evaluating checkpoints.')
    error: Optional[GoogleRpcStatus] = Field(default=None, description='Output only. The error of the evaluation run if any.')
    evaluate_dataset_response: Optional[EvaluateDatasetResponse] = Field(default=None, description='Output only. Results for EvaluationService.')
    evaluation_run: Optional[str] = Field(default=None, description='Output only. The resource name of the evaluation run. Format: `projects/{project}/locations/{location}/evaluationRuns/{evaluation_run_id}`.')
    operation_name: Optional[str] = Field(default=None, description='Output only. Deprecated: The updated architecture uses evaluation_run instead.')

class FullFineTuningSpec(_common.BaseModel):
    """Tuning Spec for Full Fine Tuning.

  This data type is not supported in Gemini API.
  """
    hyper_parameters: Optional[SupervisedHyperParameters] = Field(default=None, description='Optional. Hyperparameters for Full Fine Tuning.')
    training_dataset_uri: Optional[str] = Field(default=None, description='Required. Training dataset used for tuning. The dataset can be specified as either a Cloud Storage path to a JSONL file or as the resource name of a Vertex Multimodal Dataset.')
    validation_dataset_uri: Optional[str] = Field(default=None, description='Optional. Validation dataset used for tuning. The dataset can be specified as either a Cloud Storage path to a JSONL file or as the resource name of a Vertex Multimodal Dataset.')

class VeoHyperParameters(_common.BaseModel):
    """Hyperparameters for Veo. This data type is not supported in Gemini API."""
    epoch_count: Optional[int] = Field(default=None, description='Optional. Number of complete passes the model makes over the entire training dataset during training.')
    learning_rate_multiplier: Optional[float] = Field(default=None, description='Optional. Multiplier for adjusting the default learning rate.')
    tuning_task: Optional[TuningTask] = Field(default=None, description='The tuning task for Veo.')
    veo_data_mixture_ratio: Optional[float] = Field(default=None, description='Optional. The ratio of Google internal dataset to use in the training mixture, in range of `[0, 1)`. If `0.2`, it means 20% of Google internal dataset and 80% of user dataset will be used for training. If not set, the default value is 0.1.')
    adapter_size: Optional[AdapterSize] = Field(default=None, description='Optional. The adapter size for LoRA tuning.')
    tuning_speed: Optional[TuningSpeed] = Field(default=None, description='The speed of the tuning job. Only supported for Veo 3.0 models.')

class VeoTuningSpec(_common.BaseModel):
    """Tuning Spec for Veo Model Tuning.

  This data type is not supported in Gemini API.
  """
    hyper_parameters: Optional[VeoHyperParameters] = Field(default=None, description='Optional. Hyperparameters for Veo.')
    training_dataset_uri: Optional[str] = Field(default=None, description='Required. Training dataset used for tuning. The dataset can be specified as either a Cloud Storage path to a JSONL file or as the resource name of a Vertex Multimodal Dataset.')
    validation_dataset_uri: Optional[str] = Field(default=None, description='Optional. Validation dataset used for tuning. The dataset can be specified as either a Cloud Storage path to a JSONL file or as the resource name of a Vertex Multimodal Dataset.')

class TuningJobMetadata(_common.BaseModel):
    """Tuning job metadata. This data type is not supported in Gemini API."""
    completed_epoch_count: Optional[int] = Field(default=None, description='Output only. The number of epochs that have been completed.')
    completed_step_count: Optional[int] = Field(default=None, description='Output only. The number of steps that have been completed. Set for Multi-Step RL.')

class VeoLoraTuningSpec(_common.BaseModel):
    """Tuning Spec for Veo LoRA Model Tuning.

  This data type is not supported in Gemini API.
  """
    hyper_parameters: Optional[VeoHyperParameters] = Field(default=None, description='Optional. Hyperparameters for Veo LoRA.')
    training_dataset_uri: Optional[str] = Field(default=None, description='Required. Training dataset used for tuning. The dataset can be specified as either a Cloud Storage path to a JSONL file or as the resource name of a Vertex Multimodal Dataset.')
    validation_dataset_uri: Optional[str] = Field(default=None, description='Optional. Validation dataset used for tuning. The dataset can be specified as either a Cloud Storage path to a JSONL file or as the resource name of a Vertex Multimodal Dataset.')
    video_orientation: Optional[VideoOrientation] = Field(default=None, description='Optional. The orientation of the video. Defaults to LANDSCAPE.')

class TuningJob(_common.BaseModel):
    """A tuning job."""
    sdk_http_response: Optional[HttpResponse] = Field(default=None, description='Used to retain the full HTTP response.')
    name: Optional[str] = Field(default=None, description='Output only. Identifier. Resource name of a TuningJob. Format: `projects/{project}/locations/{location}/tuningJobs/{tuning_job}`')
    state: Optional[JobState] = Field(default=None, description='Output only. The detailed state of the job.')
    create_time: Optional[datetime.datetime] = Field(default=None, description='Output only. Time when the TuningJob was created.')
    start_time: Optional[datetime.datetime] = Field(default=None, description='Output only. Time when the TuningJob for the first time entered the `JOB_STATE_RUNNING` state.')
    end_time: Optional[datetime.datetime] = Field(default=None, description='Output only. Time when the TuningJob entered any of the following JobStates: `JOB_STATE_SUCCEEDED`, `JOB_STATE_FAILED`, `JOB_STATE_CANCELLED`, `JOB_STATE_EXPIRED`.')
    update_time: Optional[datetime.datetime] = Field(default=None, description='Output only. Time when the TuningJob was most recently updated.')
    error: Optional[GoogleRpcStatus] = Field(default=None, description="Output only. Only populated when job's state is `JOB_STATE_FAILED` or `JOB_STATE_CANCELLED`.")
    description: Optional[str] = Field(default=None, description='Optional. The description of the TuningJob.')
    base_model: Optional[str] = Field(default=None, description='The base model that is being tuned. See [Supported models](https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/tuning#supported_models).')
    tuned_model: Optional[TunedModel] = Field(default=None, description='Output only. The tuned model resources associated with this TuningJob.')
    pre_tuned_model: Optional[PreTunedModel] = Field(default=None, description='The pre-tuned model for continuous tuning.')
    supervised_tuning_spec: Optional[SupervisedTuningSpec] = Field(default=None, description='Tuning Spec for Supervised Fine Tuning.')
    preference_optimization_spec: Optional[PreferenceOptimizationSpec] = Field(default=None, description='Tuning Spec for Preference Optimization.')
    distillation_spec: Optional[DistillationSpec] = Field(default=None, description='Tuning Spec for Distillation.')
    reinforcement_tuning_spec: Optional[ReinforcementTuningSpec] = Field(default=None, description='Tuning Spec for Reinforcement Tuning.')
    tuning_data_stats: Optional[TuningDataStats] = Field(default=None, description='Output only. The tuning data statistics associated with this TuningJob.')
    encryption_spec: Optional[EncryptionSpec] = Field(default=None, description='Customer-managed encryption key options for a TuningJob. If this is set, then all resources created by the TuningJob will be encrypted with the provided encryption key.')
    partner_model_tuning_spec: Optional[PartnerModelTuningSpec] = Field(default=None, description='Tuning Spec for open sourced and third party Partner models.')
    evaluation_config: Optional[EvaluationConfig] = Field(default=None, description='Evaluation config for the tuning job.')
    custom_base_model: Optional[str] = Field(default=None, description='Optional. The user-provided path to custom model weights. Set this field to tune a custom model. The path must be a Cloud Storage directory that contains the model weights in .safetensors format along with associated model metadata files. If this field is set, the base_model field must still be set to indicate which base model the custom model is derived from. This feature is only available for open source models.')
    evaluate_dataset_runs: Optional[list[EvaluateDatasetRun]] = Field(default=None, description='Output only. Evaluation runs for the Tuning Job.')
    experiment: Optional[str] = Field(default=None, description='Output only. The Experiment associated with this TuningJob.')
    full_fine_tuning_spec: Optional[FullFineTuningSpec] = Field(default=None, description='Tuning Spec for Full Fine Tuning.')
    labels: Optional[dict[str, str]] = Field(default=None, description='Optional. The labels with user-defined metadata to organize TuningJob and generated resources such as Model and Endpoint. Label keys and values can be no longer than 64 characters (Unicode codepoints), can only contain lowercase letters, numeric characters, underscores and dashes. International characters are allowed. See https://goo.gl/xmQnxf for more information and examples of labels.')
    output_uri: Optional[str] = Field(default=None, description='Optional. Cloud Storage path to the directory where tuning job outputs are written to. This field is only available and required for open source models.')
    pipeline_job: Optional[str] = Field(default=None, description='Output only. The resource name of the PipelineJob associated with the TuningJob. Format: `projects/{project}/locations/{location}/pipelineJobs/{pipeline_job}`.')
    service_account: Optional[str] = Field(default=None, description='The service account that the tuningJob workload runs as. If not specified, the Vertex AI Secure Fine-Tuned Service Agent in the project will be used. See https://cloud.google.com/iam/docs/service-agents#vertex-ai-secure-fine-tuning-service-agent Users starting the pipeline must have the `iam.serviceAccounts.actAs` permission on this service account.')
    tuned_model_display_name: Optional[str] = Field(default=None, description='Optional. The display name of the TunedModel. The name can be up to 128 characters long and can consist of any UTF-8 characters. For continuous tuning, tuned_model_display_name will by default use the same display name as the pre-tuned model. If a new display name is provided, the tuning job will create a new model instead of a new version.')
    tuning_job_state: Optional[TuningJobState] = Field(default=None, description='Output only. The detail state of the tuning job (while the overall `JobState` is running).')
    veo_tuning_spec: Optional[VeoTuningSpec] = Field(default=None, description='Tuning Spec for Veo Tuning.')
    tuning_job_metadata: Optional[TuningJobMetadata] = Field(default=None, description='Output only. Tuning Job metadata.')
    veo_lora_tuning_spec: Optional[VeoLoraTuningSpec] = Field(default=None, description='Tuning Spec for Veo LoRA Tuning.')
    distillation_sampling_spec: Optional[DistillationSamplingSpec] = Field(default=None, description='')
    gcs_metrics_uri: Optional[str] = Field(default=None, description='Output only. The Cloud Storage metrics URI associated with this TuningJob.')

class ListTuningJobsConfig(_common.BaseModel):
    """Configuration for the list tuning jobs method."""
    http_options: Optional[HttpOptions] = Field(default=None, description='Used to override HTTP request options.')
    page_size: Optional[int] = Field(default=None, description='')
    page_token: Optional[str] = Field(default=None, description='')
    filter: Optional[str] = Field(default=None, description='')

class _ListTuningJobsParameters(_common.BaseModel):
    """Parameters for the list tuning jobs method."""
    config: Optional[ListTuningJobsConfig] = Field(default=None, description='')

class ListTuningJobsResponse(_common.BaseModel):
    """Response for the list tuning jobs method."""
    sdk_http_response: Optional[HttpResponse] = Field(default=None, description='Used to retain the full HTTP response.')
    next_page_token: Optional[str] = Field(default=None, description='A token to retrieve the next page of results. Pass this token in a subsequent [GenAiTuningService.ListTuningJobs] call to retrieve the next page of results.')
    tuning_jobs: Optional[list[TuningJob]] = Field(default=None, description='The tuning jobs that match the request.')

class CancelTuningJobConfig(_common.BaseModel):
    """Optional parameters for tunings.cancel method."""
    http_options: Optional[HttpOptions] = Field(default=None, description='Used to override HTTP request options.')

class _CancelTuningJobParameters(_common.BaseModel):
    """Parameters for the cancel method."""
    name: Optional[str] = Field(default=None, description='The resource name of the tuning job.')
    config: Optional[CancelTuningJobConfig] = Field(default=None, description='Optional parameters for the request.')

class CancelTuningJobResponse(_common.BaseModel):
    """Empty response for tunings.cancel method."""
    sdk_http_response: Optional[HttpResponse] = Field(default=None, description='Used to retain the full HTTP response.')

class TuningExample(_common.BaseModel):
    """A single example for tuning.

  This data type is not supported in Vertex AI.
  """
    output: Optional[str] = Field(default=None, description='Required. The expected model output.')
    text_input: Optional[str] = Field(default=None, description='Optional. Text model input.')

class TuningDataset(_common.BaseModel):
    """Supervised fine-tuning training dataset."""
    gcs_uri: Optional[str] = Field(default=None, description='GCS URI of the file containing training dataset in JSONL format.')
    vertex_dataset_resource: Optional[str] = Field(default=None, description="The resource name of the Gemini Enterprise Agent Platform (previously known as Vertex AI) Multimodal Dataset that is used as training dataset. Example: 'projects/my-project-id-or-number/locations/my-location/datasets/my-dataset-id'.")
    examples: Optional[list[TuningExample]] = Field(default=None, description='Inline examples with simple input/output text.')

class TuningValidationDataset(_common.BaseModel):
    gcs_uri: Optional[str] = Field(default=None, description='GCS URI of the file containing validation dataset in JSONL format.')
    vertex_dataset_resource: Optional[str] = Field(default=None, description="The resource name of the Gemini Enterprise Agent Platform (previously known as Vertex AI) Multimodal Dataset that is used as validation dataset. Example: 'projects/my-project-id-or-number/locations/my-location/datasets/my-dataset-id'.")

class CreateTuningJobConfig(_common.BaseModel):
    """Fine-tuning job creation request - optional fields."""
    http_options: Optional[HttpOptions] = Field(default=None, description='Used to override HTTP request options.')
    method: Optional[TuningMethod] = Field(default=None, description='The method to use for tuning (SUPERVISED_FINE_TUNING or PREFERENCE_TUNING or DISTILLATION or REINFORCEMENT_TUNING). If not set, the default method (SFT) will be used.')
    validation_dataset: Optional[TuningValidationDataset] = Field(default=None, description='Validation dataset for tuning. The dataset must be formatted as a JSONL file.')
    tuned_model_display_name: Optional[str] = Field(default=None, description='The display name of the tuned Model. The name can be up to 128 characters long and can consist of any UTF-8 characters.')
    description: Optional[str] = Field(default=None, description='The description of the TuningJob')
    epoch_count: Optional[int] = Field(default=None, description='Number of complete passes the model makes over the entire training dataset during training.')
    learning_rate_multiplier: Optional[float] = Field(default=None, description='Multiplier for adjusting the default learning rate. 1P models only. Mutually exclusive with learning_rate.')
    export_last_checkpoint_only: Optional[bool] = Field(default=None, description='If set to true, disable intermediate checkpoints and only the last checkpoint will be exported. Otherwise, enable intermediate checkpoints.')
    pre_tuned_model_checkpoint_id: Optional[str] = Field(default=None, description='The optional checkpoint id of the pre-tuned model to use for tuning, if applicable.')
    adapter_size: Optional[AdapterSize] = Field(default=None, description='Adapter size for tuning.')
    tuning_mode: Optional[TuningMode] = Field(default=None, description='Tuning mode for tuning.')
    custom_base_model: Optional[str] = Field(default=None, description='Custom base model for tuning. This is only supported for OSS models in Gemini Enterprise Agent Platform.')
    batch_size: Optional[int] = Field(default=None, description='The batch size hyperparameter for tuning. This is only supported for OSS models in Gemini Enterprise Agent Platform.')
    learning_rate: Optional[float] = Field(default=None, description='The learning rate for tuning. OSS models only. Mutually exclusive with learning_rate_multiplier.')
    evaluation_config: Optional[EvaluationConfig] = Field(default=None, description='Evaluation config for the tuning job.')
    labels: Optional[dict[str, str]] = Field(default=None, description='Optional. The labels with user-defined metadata to organize TuningJob and generated resources such as Model and Endpoint. Label keys and values can be no longer than 64 characters (Unicode codepoints), can only contain lowercase letters, numeric characters, underscores and dashes. International characters are allowed. See https://goo.gl/xmQnxf for more information and examples of labels.')
    beta: Optional[float] = Field(default=None, description='Weight for KL Divergence regularization, Preference Optimization tuning only.')
    base_teacher_model: Optional[str] = Field(default=None, description='The base teacher model that is being distilled. Distillation only.')
    tuned_teacher_model_source: Optional[str] = Field(default=None, description='The resource name of the Tuned teacher model. Distillation only.')
    sft_loss_weight_multiplier: Optional[float] = Field(default=None, description='Multiplier for adjusting the weight of the SFT loss. Distillation only.')
    output_uri: Optional[str] = Field(default=None, description='The Google Cloud Storage location where the tuning job outputs are written.')
    encryption_spec: Optional[EncryptionSpec] = Field(default=None, description='The encryption spec of the tuning job. Customer-managed encryption key options for a TuningJob. If this is set, then all resources created by the TuningJob will be encrypted with provided encryption key.')
    reward_config: Optional[SingleReinforcementTuningRewardConfig] = Field(default=None, description='Reward function configuration for reinforcement tuning. Reinforcement tuning only.')
    composite_reward_config: Optional[CompositeReinforcementTuningRewardConfig] = Field(default=None, description='Composite reward function configuration for reinforcement tuning. Reinforcement tuning only.')
    samples_per_prompt: Optional[int] = Field(default=None, description='Number of different responses to generate per prompt during tuning. Reinforcement tuning only.')
    evaluate_interval: Optional[int] = Field(default=None, description='How often at steps to evaluate the tuning job during training. Reinforcement tuning only.')
    checkpoint_interval: Optional[int] = Field(default=None, description='How often at steps to save checkpoints during training. Reinforcement tuning only.')
    max_output_tokens: Optional[int] = Field(default=None, description='The maximum number of tokens to generate per prompt. Reinforcement tuning only.')
    thinking_level: Optional[ReinforcementTuningThinkingLevel] = Field(default=None, description='Indicates the maximum thinking depth. Use with earlier models shall result in error. Reinforcement tuning only.')
    validation_dataset_uri: Optional[str] = Field(default=None, description='Cloud Storage path to file containing validation dataset for tuning. The dataset must be formatted as a JSONL file. If no validation dataset is provided, by default the API splits 25% of the training dataset or 50 examples, whichever is larger, as the validation dataset. Reinforcement tuning only.')

class _CreateTuningJobParametersPrivate(_common.BaseModel):
    """Fine-tuning job creation parameters - optional fields."""
    base_model: Optional[str] = Field(default=None, description='The base model that is being tuned, e.g., "gemini-flash-latest".')
    pre_tuned_model: Optional[PreTunedModel] = Field(default=None, description='The PreTunedModel that is being tuned.')
    training_dataset: Optional[TuningDataset] = Field(default=None, description='Cloud Storage path to file containing training dataset for tuning. The dataset must be formatted as a JSONL file.')
    config: Optional[CreateTuningJobConfig] = Field(default=None, description='Configuration for the tuning job.')

class TuningOperation(_common.BaseModel):
    """A long-running operation."""
    sdk_http_response: Optional[HttpResponse] = Field(default=None, description='Used to retain the full HTTP response.')
    name: Optional[str] = Field(default=None, description='The server-assigned name, which is only unique within the same service that originally returns it. If you use the default HTTP mapping, the `name` should be a resource name ending with `operations/{unique_id}`.')
    metadata: Optional[dict[str, Any]] = Field(default=None, description='Service-specific metadata associated with the operation. It typically contains progress information and common metadata such as create time. Some services might not provide such metadata.  Any method that returns a long-running operation should document the metadata type, if any.')
    done: Optional[bool] = Field(default=None, description='If the value is `false`, it means the operation is still in progress. If `true`, the operation is completed, and either `error` or `response` is available.')
    error: Optional[dict[str, Any]] = Field(default=None, description='The error result of the operation in case of failure or cancellation.')

class ValidateRewardConfig(_common.BaseModel):
    """Optional parameters for tunings.validate_reward."""
    http_options: Optional[HttpOptions] = Field(default=None, description='Used to override HTTP request options.')

class _ValidateRewardParameters(_common.BaseModel):
    """Parameters for the validate_reward method.

  Validates a reinforcement tuning reward configuration against a sample
  response and example before creating a reinforcement tuning job.
  """
    parent: Optional[str] = Field(default=None, description='Required. The resource name of the Location to validate the reward in, e.g. `projects/{project}/locations/{location}`.')
    sample_response: Optional[Content] = Field(default=None, description='Required. The sample response for validating the reward configuration.')
    example: Optional[ReinforcementTuningExample] = Field(default=None, description='Required. The example to validate the reward configuration.')
    single_reward_config: Optional[SingleReinforcementTuningRewardConfig] = Field(default=None, description='Single reward function configuration for reinforcement tuning. Mutually exclusive with composite_reward_config.')
    composite_reward_config: Optional[CompositeReinforcementTuningRewardConfig] = Field(default=None, description='Composite reward function configuration for reinforcement tuning. Mutually exclusive with single_reward_config.')
    config: Optional[ValidateRewardConfig] = Field(default=None, description='Optional parameters for the request.')

class ReinforcementTuningRewardInfo(_common.BaseModel):
    """The reward info for a reward function."""
    reward: Optional[float] = Field(default=None, description='Output only. The calculated reward for the reward function.')
    user_requested_aux_info: Optional[str] = Field(default=None, description='Output only. The user-requested auxiliary info for the reward function. This field is set only if the Cloud Run reward function configured by user returns a "user_requested_aux_info". Refer to ReinforcementTuningCloudRunRewardScorer for more details.')
    error_status: Optional[GoogleRpcStatus] = Field(default=None, description='Output only. In case of an error for this reward, this field will be populated with a detailed error status.')

class ValidateRewardResponse(_common.BaseModel):
    """Response for the validate_reward method.

  Contains the computed reward for a reinforcement tuning reward
  configuration.
  """
    sdk_http_response: Optional[HttpResponse] = Field(default=None, description='Used to retain the full HTTP response.')
    overall_reward: Optional[float] = Field(default=None, description='Output only. The overall weighted reward. For a `CompositeReinforcementTuningRewardConfig`, this is the weighted average of all rewards. For a `SingleReinforcementTuningRewardConfig`, this will be the value of the single reward.')
    error: Optional[str] = Field(default=None, description='Output only. In case of an error, this field will be populated with a detailed error message to help with debugging.')
    reward_info_details: Optional[dict[str, ReinforcementTuningRewardInfo]] = Field(default=None, description='A map from reward name to reward info.')

class CreateCachedContentConfig(_common.BaseModel):
    """Optional configuration for cached content creation."""
    http_options: Optional[HttpOptions] = Field(default=None, description='Used to override HTTP request options.')
    ttl: Optional[str] = Field(default=None, description='The TTL for this resource. The expiration time is computed: now + TTL. It is a duration string, with up to nine fractional digits, terminated by \'s\'. Example: "3.5s".')
    expire_time: Optional[datetime.datetime] = Field(default=None, description='Timestamp of when this resource is considered expired. Uses RFC 3339 format, Example: 2014-10-02T15:01:23Z.')
    display_name: Optional[str] = Field(default=None, description='The user-generated meaningful display name of the cached content.\n      ')
    contents: Optional[ContentListUnion] = Field(default=None, description='The content to cache.\n      ')
    system_instruction: Optional[ContentUnion] = Field(default=None, description='Developer set system instruction.\n      ')
    tools: Optional[list[Tool]] = Field(default=None, description='A list of `Tools` the model may use to generate the next response.\n      ')
    tool_config: Optional[ToolConfig] = Field(default=None, description='Configuration for the tools to use. This config is shared for all tools.\n      ')
    kms_key_name: Optional[str] = Field(default=None, description='The Cloud KMS resource identifier of the customer managed\n      encryption key used to protect a resource.\n      The key needs to be in the same region as where the compute resource is\n      created. See\n      https://cloud.google.com/vertex-ai/docs/general/cmek for more\n      details. If this is set, then all created CachedContent objects\n      will be encrypted with the provided encryption key.\n      Allowed formats: projects/{project}/locations/{location}/keyRings/{key_ring}/cryptoKeys/{crypto_key}\n      ')

class _CreateCachedContentParameters(_common.BaseModel):
    """Parameters for caches.create method."""
    model: Optional[str] = Field(default=None, description='ID of the model to use. Example: gemini-flash-latest')
    config: Optional[CreateCachedContentConfig] = Field(default=None, description='Configuration that contains optional parameters.\n      ')

class CachedContentUsageMetadata(_common.BaseModel):
    """Metadata on the usage of the cached content."""
    audio_duration_seconds: Optional[int] = Field(default=None, description='Duration of audio in seconds. This field is not supported in Gemini API.')
    image_count: Optional[int] = Field(default=None, description='Number of images. This field is not supported in Gemini API.')
    text_count: Optional[int] = Field(default=None, description='Number of text characters. This field is not supported in Gemini API.')
    total_token_count: Optional[int] = Field(default=None, description='Total number of tokens that the cached content consumes.')
    video_duration_seconds: Optional[int] = Field(default=None, description='Duration of video in seconds. This field is not supported in Gemini API.')

class CachedContent(_common.BaseModel):
    """A resource used in LLM queries for users to explicitly specify what to cache."""
    name: Optional[str] = Field(default=None, description='The server-generated resource name of the cached content.')
    display_name: Optional[str] = Field(default=None, description='The user-generated meaningful display name of the cached content.')
    model: Optional[str] = Field(default=None, description='The name of the publisher model to use for cached content.')
    create_time: Optional[datetime.datetime] = Field(default=None, description='Creation time of the cache entry.')
    update_time: Optional[datetime.datetime] = Field(default=None, description='When the cache entry was last updated in UTC time.')
    expire_time: Optional[datetime.datetime] = Field(default=None, description='Expiration time of the cached content.')
    usage_metadata: Optional[CachedContentUsageMetadata] = Field(default=None, description='Metadata on the usage of the cached content.')

class GetCachedContentConfig(_common.BaseModel):
    """Optional parameters for caches.get method."""
    http_options: Optional[HttpOptions] = Field(default=None, description='Used to override HTTP request options.')

class _GetCachedContentParameters(_common.BaseModel):
    """Parameters for caches.get method."""
    name: Optional[str] = Field(default=None, description='The server-generated resource name of the cached content.\n      ')
    config: Optional[GetCachedContentConfig] = Field(default=None, description='Optional parameters for the request.\n      ')

class DeleteCachedContentConfig(_common.BaseModel):
    """Optional parameters for caches.delete method."""
    http_options: Optional[HttpOptions] = Field(default=None, description='Used to override HTTP request options.')

class _DeleteCachedContentParameters(_common.BaseModel):
    """Parameters for caches.delete method."""
    name: Optional[str] = Field(default=None, description='The server-generated resource name of the cached content.\n      ')
    config: Optional[DeleteCachedContentConfig] = Field(default=None, description='Optional parameters for the request.\n      ')

class DeleteCachedContentResponse(_common.BaseModel):
    """Empty response for caches.delete method."""
    sdk_http_response: Optional[HttpResponse] = Field(default=None, description='Used to retain the full HTTP response.')

class UpdateCachedContentConfig(_common.BaseModel):
    """Optional parameters for caches.update method."""
    http_options: Optional[HttpOptions] = Field(default=None, description='Used to override HTTP request options.')
    ttl: Optional[str] = Field(default=None, description='The TTL for this resource. The expiration time is computed: now + TTL. It is a duration string, with up to nine fractional digits, terminated by \'s\'. Example: "3.5s".')
    expire_time: Optional[datetime.datetime] = Field(default=None, description='Timestamp of when this resource is considered expired. Uses RFC 3339 format, Example: 2014-10-02T15:01:23Z.')

class _UpdateCachedContentParameters(_common.BaseModel):
    name: Optional[str] = Field(default=None, description='The server-generated resource name of the cached content.\n      ')
    config: Optional[UpdateCachedContentConfig] = Field(default=None, description='Configuration that contains optional parameters.\n      ')

class ListCachedContentsConfig(_common.BaseModel):
    """Config for caches.list method."""
    http_options: Optional[HttpOptions] = Field(default=None, description='Used to override HTTP request options.')
    page_size: Optional[int] = Field(default=None, description='')
    page_token: Optional[str] = Field(default=None, description='')

class _ListCachedContentsParameters(_common.BaseModel):
    """Parameters for caches.list method."""
    config: Optional[ListCachedContentsConfig] = Field(default=None, description='Configuration that contains optional parameters.\n      ')

class ListCachedContentsResponse(_common.BaseModel):
    sdk_http_response: Optional[HttpResponse] = Field(default=None, description='Used to retain the full HTTP response.')
    next_page_token: Optional[str] = Field(default=None, description='')
    cached_contents: Optional[list[CachedContent]] = Field(default=None, description='List of cached contents.\n      ')

class GetDocumentConfig(_common.BaseModel):
    """Optional Config."""
    http_options: Optional[HttpOptions] = Field(default=None, description='Used to override HTTP request options.')

class _GetDocumentParameters(_common.BaseModel):
    """Parameters for documents.get."""
    name: Optional[str] = Field(default=None, description='The resource name of the Document.\n    Example: fileSearchStores/file-search-store-foo/documents/documents-bar')
    config: Optional[GetDocumentConfig] = Field(default=None, description='Optional parameters for the request.')

class StringList(_common.BaseModel):
    """User provided string values assigned to a single metadata key.

  This data type is not supported in Vertex AI.
  """
    values: Optional[list[str]] = Field(default=None, description='The string values of the metadata to store.')

class CustomMetadata(_common.BaseModel):
    """User provided metadata stored as key-value pairs.

  This data type is not supported in Vertex AI.
  """
    key: Optional[str] = Field(default=None, description='Required. The key of the metadata to store.')
    numeric_value: Optional[float] = Field(default=None, description='The numeric value of the metadata to store.')
    string_list_value: Optional[StringList] = Field(default=None, description='The StringList value of the metadata to store.')
    string_value: Optional[str] = Field(default=None, description='The string value of the metadata to store.')

class Document(_common.BaseModel):
    """A Document is a collection of Chunks."""
    name: Optional[str] = Field(default=None, description='Immutable. Identifier. The `Document` resource name. The ID (name excluding the "fileSearchStores/&#42;/documents/" prefix) can contain up to 40 characters that are lowercase alphanumeric or dashes (-). The ID cannot start or end with a dash. If the name is empty on create, a unique name will be derived from `display_name` along with a 12 character random suffix. Example: `fileSearchStores/{file_search_store_id}/documents/my-awesome-doc-123a456b789c`')
    display_name: Optional[str] = Field(default=None, description='Optional. The human-readable display name for the `Document`. The display name must be no more than 512 characters in length, including spaces. Example: "Semantic Retriever Documentation".')
    state: Optional[DocumentState] = Field(default=None, description='Output only. Current state of the `Document`.')
    size_bytes: Optional[int] = Field(default=None, description='Output only. The size of raw bytes ingested into the Document.')
    mime_type: Optional[str] = Field(default=None, description='Output only. The mime type of the Document.')
    create_time: Optional[datetime.datetime] = Field(default=None, description='Output only. The Timestamp of when the `Document` was created.')
    custom_metadata: Optional[list[CustomMetadata]] = Field(default=None, description='Optional. User provided custom metadata stored as key-value pairs used for querying. A `Document` can have a maximum of 20 `CustomMetadata`.')
    update_time: Optional[datetime.datetime] = Field(default=None, description='Output only. The Timestamp of when the `Document` was last updated.')

class DeleteDocumentConfig(_common.BaseModel):
    """Config for optional parameters."""
    http_options: Optional[HttpOptions] = Field(default=None, description='Used to override HTTP request options.')
    force: Optional[bool] = Field(default=None, description='If set to true, any `Chunk`s and objects related to this `Document` will\n      also be deleted.\n      ')

class _DeleteDocumentParameters(_common.BaseModel):
    """Config for documents.delete parameters."""
    name: Optional[str] = Field(default=None, description='The resource name of the Document.\n    Example: fileSearchStores/file-search-store-foo/documents/documents-bar')
    config: Optional[DeleteDocumentConfig] = Field(default=None, description='Optional parameters for the request.')

class ListDocumentsConfig(_common.BaseModel):
    """Config for optional parameters."""
    http_options: Optional[HttpOptions] = Field(default=None, description='Used to override HTTP request options.')
    page_size: Optional[int] = Field(default=None, description='')
    page_token: Optional[str] = Field(default=None, description='')

class _ListDocumentsParameters(_common.BaseModel):
    """Config for documents.list parameters."""
    parent: Optional[str] = Field(default=None, description='The resource name of the FileSearchStores. Example: `fileSearchStore/file-search-store-foo`')
    config: Optional[ListDocumentsConfig] = Field(default=None, description='')

class ListDocumentsResponse(_common.BaseModel):
    """Config for documents.list return value."""
    sdk_http_response: Optional[HttpResponse] = Field(default=None, description='Used to retain the full HTTP response.')
    next_page_token: Optional[str] = Field(default=None, description='A token, which can be sent as `page_token` to retrieve the next page. If this field is omitted, there are no more pages.')
    documents: Optional[list[Document]] = Field(default=None, description='The returned `Document`s.')

class CreateFileSearchStoreConfig(_common.BaseModel):
    """Optional parameters for creating a file search store."""
    http_options: Optional[HttpOptions] = Field(default=None, description='Used to override HTTP request options.')
    display_name: Optional[str] = Field(default=None, description='The human-readable display name for the file search store.\n      ')
    embedding_model: Optional[str] = Field(default=None, description='The embedding model to use for the FileSearchStore.\n      Format: `models/{model}`. If not specified, the default embedding model will be used.\n      ')

class _CreateFileSearchStoreParameters(_common.BaseModel):
    """Config for file_search_stores.create parameters."""
    config: Optional[CreateFileSearchStoreConfig] = Field(default=None, description='Optional parameters for creating a file search store.\n      ')

class FileSearchStore(_common.BaseModel):
    """A collection of Documents."""
    name: Optional[str] = Field(default=None, description='Output only. Immutable. Identifier. The `FileSearchStore` resource name. It is an ID (name excluding the "fileSearchStores/" prefix) that can contain up to 40 characters that are lowercase alphanumeric or dashes (-). It is output only. The unique name will be derived from `display_name` along with a 12 character random suffix. Example: `fileSearchStores/my-awesome-file-search-store-123a456b789c` If `display_name` is not provided, the name will be randomly generated.')
    display_name: Optional[str] = Field(default=None, description='Optional. The human-readable display name for the `FileSearchStore`. The display name must be no more than 512 characters in length, including spaces. Example: "Docs on Semantic Retriever".')
    create_time: Optional[datetime.datetime] = Field(default=None, description='Output only. The Timestamp of when the `FileSearchStore` was created.')
    update_time: Optional[datetime.datetime] = Field(default=None, description='Output only. The Timestamp of when the `FileSearchStore` was last updated.')
    active_documents_count: Optional[int] = Field(default=None, description='Output only. The number of documents in the `FileSearchStore` that are active and ready for retrieval.')
    pending_documents_count: Optional[int] = Field(default=None, description='Output only. The number of documents in the `FileSearchStore` that are being processed.')
    failed_documents_count: Optional[int] = Field(default=None, description='Output only. The number of documents in the `FileSearchStore` that have failed processing.')
    size_bytes: Optional[int] = Field(default=None, description='Output only. The size of raw bytes ingested into the `FileSearchStore`. This is the total size of all the documents in the `FileSearchStore`.')
    embedding_model: Optional[str] = Field(default=None, description='The embedding model used by the FileSearchStore.')

class GetFileSearchStoreConfig(_common.BaseModel):
    """Optional parameters for getting a FileSearchStore."""
    http_options: Optional[HttpOptions] = Field(default=None, description='Used to override HTTP request options.')

class _GetFileSearchStoreParameters(_common.BaseModel):
    """Config for file_search_stores.get parameters."""
    name: Optional[str] = Field(default=None, description='The resource name of the FileSearchStore. Example: `fileSearchStores/my-file-search-store-123`')
    config: Optional[GetFileSearchStoreConfig] = Field(default=None, description='Optional parameters for the request.')

class DeleteFileSearchStoreConfig(_common.BaseModel):
    """Optional parameters for deleting a FileSearchStore."""
    http_options: Optional[HttpOptions] = Field(default=None, description='Used to override HTTP request options.')
    force: Optional[bool] = Field(default=None, description='If set to true, any Documents and objects related to this FileSearchStore will also be deleted.\n      If false (the default), a FAILED_PRECONDITION error will be returned if\n      the FileSearchStore contains any Documents.\n      ')

class _DeleteFileSearchStoreParameters(_common.BaseModel):
    """Config for file_search_stores.delete parameters."""
    name: Optional[str] = Field(default=None, description='The resource name of the FileSearchStore. Example: `fileSearchStores/my-file-search-store-123`')
    config: Optional[DeleteFileSearchStoreConfig] = Field(default=None, description='Optional parameters for the request.')

class ListFileSearchStoresConfig(_common.BaseModel):
    """Optional parameters for listing FileSearchStore."""
    http_options: Optional[HttpOptions] = Field(default=None, description='Used to override HTTP request options.')
    page_size: Optional[int] = Field(default=None, description='')
    page_token: Optional[str] = Field(default=None, description='')

class _ListFileSearchStoresParameters(_common.BaseModel):
    """Config for file_search_stores.list parameters."""
    config: Optional[ListFileSearchStoresConfig] = Field(default=None, description='Optional parameters for the list request.')

class ListFileSearchStoresResponse(_common.BaseModel):
    """Config for file_search_stores.list return value."""
    sdk_http_response: Optional[HttpResponse] = Field(default=None, description='Used to retain the full HTTP response.')
    next_page_token: Optional[str] = Field(default=None, description='A token, which can be sent as `page_token` to retrieve the next page. If this field is omitted, there are no more pages.')
    file_search_stores: Optional[list[FileSearchStore]] = Field(default=None, description='The returned file search stores.')

class WhiteSpaceConfig(_common.BaseModel):
    """Configuration for a white space chunking algorithm."""
    max_tokens_per_chunk: Optional[int] = Field(default=None, description='Maximum number of tokens per chunk.')
    max_overlap_tokens: Optional[int] = Field(default=None, description='Maximum number of overlapping tokens between two adjacent chunks.')

class ChunkingConfig(_common.BaseModel):
    """Config for telling the service how to chunk the file."""
    white_space_config: Optional[WhiteSpaceConfig] = Field(default=None, description='White space chunking configuration.')

class UploadToFileSearchStoreConfig(_common.BaseModel):
    """Optional parameters for uploading a file to a FileSearchStore."""
    http_options: Optional[HttpOptions] = Field(default=None, description='Used to override HTTP request options.')
    should_return_http_response: Optional[bool] = Field(default=None, description=" If true, the raw HTTP response will be returned in the 'sdk_http_response' field.")
    mime_type: Optional[str] = Field(default=None, description='MIME type of the file to be uploaded. If not provided, it will be inferred from the file extension.')
    display_name: Optional[str] = Field(default=None, description='Display name of the created document.')
    custom_metadata: Optional[list[CustomMetadata]] = Field(default=None, description='User provided custom metadata stored as key-value pairs used for querying.')
    chunking_config: Optional[ChunkingConfig] = Field(default=None, description='Config for telling the service how to chunk the file.')

class _UploadToFileSearchStoreParameters(_common.BaseModel):
    """Generates the parameters for the private _upload_to_file_search_store method."""
    file_search_store_name: Optional[str] = Field(default=None, description='The resource name of the FileSearchStore. Example: `fileSearchStores/my-file-search-store-123`')
    config: Optional[UploadToFileSearchStoreConfig] = Field(default=None, description='Used to override the default configuration.')

class UploadToFileSearchStoreResumableResponse(_common.BaseModel):
    """Response for the resumable upload method."""
    sdk_http_response: Optional[HttpResponse] = Field(default=None, description='Used to retain the full HTTP response.')

class ImportFileConfig(_common.BaseModel):
    """Optional parameters for importing a file."""
    http_options: Optional[HttpOptions] = Field(default=None, description='Used to override HTTP request options.')
    custom_metadata: Optional[list[CustomMetadata]] = Field(default=None, description='User provided custom metadata stored as key-value pairs used for querying.')
    chunking_config: Optional[ChunkingConfig] = Field(default=None, description='Config for telling the service how to chunk the file.')

class _ImportFileParameters(_common.BaseModel):
    """Config for file_search_stores.import_file parameters."""
    file_search_store_name: Optional[str] = Field(default=None, description='The resource name of the FileSearchStore. Example: `fileSearchStores/my-file-search-store-123`')
    file_name: Optional[str] = Field(default=None, description='The name of the File API File to import. Example: `files/abc-123`')
    config: Optional[ImportFileConfig] = Field(default=None, description='Optional parameters for the request.')

class ImportFileResponse(_common.BaseModel):
    """Response for ImportFile to import a File API file with a file search store."""
    sdk_http_response: Optional[HttpResponse] = Field(default=None, description='Used to retain the full HTTP response.')
    parent: Optional[str] = Field(default=None, description='The name of the FileSearchStore containing Documents.')
    document_name: Optional[str] = Field(default=None, description='The identifier for the Document imported.')

class ImportFileOperation(_common.BaseModel, Operation):
    """Long-running operation for importing a file to a FileSearchStore."""
    response: Optional[ImportFileResponse] = Field(default=None, description='The result of the ImportFile operation, available when the operation is done.')

class ListFilesConfig(_common.BaseModel):
    """Used to override the default configuration."""
    http_options: Optional[HttpOptions] = Field(default=None, description='Used to override HTTP request options.')
    page_size: Optional[int] = Field(default=None, description='')
    page_token: Optional[str] = Field(default=None, description='')

class _ListFilesParameters(_common.BaseModel):
    """Generates the parameters for the list method."""
    config: Optional[ListFilesConfig] = Field(default=None, description='Used to override the default configuration.')

class ListFilesResponse(_common.BaseModel):
    """Response for the list files method."""
    sdk_http_response: Optional[HttpResponse] = Field(default=None, description='Used to retain the full HTTP response.')
    next_page_token: Optional[str] = Field(default=None, description='A token that can be sent as a `page_token` into a subsequent `ListFiles` call.')
    files: Optional[list[File]] = Field(default=None, description='The list of `File`s.')

class CreateFileConfig(_common.BaseModel):
    """Used to override the default configuration."""
    http_options: Optional[HttpOptions] = Field(default=None, description='Used to override HTTP request options.')
    should_return_http_response: Optional[bool] = Field(default=None, description=" If true, the raw HTTP response will be returned in the 'sdk_http_response' field.")

class _CreateFileParameters(_common.BaseModel):
    """Generates the parameters for the private _create method."""
    file: Optional[File] = Field(default=None, description="The file to be uploaded.\n            mime_type: (Required) The MIME type of the file. Must be provided.\n            name: (Optional) The name of the file in the destination (e.g.\n            'files/sample-image').\n            display_name: (Optional) The display name of the file.\n      ")
    config: Optional[CreateFileConfig] = Field(default=None, description='Used to override the default configuration.')

class CreateFileResponse(_common.BaseModel):
    """Response for the create file method."""
    sdk_http_response: Optional[HttpResponse] = Field(default=None, description='Used to retain the full HTTP response.')

class GetFileConfig(_common.BaseModel):
    """Used to override the default configuration."""
    http_options: Optional[HttpOptions] = Field(default=None, description='Used to override HTTP request options.')

class _GetFileParameters(_common.BaseModel):
    """Generates the parameters for the get method."""
    name: Optional[str] = Field(default=None, description='The name identifier for the file to retrieve.')
    config: Optional[GetFileConfig] = Field(default=None, description='Used to override the default configuration.')

class DeleteFileConfig(_common.BaseModel):
    """Used to override the default configuration."""
    http_options: Optional[HttpOptions] = Field(default=None, description='Used to override HTTP request options.')

class _DeleteFileParameters(_common.BaseModel):
    """Generates the parameters for the get method."""
    name: Optional[str] = Field(default=None, description='The name identifier for the file to be deleted.')
    config: Optional[DeleteFileConfig] = Field(default=None, description='Used to override the default configuration.')

class DeleteFileResponse(_common.BaseModel):
    """Response for the delete file method."""
    sdk_http_response: Optional[HttpResponse] = Field(default=None, description='Used to retain the full HTTP response.')

class RegisterFilesConfig(_common.BaseModel):
    """Used to override the default configuration."""
    http_options: Optional[HttpOptions] = Field(default=None, description='Used to override HTTP request options.')
    should_return_http_response: Optional[bool] = Field(default=None, description=" If true, the raw HTTP response will be returned in the 'sdk_http_response' field.")

class _InternalRegisterFilesParameters(_common.BaseModel):
    """Parameters for the private _Register method."""
    uris: Optional[list[str]] = Field(default=None, description='The Google Cloud Storage URIs to register. Example: `gs://bucket/object`.')
    config: Optional[RegisterFilesConfig] = Field(default=None, description='Used to override the default configuration.')

class RegisterFilesResponse(_common.BaseModel):
    """Response for the _register file method."""
    sdk_http_response: Optional[HttpResponse] = Field(default=None, description='Used to retain the full HTTP response.')
    files: Optional[list[File]] = Field(default=None, description='The registered files.')

class InlinedRequest(_common.BaseModel):
    """Config for inlined request."""
    model: Optional[str] = Field(default=None, description='ID of the model to use. For a list of models, see `Google models\n      <https://cloud.google.com/vertex-ai/generative-ai/docs/learn/models>`_.')
    contents: Optional[ContentListUnion] = Field(default=None, description='Content of the request.\n      ')
    metadata: Optional[dict[str, str]] = Field(default=None, description='The metadata to be associated with the request.')
    config: Optional[GenerateContentConfig] = Field(default=None, description='Configuration that contains optional model parameters.\n      ')

class BatchJobSource(_common.BaseModel):
    """Config for `src` parameter."""
    format: Optional[str] = Field(default=None, description="Storage format of the input files. Must be one of:\n      'jsonl', 'bigquery', 'vertex-dataset'.\n      ")
    gcs_uri: Optional[list[str]] = Field(default=None, description='The Google Cloud Storage URIs to input files.\n      ')
    bigquery_uri: Optional[str] = Field(default=None, description='The BigQuery URI to input table.\n      ')
    file_name: Optional[str] = Field(default=None, description='The Gemini Developer API\'s file resource name of the input data\n      (e.g. "files/12345").\n      ')
    inlined_requests: Optional[list[InlinedRequest]] = Field(default=None, description="The Gemini Developer API's inlined input data to run batch job.\n      ")
    vertex_dataset_name: Optional[str] = Field(default=None, description='This field is experimental and may change in future versions. The Vertex AI dataset resource name to use as input. Must be of type multimodal.\n      ')

class VertexMultimodalDatasetDestination(_common.BaseModel):
    """This class is experimental and may change in future versions.

  The specification for an output Vertex AI multimodal dataset.
  """
    bigquery_destination: Optional[str] = Field(default=None, description='The BigQuery destination for the multimodal dataset.')
    display_name: Optional[str] = Field(default=None, description='The display name of the multimodal dataset.')

class JobError(_common.BaseModel):
    """Job error."""
    details: Optional[list[str]] = Field(default=None, description='A list of messages that carry the error details. There is a common set of message types for APIs to use.')
    code: Optional[int] = Field(default=None, description='The status code.')
    message: Optional[str] = Field(default=None, description='A developer-facing error message, which should be in English. Any user-facing error message should be localized and sent in the `details` field.')

class InlinedResponse(_common.BaseModel):
    """Config for `inlined_responses` parameter."""
    response: Optional[GenerateContentResponse] = Field(default=None, description='The response to the request.\n      ')
    metadata: Optional[dict[str, str]] = Field(default=None, description='The metadata to be associated with the request.')
    error: Optional[JobError] = Field(default=None, description='The error encountered while processing the request.\n      ')

class SingleEmbedContentResponse(_common.BaseModel):
    """Config for `response` parameter."""
    embedding: Optional[ContentEmbedding] = Field(default=None, description='The response to the request.\n      ')
    token_count: Optional[int] = Field(default=None, description='The error encountered while processing the request.\n      ')

class InlinedEmbedContentResponse(_common.BaseModel):
    """Config for `inlined_embedding_responses` parameter."""
    response: Optional[SingleEmbedContentResponse] = Field(default=None, description='Output only. The response to the request.')
    error: Optional[JobError] = Field(default=None, description='Output only. The error encountered while processing the request.')
    metadata: Optional[dict[str, Any]] = Field(default=None, description='Output only. The metadata associated with the request.')

class BatchJobDestination(_common.BaseModel):
    """Config for `dest` parameter."""
    format: Optional[str] = Field(default=None, description="Storage format of the output files. Must be one of:\n      'jsonl', 'bigquery', 'vertex-dataset'.\n      ")
    gcs_uri: Optional[str] = Field(default=None, description='The Google Cloud Storage URI to the output file.\n      ')
    bigquery_uri: Optional[str] = Field(default=None, description='The BigQuery URI to the output table.\n      ')
    file_name: Optional[str] = Field(default=None, description='The Gemini Developer API\'s file resource name of the output data\n      (e.g. "files/12345"). The file will be a JSONL file with a single response\n      per line. The responses will be GenerateContentResponse messages formatted\n      as JSON. The responses will be written in the same order as the input\n      requests.\n      ')
    inlined_responses: Optional[list[InlinedResponse]] = Field(default=None, description='The responses to the requests in the batch. Returned when the batch was\n      built using inlined requests. The responses will be in the same order as\n      the input requests.\n      ')
    inlined_embed_content_responses: Optional[list[InlinedEmbedContentResponse]] = Field(default=None, description='The responses to the requests in the batch. Returned when the batch was\n      built using inlined requests. The responses will be in the same order as\n      the input requests.\n      ')
    vertex_dataset: Optional[VertexMultimodalDatasetDestination] = Field(default=None, description='This field is experimental and may change in future versions. The Vertex AI dataset destination.\n      ')
BatchJobDestinationUnion = Union[BatchJobDestination, str]

class CreateBatchJobConfig(_common.BaseModel):
    """Config for optional parameters."""
    http_options: Optional[HttpOptions] = Field(default=None, description='Used to override HTTP request options.')
    display_name: Optional[str] = Field(default=None, description='The user-defined name of this BatchJob.\n      ')
    dest: Optional[BatchJobDestinationUnion] = Field(default=None, description='GCS or BigQuery URI prefix for the output predictions. Example:\n      "gs://path/to/output/data" or "bq://projectId.bqDatasetId.bqTableId".\n      ')
    webhook_config: Optional[WebhookConfig] = Field(default=None, description='Webhook configuration for receiving notifications when the batch\n      operation completes.\n      ')
BatchJobSourceUnion = Union[BatchJobSource, list[InlinedRequest], str]

class _CreateBatchJobParameters(_common.BaseModel):
    """Config for batches.create parameters."""
    model: Optional[str] = Field(default=None, description='The name of the model to produces the predictions via the BatchJob.\n      ')
    src: Optional[BatchJobSourceUnion] = Field(default=None, description='GCS URI(-s) or BigQuery URI to your input data to run batch job.\n      Example: "gs://path/to/input/data" or "bq://projectId.bqDatasetId.bqTableId".\n      ')
    config: Optional[CreateBatchJobConfig] = Field(default=None, description='Optional parameters for creating a BatchJob.\n      ')

class BatchJobOutputInfo(_common.BaseModel):
    """Represents the `output_info` field in batch jobs."""
    vertex_multimodal_dataset_name: Optional[str] = Field(default=None, description='This field is experimental and may change in future versions. The Vertex AI dataset name containing the output data.')
    gcs_output_directory: Optional[str] = Field(default=None, description='The full path of the Cloud Storage directory created, into which the prediction output is written.')
    bigquery_output_table: Optional[str] = Field(default=None, description='The name of the BigQuery table created, in `predictions_TIMESTAMP` format, into which the prediction output is written.')

class CompletionStats(_common.BaseModel):
    """Success and error statistics of processing multiple entities (for example, DataItems or structured data rows) in batch.

  This data type is not supported in Gemini API.
  """
    failed_count: Optional[int] = Field(default=None, description='Output only. The number of entities for which any error was encountered.')
    incomplete_count: Optional[int] = Field(default=None, description='Output only. In cases when enough errors are encountered a job, pipeline, or operation may be failed as a whole. Below is the number of entities for which the processing had not been finished (either in successful or failed state). Set to -1 if the number is unknown (for example, the operation failed before the total entity number could be collected).')
    successful_count: Optional[int] = Field(default=None, description='Output only. The number of entities that had been processed successfully.')
    successful_forecast_point_count: Optional[int] = Field(default=None, description='Output only. The number of the successful forecast points that are generated by the forecasting model. This is ONLY used by the forecasting batch prediction.')

class BatchJob(_common.BaseModel):
    """Config for batches.create return value."""
    name: Optional[str] = Field(default=None, description='The resource name of the BatchJob. Output only.".\n      ')
    display_name: Optional[str] = Field(default=None, description='The display name of the BatchJob.\n      ')
    state: Optional[JobState] = Field(default=None, description='The state of the BatchJob.\n      ')
    error: Optional[JobError] = Field(default=None, description="Output only. Only populated when the job's state is JOB_STATE_FAILED or JOB_STATE_CANCELLED.")
    create_time: Optional[datetime.datetime] = Field(default=None, description='The time when the BatchJob was created.\n      ')
    start_time: Optional[datetime.datetime] = Field(default=None, description='Output only. Time when the Job for the first time entered the `JOB_STATE_RUNNING` state.')
    end_time: Optional[datetime.datetime] = Field(default=None, description='The time when the BatchJob was completed. This field is for Gemini Enterprise Agent Platform only.\n      ')
    update_time: Optional[datetime.datetime] = Field(default=None, description='The time when the BatchJob was last updated.\n      ')
    model: Optional[str] = Field(default=None, description='The name of the model that produces the predictions via the BatchJob.\n      ')
    src: Optional[BatchJobSource] = Field(default=None, description='Configuration for the input data. This field is for Gemini Enterprise Agent Platform only.\n      ')
    dest: Optional[BatchJobDestination] = Field(default=None, description='Configuration for the output data.\n      ')
    completion_stats: Optional[CompletionStats] = Field(default=None, description='Statistics on completed and failed prediction instances. This field is for Gemini Enterprise Agent Platform only.\n      ')
    output_info: Optional[BatchJobOutputInfo] = Field(default=None, description='Information further describing the output of this job. Output only.\n      ')

class GenerationConfigThinkingConfig(ThinkingConfig):
    """Config for thinking feature.

  This class will be deprecated. Please use `ThinkingConfig` instead.
  """

class EmbedContentBatch(_common.BaseModel):
    """Parameters for the embed_content method."""
    contents: Optional[ContentListUnion] = Field(default=None, description='The content to embed. Only the `parts.text` fields will be counted.\n      ')
    config: Optional[EmbedContentConfig] = Field(default=None, description='Configuration that contains optional parameters.\n      ')

class EmbeddingsBatchJobSource(_common.BaseModel):
    file_name: Optional[str] = Field(default=None, description='The Gemini Developer API\'s file resource name of the input data\n      (e.g. "files/12345").\n      ')
    inlined_requests: Optional[EmbedContentBatch] = Field(default=None, description="The Gemini Developer API's inlined input data to run batch job.\n      ")

class CreateEmbeddingsBatchJobConfig(_common.BaseModel):
    """Config for optional parameters."""
    http_options: Optional[HttpOptions] = Field(default=None, description='Used to override HTTP request options.')
    display_name: Optional[str] = Field(default=None, description='The user-defined name of this BatchJob.\n      ')

class _CreateEmbeddingsBatchJobParameters(_common.BaseModel):
    """Config for batches.create parameters."""
    model: Optional[str] = Field(default=None, description='The name of the model to produces the predictions via the BatchJob.\n      ')
    src: Optional[EmbeddingsBatchJobSource] = Field(default=None, description='input data to run batch job".\n      ')
    config: Optional[CreateEmbeddingsBatchJobConfig] = Field(default=None, description='Optional parameters for creating a BatchJob.\n      ')

class GetBatchJobConfig(_common.BaseModel):
    """Optional parameters."""
    http_options: Optional[HttpOptions] = Field(default=None, description='Used to override HTTP request options.')

class _GetBatchJobParameters(_common.BaseModel):
    """Config for batches.get parameters."""
    name: Optional[str] = Field(default=None, description='A fully-qualified BatchJob resource name or ID.\n    Example: "projects/.../locations/.../batchPredictionJobs/456"\n    or "456" when project and location are initialized in the client.\n    ')
    config: Optional[GetBatchJobConfig] = Field(default=None, description='Optional parameters for the request.')

class CancelBatchJobConfig(_common.BaseModel):
    """Optional parameters."""
    http_options: Optional[HttpOptions] = Field(default=None, description='Used to override HTTP request options.')

class _CancelBatchJobParameters(_common.BaseModel):
    """Config for batches.cancel parameters."""
    name: Optional[str] = Field(default=None, description='A fully-qualified BatchJob resource name or ID.\n    Example: "projects/.../locations/.../batchPredictionJobs/456"\n    or "456" when project and location are initialized in the client.\n    ')
    config: Optional[CancelBatchJobConfig] = Field(default=None, description='Optional parameters for the request.')

class ListBatchJobsConfig(_common.BaseModel):
    """Config for optional parameters."""
    http_options: Optional[HttpOptions] = Field(default=None, description='Used to override HTTP request options.')
    page_size: Optional[int] = Field(default=None, description='')
    page_token: Optional[str] = Field(default=None, description='')
    filter: Optional[str] = Field(default=None, description='')

class _ListBatchJobsParameters(_common.BaseModel):
    """Config for batches.list parameters."""
    config: Optional[ListBatchJobsConfig] = Field(default=None, description='')

class ListBatchJobsResponse(_common.BaseModel):
    """Config for batches.list return value."""
    sdk_http_response: Optional[HttpResponse] = Field(default=None, description='Used to retain the full HTTP response.')
    next_page_token: Optional[str] = Field(default=None, description='')
    batch_jobs: Optional[list[BatchJob]] = Field(default=None, description='')

class DeleteBatchJobConfig(_common.BaseModel):
    """Optional parameters for models.get method."""
    http_options: Optional[HttpOptions] = Field(default=None, description='Used to override HTTP request options.')

class _DeleteBatchJobParameters(_common.BaseModel):
    """Config for batches.delete parameters."""
    name: Optional[str] = Field(default=None, description='A fully-qualified BatchJob resource name or ID.\n    Example: "projects/.../locations/.../batchPredictionJobs/456"\n    or "456" when project and location are initialized in the client.\n    ')
    config: Optional[DeleteBatchJobConfig] = Field(default=None, description='Optional parameters for the request.')

class DeleteResourceJob(_common.BaseModel):
    """The return value of delete operation."""
    sdk_http_response: Optional[HttpResponse] = Field(default=None, description='Used to retain the full HTTP response.')
    name: Optional[str] = Field(default=None, description='')
    done: Optional[bool] = Field(default=None, description='')
    error: Optional[JobError] = Field(default=None, description='')

class GetOperationConfig(_common.BaseModel):
    http_options: Optional[HttpOptions] = Field(default=None, description='Used to override HTTP request options.')

class _GetOperationParameters(_common.BaseModel):
    """Parameters for the GET method."""
    operation_name: Optional[str] = Field(default=None, description='The server-assigned name for the operation.')
    config: Optional[GetOperationConfig] = Field(default=None, description='Used to override the default configuration.')

class FetchPredictOperationConfig(_common.BaseModel):
    http_options: Optional[HttpOptions] = Field(default=None, description='Used to override HTTP request options.')

class _FetchPredictOperationParameters(_common.BaseModel):
    """Parameters for the fetchPredictOperation method."""
    operation_name: Optional[str] = Field(default=None, description='The server-assigned name for the operation.')
    resource_name: Optional[str] = Field(default=None, description='')
    config: Optional[FetchPredictOperationConfig] = Field(default=None, description='Used to override the default configuration.')

class _GetProjectOperationParameters(_common.BaseModel):
    """Parameters for the getProjectOperation method."""
    operation_id: Optional[str] = Field(default=None, description='The ID of the project-level Gemini Enterprise Agent Platform operation to get. For example if the operation resource name is\n      projects/123/locations/us-central1/operations/456, the operation_id is\n      456.')
    config: Optional[GetOperationConfig] = Field(default=None, description='Used to override the default configuration.')

class ProjectOperation(_common.BaseModel):
    """A project-level operation in Gemini Enterprise Agent Platform."""
    name: Optional[str] = Field(default=None, description='The server-assigned name, which is only unique within the same service that originally returns it. If you use the default HTTP mapping, the `name` should be a resource name ending with `operations/{unique_id}`.')
    metadata: Optional[dict[str, Any]] = Field(default=None, description='Service-specific metadata associated with the operation. It typically contains progress information and common metadata such as create time. Some services might not provide such metadata.  Any method that returns a long-running operation should document the metadata type, if any.')
    done: Optional[bool] = Field(default=None, description='If the value is `false`, it means the operation is still in progress. If `true`, the operation is completed, and either `error` or `response` is available.')
    error: Optional[dict[str, Any]] = Field(default=None, description='The error result of the operation in case of failure or cancellation.')

class TestTableItem(_common.BaseModel):
    name: Optional[str] = Field(default=None, description='The name of the test. This is used to derive the replay id.')
    parameters: Optional[dict[str, Any]] = Field(default=None, description='The parameters to the test. Use pydantic models.')
    exception_if_mldev: Optional[str] = Field(default=None, description='Expects an exception for MLDev matching the string.')
    exception_if_vertex: Optional[str] = Field(default=None, description='Expects an exception for Vertex matching the string.')
    override_replay_id: Optional[str] = Field(default=None, description="Use if you don't want to use the default replay id which is derived from the test name.")
    has_union: Optional[bool] = Field(default=None, description='True if the parameters contain an unsupported union type. This test  will be skipped for languages that do not support the union type.')
    skip_in_api_mode: Optional[str] = Field(default=None, description='When set to a reason string, this test will be skipped in the API mode. Use this flag for tests that can not be reproduced with the real API. E.g. a test that deletes a resource.')
    ignore_keys: Optional[list[str]] = Field(default=None, description='Keys to ignore when comparing the request and response. This is useful for tests that are not deterministic.')

class TestTableFile(_common.BaseModel):
    comment: Optional[str] = Field(default=None, description='')
    test_method: Optional[str] = Field(default=None, description='')
    parameter_names: Optional[list[str]] = Field(default=None, description='')
    test_table: Optional[list[TestTableItem]] = Field(default=None, description='')

class ReplayRequest(_common.BaseModel):
    """Represents a single request in a replay."""
    method: Optional[str] = Field(default=None, description='')
    url: Optional[str] = Field(default=None, description='')
    headers: Optional[dict[str, str]] = Field(default=None, description='')
    body_segments: Optional[list[dict[str, Any]]] = Field(default=None, description='')

class ReplayResponse(_common.BaseModel):
    """Represents a single response in a replay."""
    status_code: Optional[int] = Field(default=None, description='')
    headers: Optional[dict[str, str]] = Field(default=None, description='')
    body_segments: Optional[list[dict[str, Any]]] = Field(default=None, description='')
    sdk_response_segments: Optional[list[dict[str, Any]]] = Field(default=None, description='')

class ReplayInteraction(_common.BaseModel):
    """Represents a single interaction, request and response in a replay."""
    request: Optional[ReplayRequest] = Field(default=None, description='')
    response: Optional[ReplayResponse] = Field(default=None, description='')

class ReplayFile(_common.BaseModel):
    """Represents a recorded session."""
    replay_id: Optional[str] = Field(default=None, description='')
    interactions: Optional[list[ReplayInteraction]] = Field(default=None, description='')

class UploadFileConfig(_common.BaseModel):
    """Used to override the default configuration."""
    http_options: Optional[HttpOptions] = Field(default=None, description='Used to override HTTP request options.')
    name: Optional[str] = Field(default=None, description="The name of the file in the destination (e.g., 'files/sample-image'. If not provided one will be generated.")
    mime_type: Optional[str] = Field(default=None, description='mime_type: The MIME type of the file. If not provided, it will be inferred from the file extension.')
    display_name: Optional[str] = Field(default=None, description='Optional display name of the file.')

class DownloadFileConfig(_common.BaseModel):
    """Used to override the default configuration."""
    http_options: Optional[HttpOptions] = Field(default=None, description='Used to override HTTP request options.')

class UpscaleImageConfig(_common.BaseModel):
    """Configuration for upscaling an image.

  For more information on this configuration, refer to
  the `Imagen API reference documentation
  <https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/imagen-api>`_.
  """
    http_options: Optional[HttpOptions] = Field(default=None, description='Used to override HTTP request options.')
    output_gcs_uri: Optional[str] = Field(default=None, description='Cloud Storage URI used to store the generated images.')
    safety_filter_level: Optional[SafetyFilterLevel] = Field(default=None, description='Filter level for safety filtering.')
    person_generation: Optional[PersonGeneration] = Field(default=None, description='Allows generation of people by the model.')
    include_rai_reason: Optional[bool] = Field(default=None, description='Whether to include a reason for filtered-out images in the\n      response.')
    output_mime_type: Optional[str] = Field(default=None, description='The image format that the output should be saved as.')
    output_compression_quality: Optional[int] = Field(default=None, description='The level of compression. Only applicable if the\n      ``output_mime_type`` is ``image/jpeg``.')
    enhance_input_image: Optional[bool] = Field(default=None, description='Whether to add an image enhancing step before upscaling.\n      It is expected to suppress the noise and JPEG compression artifacts\n      from the input image.')
    image_preservation_factor: Optional[float] = Field(default=None, description='With a higher image preservation factor, the original image\n      pixels are more respected. With a lower image preservation factor, the\n      output image will have be more different from the input image, but\n      with finer details and less noise.')
    labels: Optional[dict[str, str]] = Field(default=None, description='User specified labels to track billing usage.')

class UpscaleImageParameters(_common.BaseModel):
    """User-facing config UpscaleImageParameters."""
    model: Optional[str] = Field(default=None, description='The model to use.')
    image: Optional[Image] = Field(default=None, description='The input image to upscale.')
    upscale_factor: Optional[str] = Field(default=None, description='The factor to upscale the image (x2 or x4).')
    config: Optional[UpscaleImageConfig] = Field(default=None, description='Configuration for upscaling.')

class RawReferenceImage(_common.BaseModel):
    """A raw reference image.

  A raw reference image represents the base image to edit, provided by the user.
  It can optionally be provided in addition to a mask reference image or
  a style reference image.
  """
    reference_image: Optional[Image] = Field(default=None, description='The reference image for the editing operation.')
    reference_id: Optional[int] = Field(default=None, description='The id of the reference image.')
    reference_type: Optional[str] = Field(default=None, description='The type of the reference image. Only set by the SDK.')

    @pydantic.model_validator(mode='before')
    @classmethod
    def _validate_mask_image_config(self, values: Any) -> Any:
        if 'reference_type' in values:
            raise ValueError('Cannot set internal reference_type field directly.')
        values['reference_type'] = 'REFERENCE_TYPE_RAW'
        return values

class MaskReferenceImage(_common.BaseModel):
    """A mask reference image.

  This encapsulates either a mask image provided by the user and configs for
  the user provided mask, or only config parameters for the model to generate
  a mask.

  A mask image is an image whose non-zero values indicate where to edit the base
  image. If the user provides a mask image, the mask must be in the same
  dimensions as the raw image.
  """
    reference_image: Optional[Image] = Field(default=None, description='The reference image for the editing operation.')
    reference_id: Optional[int] = Field(default=None, description='The id of the reference image.')
    reference_type: Optional[str] = Field(default=None, description='The type of the reference image. Only set by the SDK.')
    config: Optional[MaskReferenceConfig] = Field(default=None, description='Configuration for the mask reference image.')
    mask_image_config: Optional['MaskReferenceConfig'] = Field(default=None, description='')

    @pydantic.model_validator(mode='before')
    @classmethod
    def _validate_mask_image_config(self, values: Any) -> Any:
        config = values.get('config', None)
        values['mask_image_config'] = config
        if 'reference_type' in values:
            raise ValueError('Cannot set internal reference_type field directly.')
        values['reference_type'] = 'REFERENCE_TYPE_MASK'
        return values

class ControlReferenceImage(_common.BaseModel):
    """A control reference image.

  The image of the control reference image is either a control image provided
  by the user, or a regular image which the backend will use to generate a
  control image of. In the case of the latter, the
  enable_control_image_computation field in the config should be set to True.

  A control image is an image that represents a sketch image of areas for the
  model to fill in based on the prompt.
  """
    reference_image: Optional[Image] = Field(default=None, description='The reference image for the editing operation.')
    reference_id: Optional[int] = Field(default=None, description='The id of the reference image.')
    reference_type: Optional[str] = Field(default=None, description='The type of the reference image. Only set by the SDK.')
    config: Optional[ControlReferenceConfig] = Field(default=None, description='Configuration for the control reference image.')
    control_image_config: Optional['ControlReferenceConfig'] = Field(default=None, description='')

    @pydantic.model_validator(mode='before')
    @classmethod
    def _validate_mask_image_config(self, values: Any) -> Any:
        config = values.get('config', None)
        values['control_image_config'] = config
        if 'reference_type' in values:
            raise ValueError('Cannot set internal reference_type field directly.')
        values['reference_type'] = 'REFERENCE_TYPE_CONTROL'
        return values

class StyleReferenceImage(_common.BaseModel):
    """A style reference image.

  This encapsulates a style reference image provided by the user, and
  additionally optional config parameters for the style reference image.

  A raw reference image can also be provided as a destination for the style to
  be applied to.
  """
    reference_image: Optional[Image] = Field(default=None, description='The reference image for the editing operation.')
    reference_id: Optional[int] = Field(default=None, description='The id of the reference image.')
    reference_type: Optional[str] = Field(default=None, description='The type of the reference image. Only set by the SDK.')
    config: Optional[StyleReferenceConfig] = Field(default=None, description='Configuration for the style reference image.')
    style_image_config: Optional['StyleReferenceConfig'] = Field(default=None, description='')

    @pydantic.model_validator(mode='before')
    @classmethod
    def _validate_mask_image_config(self, values: Any) -> Any:
        config = values.get('config', None)
        values['style_image_config'] = config
        if 'reference_type' in values:
            raise ValueError('Cannot set internal reference_type field directly.')
        values['reference_type'] = 'REFERENCE_TYPE_STYLE'
        return values

class SubjectReferenceImage(_common.BaseModel):
    """A subject reference image.

  This encapsulates a subject reference image provided by the user, and
  additionally optional config parameters for the subject reference image.

  A raw reference image can also be provided as a destination for the subject to
  be applied to.
  """
    reference_image: Optional[Image] = Field(default=None, description='The reference image for the editing operation.')
    reference_id: Optional[int] = Field(default=None, description='The id of the reference image.')
    reference_type: Optional[str] = Field(default=None, description='The type of the reference image. Only set by the SDK.')
    config: Optional[SubjectReferenceConfig] = Field(default=None, description='Configuration for the subject reference image.')
    subject_image_config: Optional['SubjectReferenceConfig'] = Field(default=None, description='')

    @pydantic.model_validator(mode='before')
    @classmethod
    def _validate_mask_image_config(self, values: Any) -> Any:
        config = values.get('config', None)
        values['subject_image_config'] = config
        if 'reference_type' in values:
            raise ValueError('Cannot set internal reference_type field directly.')
        values['reference_type'] = 'REFERENCE_TYPE_SUBJECT'
        return values

class ContentReferenceImage(_common.BaseModel):
    """A content reference image.

  A content reference image represents a subject to reference (ex. person,
  product, animal) provided by the user. It can optionally be provided in
  addition to a style reference image (ex. background, style reference).
  """
    reference_image: Optional[Image] = Field(default=None, description='The reference image for the editing operation.')
    reference_id: Optional[int] = Field(default=None, description='The id of the reference image.')
    reference_type: Optional[str] = Field(default=None, description='The type of the reference image. Only set by the SDK.')

    @pydantic.model_validator(mode='before')
    @classmethod
    def _validate_mask_image_config(self, values: Any) -> Any:
        if 'reference_type' in values:
            raise ValueError('Cannot set internal reference_type field directly.')
        values['reference_type'] = 'REFERENCE_TYPE_CONTENT'
        return values

class LiveServerSetupComplete(_common.BaseModel):
    """Sent in response to a `LiveGenerateContentSetup` message from the client."""
    session_id: Optional[str] = Field(default=None, description='The session id of the live session.')
    voice_consent_signature: Optional[VoiceConsentSignature] = Field(default=None, description='Signature of the verified consent audio. This is populated when the\n      request has a ReplicatedVoiceConfig with consent_audio set, if the consent\n      verification was successful. This may be used in a subsequent request\n      instead of the consent_audio to verify the same consent.')

class LiveServerContent(_common.BaseModel):
    """Incremental server update generated by the model in response to client messages.

  Content is generated as quickly as possible, and not in real time. Clients
  may choose to buffer and play it out in real time.
  """
    model_turn: Optional[Content] = Field(default=None, description='The content that the model has generated as part of the current conversation with the user.')
    turn_complete: Optional[bool] = Field(default=None, description='If true, indicates that the model is done generating. Generation will only start in response to additional client messages. Can be set alongside `content`, indicating that the `content` is the last in the turn.')
    interrupted: Optional[bool] = Field(default=None, description='If true, indicates that a client message has interrupted current model generation. If the client is playing out the content in realtime, this is a good signal to stop and empty the current queue.')
    grounding_metadata: Optional[GroundingMetadata] = Field(default=None, description='Metadata returned to client when grounding is enabled.')
    generation_complete: Optional[bool] = Field(default=None, description='If true, indicates that the model is done generating. When model is\n      interrupted while generating there will be no generation_complete message\n      in interrupted turn, it will go through interrupted > turn_complete.\n      When model assumes realtime playback there will be delay between\n      generation_complete and turn_complete that is caused by model\n      waiting for playback to finish. If true, indicates that the model\n      has finished generating all content. This is a signal to the client\n      that it can stop sending messages.')
    input_transcription: Optional[Transcription] = Field(default=None, description='Input transcription. The transcription is independent to the model\n      turn which means it doesn’t imply any ordering between transcription and\n      model turn.')
    output_transcription: Optional[Transcription] = Field(default=None, description='Output transcription. The transcription is independent to the model\n      turn which means it doesn’t imply any ordering between transcription and\n      model turn.\n      ')
    url_context_metadata: Optional[UrlContextMetadata] = Field(default=None, description='Metadata related to url context retrieval tool.')
    turn_complete_reason: Optional[TurnCompleteReason] = Field(default=None, description='Reason for the turn is complete.')
    waiting_for_input: Optional[bool] = Field(default=None, description='If true, indicates that the model is not generating content because\n      it is waiting for more input from the user, e.g. because it expects the\n      user to continue talking.')
    interim_input_transcription: Optional[Transcription] = Field(default=None, description='Low latency transcription updated while the user is speaking.')
    interaction_status: Optional[InteractionStatus] = Field(default=None, description='The current activity status of the live session. Always sent alongside `turn_complete`.')

class LiveServerToolCall(_common.BaseModel):
    """Request for the client to execute the `function_calls` and return the responses with the matching `id`s."""
    function_calls: Optional[list[FunctionCall]] = Field(default=None, description='The function call to be executed.')

class LiveServerToolCallCancellation(_common.BaseModel):
    """Notification for the client that a previously issued `ToolCallMessage` with the specified `id`s should have been not executed and should be cancelled.

  If there were side-effects to those tool calls, clients may attempt to undo
  the tool calls. This message occurs only in cases where the clients interrupt
  server turns.
  """
    ids: Optional[list[str]] = Field(default=None, description='The ids of the tool calls to be cancelled.')

class UsageMetadata(_common.BaseModel):
    """Usage metadata about response(s)."""
    prompt_token_count: Optional[int] = Field(default=None, description='The total number of tokens in the prompt. This includes any text, images, or other media provided in the request. When `cached_content` is set, this also includes the number of tokens in the cached content.')
    cached_content_token_count: Optional[int] = Field(default=None, description='Output only. The number of tokens in the cached content that was used for this request.')
    response_token_count: Optional[int] = Field(default=None, description='Total number of tokens across all the generated response candidates.')
    tool_use_prompt_token_count: Optional[int] = Field(default=None, description='Output only. The number of tokens in the results from tool executions, which are provided back to the model as input, if applicable.')
    thoughts_token_count: Optional[int] = Field(default=None, description='Output only. The number of tokens that were part of the model\'s generated "thoughts" output, if applicable.')
    total_token_count: Optional[int] = Field(default=None, description='The total number of tokens for the entire request. This is the sum of `prompt_token_count`, `candidates_token_count`, `tool_use_prompt_token_count`, and `thoughts_token_count`.')
    prompt_tokens_details: Optional[list[ModalityTokenCount]] = Field(default=None, description='Output only. A detailed breakdown of the token count for each modality in the prompt.')
    cache_tokens_details: Optional[list[ModalityTokenCount]] = Field(default=None, description='Output only. A detailed breakdown of the token count for each modality in the cached content.')
    response_tokens_details: Optional[list[ModalityTokenCount]] = Field(default=None, description='List of modalities that were returned in the response.')
    tool_use_prompt_tokens_details: Optional[list[ModalityTokenCount]] = Field(default=None, description='Output only. A detailed breakdown by modality of the token counts from the results of tool executions, which are provided back to the model as input.')
    traffic_type: Optional[TrafficType] = Field(default=None, description='Output only. The traffic type for this request. This field is not supported in Gemini API.')
    service_tier: Optional[ServiceTier] = Field(default=None, description='Output only. Service tier of the request. This field is not supported in Vertex AI.')

class LiveServerGoAway(_common.BaseModel):
    """Server will not be able to service client soon."""
    time_left: Optional[str] = Field(default=None, description='The remaining time before the connection will be terminated as ABORTED. The minimal time returned here is specified differently together with the rate limits for a given model.')

class LiveServerSessionResumptionUpdate(_common.BaseModel):
    """Update of the session resumption state.

  Only sent if `session_resumption` was set in the connection config.
  """
    new_handle: Optional[str] = Field(default=None, description='New handle that represents state that can be resumed. Empty if `resumable`=false.')
    resumable: Optional[bool] = Field(default=None, description='True if session can be resumed at this point. It might be not possible to resume session at some points. In that case we send update empty new_handle and resumable=false. Example of such case could be model executing function calls or just generating. Resuming session (using previous session token) in such state will result in some data loss.')
    last_consumed_client_message_index: Optional[int] = Field(default=None, description='Index of last message sent by client that is included in state represented by this SessionResumptionToken. Only sent when `SessionResumptionConfig.transparent` is set.\n\nPresence of this index allows users to transparently reconnect and avoid issue of losing some part of realtime audio input/video. If client wishes to temporarily disconnect (for example as result of receiving GoAway) they can do it without losing state by buffering messages sent since last `SessionResumptionTokenUpdate`. This field will enable them to limit buffering (avoid keeping all requests in RAM).\n\nNote: This should not be used for when resuming a session at some time later -- in those cases partial audio and video frames are likely not needed.')

class VoiceActivityDetectionSignal(_common.BaseModel):
    vad_signal_type: Optional[VadSignalType] = Field(default=None, description='The type of the VAD signal.')

class VoiceActivity(_common.BaseModel):
    """Voice activity signal."""
    voice_activity_type: Optional[VoiceActivityType] = Field(default=None, description='The type of the voice activity signal.')
    audio_offset: Optional[str] = Field(default=None, description='The time voice activity detected in audio time, relative to the start of the audio stream.')

class LiveServerMessage(_common.BaseModel):
    """Response message for API call."""
    setup_complete: Optional[LiveServerSetupComplete] = Field(default=None, description='Sent in response to a `LiveClientSetup` message from the client.')
    server_content: Optional[LiveServerContent] = Field(default=None, description='Content generated by the model in response to client messages.')
    tool_call: Optional[LiveServerToolCall] = Field(default=None, description='Request for the client to execute the `function_calls` and return the responses with the matching `id`s.')
    tool_call_cancellation: Optional[LiveServerToolCallCancellation] = Field(default=None, description='Notification for the client that a previously issued `ToolCallMessage` with the specified `id`s should have been not executed and should be cancelled.')
    usage_metadata: Optional[UsageMetadata] = Field(default=None, description='Usage metadata about model response(s).')
    go_away: Optional[LiveServerGoAway] = Field(default=None, description='Server will disconnect soon.')
    session_resumption_update: Optional[LiveServerSessionResumptionUpdate] = Field(default=None, description='Update of the session resumption state.')
    voice_activity_detection_signal: Optional[VoiceActivityDetectionSignal] = Field(default=None, description='Voice activity detection signal. Allowlisted only.')
    voice_activity: Optional[VoiceActivity] = Field(default=None, description='Voice activity signal.')

class SessionResumptionConfig(_common.BaseModel):
    """Configuration of session resumption mechanism.

  Included in `LiveConnectConfig.session_resumption`. If included server
  will send `LiveServerSessionResumptionUpdate` messages.
  """
    handle: Optional[str] = Field(default=None, description='Session resumption handle of previous session (session to restore).\n\nIf not present new session will be started.')
    transparent: Optional[bool] = Field(default=None, description='If set the server will send `last_consumed_client_message_index` in the `session_resumption_update` messages to allow for transparent reconnections.')

class SlidingWindow(_common.BaseModel):
    """Context window will be truncated by keeping only suffix of it.

  Context window will always be cut at start of USER role turn. System
  instructions and `BidiGenerateContentSetup.prefix_turns` will not be
  subject to the sliding window mechanism, they will always stay at the
  beginning of context window.
  """
    target_tokens: Optional[int] = Field(default=None, description='Session reduction target -- how many tokens we should keep. Window shortening operation has some latency costs, so we should avoid running it on every turn. Should be < trigger_tokens. If not set, trigger_tokens/2 is assumed.')

class ContextWindowCompressionConfig(_common.BaseModel):
    """Enables context window compression -- mechanism managing model context window so it does not exceed given length."""
    trigger_tokens: Optional[int] = Field(default=None, description='Number of tokens (before running turn) that triggers context window compression mechanism.')
    sliding_window: Optional[SlidingWindow] = Field(default=None, description='Sliding window compression mechanism.')

class ProactivityConfig(_common.BaseModel):
    """Config for proactivity features."""
    proactive_audio: Optional[bool] = Field(default=None, description='If enabled, the model can reject responding to the last prompt. For\n        example, this allows the model to ignore out of context speech or to stay\n        silent if the user did not make a request, yet.')

class HistoryConfig(_common.BaseModel):
    """Configuration for history exchange between client and server."""
    initial_history_in_client_content: Optional[bool] = Field(default=None, description='If true, after sending `setup_complete`, the server will wait\n      and at first process `client_content` messages until `turn_complete` is\n      `true`. This initial history will not trigger a model call and\n      may end with model content. After `turn_complete` is `true`, the client\n      can start the realtime conversation via `realtime_input`.')

class CustomizedAvatar(_common.BaseModel):
    """Configures the customized avatar to be used in the session."""
    image_mime_type: Optional[str] = Field(default=None, description='The mime type of the reference image, e.g., "image/jpeg".')
    image_data: Optional[bytes] = Field(default=None, description='The data of the reference image. The dimensions of the reference\n      image should be 9:16 (portrait) with a minimum resolution of 704x1280.')

class AvatarConfig(_common.BaseModel):
    """Configures the avatar to be used in the session."""
    avatar_name: Optional[str] = Field(default=None, description='Pre-built avatar id.')
    customized_avatar: Optional[CustomizedAvatar] = Field(default=None, description='Customized avatar appearance with a reference image.')
    audio_bitrate_bps: Optional[int] = Field(default=None, description='The bitrate of compressed audio.')
    video_bitrate_bps: Optional[int] = Field(default=None, description='The bitrate of compressed video output.')

class LiveClientSetup(_common.BaseModel):
    """Message contains configuration that will apply for the duration of the streaming session."""
    model: Optional[str] = Field(default=None, description='\n      The fully qualified name of the publisher model or tuned model endpoint to\n      use.\n      ')
    generation_config: Optional[GenerationConfig] = Field(default=None, description='The generation configuration for the session.\n      Note: only a subset of fields are supported.\n      ')
    system_instruction: Optional[ContentUnion] = Field(default=None, description='The user provided system instructions for the model.\n      Note: only text should be used in parts and content in each part will be\n      in a separate paragraph.')
    tools: Optional[ToolListUnion] = Field(default=None, description=' A list of `Tools` the model may use to generate the next response.\n\n      A `Tool` is a piece of code that enables the system to interact with\n      external systems to perform an action, or set of actions, outside of\n      knowledge and scope of the model.')
    session_resumption: Optional[SessionResumptionConfig] = Field(default=None, description='Configures session resumption mechanism.\n\n          If included server will send SessionResumptionUpdate messages.')
    context_window_compression: Optional[ContextWindowCompressionConfig] = Field(default=None, description='Configures context window compression mechanism.\n\n      If included, server will compress context window to fit into given length.')
    input_audio_transcription: Optional[AudioTranscriptionConfig] = Field(default=None, description='The transcription of the input aligns with the input audio language.\n      ')
    output_audio_transcription: Optional[AudioTranscriptionConfig] = Field(default=None, description='The transcription of the output aligns with the language code\n      specified for the output audio.\n      ')
    proactivity: Optional[ProactivityConfig] = Field(default=None, description='Configures the proactivity of the model. This allows the model to respond proactively to\n    the input and to ignore irrelevant input.')
    explicit_vad_signal: Optional[bool] = Field(default=None, description='Configures the explicit VAD signal. If enabled, the client will send\n      vad_signal to indicate the start and end of speech. This allows the server\n      to process the audio more efficiently.')
    history_config: Optional[HistoryConfig] = Field(default=None, description='Configures the exchange of history between the client and the server.')
    avatar_config: Optional[AvatarConfig] = Field(default=None, description='Configures the avatar model behavior.')
    safety_settings: Optional[list[SafetySetting]] = Field(default=None, description='Safety settings in the request to block unsafe content in the\n      response.\n      ')
    labels: Optional[dict[str, str]] = Field(default=None, description='Optional. Labels with user-defined metadata for the request. Optional. Labels must follow standard unified Cloud label requirements: - Label keys must start with a letter. - Label keys and values can be no longer than 63 characters (Unicode codepoints) and can only contain lowercase letters, numeric characters, underscores, and dashes. - International characters are allowed. Usage: - Safety identifiers from aggregators: Use the key `safety_identifier` (e.g. `{"safety_identifier": "user_session_123"}`)')

class LiveClientContent(_common.BaseModel):
    """Incremental update of the current conversation delivered from the client.

  All the content here will unconditionally be appended to the conversation
  history and used as part of the prompt to the model to generate content.

  A message here will interrupt any current model generation.
  """
    turns: Optional[list[Content]] = Field(default=None, description='The content appended to the current conversation with the model.\n\n      For single-turn queries, this is a single instance. For multi-turn\n      queries, this is a repeated field that contains conversation history and\n      latest request.\n      ')
    turn_complete: Optional[bool] = Field(default=None, description='If true, indicates that the server content generation should start with\n  the currently accumulated prompt. Otherwise, the server will await\n  additional messages before starting generation.')

class ActivityStart(_common.BaseModel):
    """Marks the start of user activity.

  This can only be sent if automatic (i.e. server-side) activity detection is
  disabled.
  """
    pass

class ActivityEnd(_common.BaseModel):
    """Marks the end of user activity.

  This can only be sent if automatic (i.e. server-side) activity detection is
  disabled.
  """
    pass

class LiveClientRealtimeInput(_common.BaseModel):
    """User input that is sent in real time.

  This is different from `LiveClientContent` in a few ways:

    - Can be sent continuously without interruption to model generation.
    - If there is a need to mix data interleaved across the
      `LiveClientContent` and the `LiveClientRealtimeInput`, server attempts to
      optimize for best response, but there are no guarantees.
    - End of turn is not explicitly specified, but is rather derived from user
      activity (for example, end of speech).
    - Even before the end of turn, the data is processed incrementally
      to optimize for a fast start of the response from the model.
    - Is always assumed to be the user's input (cannot be used to populate
      conversation history).
  """
    media_chunks: Optional[list[Blob]] = Field(default=None, description='Inlined bytes data for media input.')
    audio: Optional[Blob] = Field(default=None, description='The realtime audio input stream.')
    audio_stream_end: Optional[bool] = Field(default=None, description='\nIndicates that the audio stream has ended, e.g. because the microphone was\nturned off.\n\nThis should only be sent when automatic activity detection is enabled\n(which is the default).\n\nThe client can reopen the stream by sending an audio message.\n')
    video: Optional[Blob] = Field(default=None, description='The realtime video input stream.')
    text: Optional[str] = Field(default=None, description='The realtime text input stream.')
    activity_start: Optional[ActivityStart] = Field(default=None, description='Marks the start of user activity.')
    activity_end: Optional[ActivityEnd] = Field(default=None, description='Marks the end of user activity.')

class LiveClientToolResponse(_common.BaseModel):
    """Client generated response to a `ToolCall` received from the server.

  Individual `FunctionResponse` objects are matched to the respective
  `FunctionCall` objects by the `id` field.

  Note that in the unary and server-streaming GenerateContent APIs function
  calling happens by exchanging the `Content` parts, while in the bidi
  GenerateContent APIs function calling happens over this dedicated set of
  messages.
  """
    function_responses: Optional[list[FunctionResponse]] = Field(default=None, description='The response to the function calls.')

class LiveClientContextUpdateTools(_common.BaseModel):
    """A wrapper around the list of tools.

  This wrapper exists because a bare `repeated Tool` field cannot tell apart
  "not sending a tools update" from "clearing all tools": an unset repeated
  field and an empty repeated field look identical on the wire. Wrapping the
  list in a message adds a presence bit, so the two cases become: - `tools`
  field unset: no update; keep the previously provided tools. - `tools` field
  set (even with an empty list): replace the current tools with the provided
  list, which may be empty to clear all tools.
  """
    tools: Optional[ToolListUnion] = Field(default=None, description='The list of tools the model may use to generate the next response.')

class LiveClientContextUpdate(_common.BaseModel):
    """Updates to the context of the current session.

  Only fields that are set will be updated. Updates are guaranteed to be
  processed *in order* with the rest of the inputs.
  """
    system_instruction: Optional[ContentUnion] = Field(default=None, description='Updated system instruction for the model. If set, overrides `BidiGenerateContentSetup.system_instruction`. The system instructions are part of the model preamble, so updating them invalidates the prefix cache. Clients should only update this field when strictly necessary as it might have a performance impact on the model generation.')
    tools: Optional[LiveClientContextUpdateTools] = Field(default=None, description='An updated list of tools the model may use to generate the subsequent responses. If set, this list replaces the previously provided tools. The tools are part of the model preamble, so updating them invalidates the prefix cache. Clients should only update this field when strictly necessary as it might have a performance impact on the model generation.')

class LiveClientMessage(_common.BaseModel):
    """Messages sent by the client in the API call."""
    setup: Optional[LiveClientSetup] = Field(default=None, description='Message to be sent by the system when connecting to the API. SDK users should not send this message.')
    client_content: Optional[LiveClientContent] = Field(default=None, description='Incremental update of the current conversation delivered from the client.')
    realtime_input: Optional[LiveClientRealtimeInput] = Field(default=None, description='User input that is sent in real time.')
    tool_response: Optional[LiveClientToolResponse] = Field(default=None, description='Response to a `ToolCallMessage` received from the server.')
    context_update: Optional[LiveClientContextUpdate] = Field(default=None, description='Updates to the context of the current session.')

class AutomaticActivityDetection(_common.BaseModel):
    """Configures automatic detection of activity."""
    disabled: Optional[bool] = Field(default=None, description='If enabled, detected voice and text input count as activity. If disabled, the client must send activity signals.')
    start_of_speech_sensitivity: Optional[StartSensitivity] = Field(default=None, description='Determines how likely speech is to be detected.')
    end_of_speech_sensitivity: Optional[EndSensitivity] = Field(default=None, description='Determines how likely detected speech is ended.')
    prefix_padding_ms: Optional[int] = Field(default=None, description='The required duration of detected speech before start-of-speech is committed. The lower this value the more sensitive the start-of-speech detection is and the shorter speech can be recognized. However, this also increases the probability of false positives.')
    silence_duration_ms: Optional[int] = Field(default=None, description="The required duration of detected non-speech (e.g. silence) before end-of-speech is committed. The larger this value, the longer speech gaps can be without interrupting the user's activity but this will increase the model's latency.")

class RealtimeInputConfig(_common.BaseModel):
    """Marks the end of user activity.

  This can only be sent if automatic (i.e. server-side) activity detection is
  disabled.
  """
    automatic_activity_detection: Optional[AutomaticActivityDetection] = Field(default=None, description='If not set, automatic activity detection is enabled by default. If automatic voice detection is disabled, the client must send activity signals.')
    activity_handling: Optional[ActivityHandling] = Field(default=None, description='Defines what effect activity has.')
    turn_coverage: Optional[TurnCoverage] = Field(default=None, description="Defines which input is included in the user's turn.")
    interim_transcript_timestamp_enabled: Optional[bool] = Field(default=None, description='If true, enables interim transcript timestamps.')

class LiveConnectConfig(_common.BaseModel):
    """Session config for the API connection."""
    http_options: Optional[HttpOptions] = Field(default=None, description='Used to override HTTP request options.')
    generation_config: Optional[GenerationConfig] = Field(default=None, description='The generation configuration for the session.')
    response_modalities: Optional[list[Modality]] = Field(default=None, description='The requested modalities of the response. Represents the set of\n      modalities that the model can return. Defaults to AUDIO if not specified.\n      ')
    temperature: Optional[float] = Field(default=None, description='Value that controls the degree of randomness in token selection.\n      Lower temperatures are good for prompts that require a less open-ended or\n      creative response, while higher temperatures can lead to more diverse or\n      creative results.\n      ')
    top_p: Optional[float] = Field(default=None, description='Tokens are selected from the most to least probable until the sum\n      of their probabilities equals this value. Use a lower value for less\n      random responses and a higher value for more random responses.\n      ')
    top_k: Optional[float] = Field(default=None, description='For each token selection step, the ``top_k`` tokens with the\n      highest probabilities are sampled. Then tokens are further filtered based\n      on ``top_p`` with the final token selected using temperature sampling. Use\n      a lower number for less random responses and a higher number for more\n      random responses.\n      ')
    max_output_tokens: Optional[int] = Field(default=None, description='Maximum number of tokens that can be generated in the response.\n      ')
    media_resolution: Optional[MediaResolution] = Field(default=None, description='If specified, the media resolution specified will be used.\n      ')
    seed: Optional[int] = Field(default=None, description='When ``seed`` is fixed to a specific number, the model makes a best\n      effort to provide the same response for repeated requests. By default, a\n      random number is used.\n      ')
    speech_config: Optional[SpeechConfig] = Field(default=None, description='The speech generation configuration.\n      ')
    thinking_config: Optional[ThinkingConfig] = Field(default=None, description="Config for thinking features.\n      An error will be returned if this field is set for models that don't\n      support thinking.\n      ")
    enable_affective_dialog: Optional[bool] = Field(default=None, description='If enabled, the model will detect emotions and adapt its responses accordingly.')
    system_instruction: Optional[ContentUnion] = Field(default=None, description='The user provided system instructions for the model.\n      Note: only text should be used in parts and content in each part will be\n      in a separate paragraph.')
    tools: Optional[ToolListUnion] = Field(default=None, description='A list of `Tools` the model may use to generate the next response.\n\n      A `Tool` is a piece of code that enables the system to interact with\n      external systems to perform an action, or set of actions, outside of\n      knowledge and scope of the model.')
    session_resumption: Optional[SessionResumptionConfig] = Field(default=None, description='Configures session resumption mechanism.\n\nIf included the server will send SessionResumptionUpdate messages.')
    input_audio_transcription: Optional[AudioTranscriptionConfig] = Field(default=None, description='The transcription of the input aligns with the input audio language.\n      ')
    output_audio_transcription: Optional[AudioTranscriptionConfig] = Field(default=None, description='The transcription of the output aligns with the language code\n      specified for the output audio.\n      ')
    realtime_input_config: Optional[RealtimeInputConfig] = Field(default=None, description='Configures the realtime input behavior in BidiGenerateContent.')
    context_window_compression: Optional[ContextWindowCompressionConfig] = Field(default=None, description='Configures context window compression mechanism.\n\n      If included, server will compress context window to fit into given length.')
    proactivity: Optional[ProactivityConfig] = Field(default=None, description='Configures the proactivity of the model. This allows the model to respond proactively to\n    the input and to ignore irrelevant input.')
    explicit_vad_signal: Optional[bool] = Field(default=None, description='Configures the explicit VAD signal. If enabled, the client will send\n      vad_signal to indicate the start and end of speech. This allows the server\n      to process the audio more efficiently.')
    history_config: Optional[HistoryConfig] = Field(default=None, description='Configures the exchange of history between the client and the server.')
    avatar_config: Optional[AvatarConfig] = Field(default=None, description='Configures the avatar model behavior.')
    safety_settings: Optional[list[SafetySetting]] = Field(default=None, description='Safety settings in the request to block unsafe content in the\n      response.\n      ')
    translation_config: Optional[TranslationConfig] = Field(default=None, description='Config for translation.')
    labels: Optional[dict[str, str]] = Field(default=None, description='Labels with user-defined metadata for the session. In Gemini\n      Enterprise Agent Platform, they are used for billing and reporting.')

class LiveConnectParameters(_common.BaseModel):
    """Parameters for connecting to the live API."""
    model: Optional[str] = Field(default=None, description='ID of the model to use. For a list of models, see `Google models\n    <https://cloud.google.com/vertex-ai/generative-ai/docs/learn/models>`_.')
    config: Optional[LiveConnectConfig] = Field(default=None, description='Optional configuration parameters for the request.\n      ')
if _is_pillow_image_imported:
    BlobImageUnion = Union[PIL_Image, Blob]
else:
    BlobImageUnion = Blob

class LiveSendRealtimeInputParameters(_common.BaseModel):
    """Parameters for sending realtime input to the live API."""
    media: Optional[BlobImageUnion] = Field(default=None, description='Realtime input to send to the session.')
    audio: Optional[Blob] = Field(default=None, description='The realtime audio input stream.')
    audio_stream_end: Optional[bool] = Field(default=None, description='\nIndicates that the audio stream has ended, e.g. because the microphone was\nturned off.\n\nThis should only be sent when automatic activity detection is enabled\n(which is the default).\n\nThe client can reopen the stream by sending an audio message.\n')
    video: Optional[BlobImageUnion] = Field(default=None, description='The realtime video input stream.')
    text: Optional[str] = Field(default=None, description='The realtime text input stream.')
    activity_start: Optional[ActivityStart] = Field(default=None, description='Marks the start of user activity.')
    activity_end: Optional[ActivityEnd] = Field(default=None, description='Marks the end of user activity.')

class LiveMusicClientSetup(_common.BaseModel):
    """Message to be sent by the system when connecting to the API."""
    model: Optional[str] = Field(default=None, description="The model's resource name. Format: `models/{model}`.")

class WeightedPrompt(_common.BaseModel):
    """Maps a prompt to a relative weight to steer music generation."""
    text: Optional[str] = Field(default=None, description='Text prompt.')
    weight: Optional[float] = Field(default=None, description='Weight of the prompt. The weight is used to control the relative\n      importance of the prompt. Higher weights are more important than lower\n      weights.\n\n      Weight must not be 0. Weights of all weighted_prompts in this\n      LiveMusicClientContent message will be normalized.')

class LiveMusicClientContent(_common.BaseModel):
    """User input to start or steer the music."""
    weighted_prompts: Optional[list[WeightedPrompt]] = Field(default=None, description='Weighted prompts as the model input.')

class LiveMusicGenerationConfig(_common.BaseModel):
    """Configuration for music generation."""
    temperature: Optional[float] = Field(default=None, description='Controls the variance in audio generation. Higher values produce\n      higher variance. Range is [0.0, 3.0].')
    top_k: Optional[int] = Field(default=None, description='Controls how the model selects tokens for output. Samples the topK\n      tokens with the highest probabilities. Range is [1, 1000].')
    seed: Optional[int] = Field(default=None, description='Seeds audio generation. If not set, the request uses a randomly\n      generated seed.')
    guidance: Optional[float] = Field(default=None, description='Controls how closely the model follows prompts.\n      Higher guidance follows more closely, but will make transitions more\n      abrupt. Range is [0.0, 6.0].')
    bpm: Optional[int] = Field(default=None, description='Beats per minute. Range is [60, 200].')
    density: Optional[float] = Field(default=None, description='Density of sounds. Range is [0.0, 1.0].')
    brightness: Optional[float] = Field(default=None, description='Brightness of the music. Range is [0.0, 1.0].')
    scale: Optional[Scale] = Field(default=None, description='Scale of the generated music.')
    mute_bass: Optional[bool] = Field(default=None, description='Whether the audio output should contain bass.')
    mute_drums: Optional[bool] = Field(default=None, description='Whether the audio output should contain drums.')
    only_bass_and_drums: Optional[bool] = Field(default=None, description='Whether the audio output should contain only bass and drums.')
    music_generation_mode: Optional[MusicGenerationMode] = Field(default=None, description='The mode of music generation. Default mode is QUALITY.')

class LiveMusicClientMessage(_common.BaseModel):
    """Messages sent by the client in the LiveMusicClientMessage call."""
    setup: Optional[LiveMusicClientSetup] = Field(default=None, description='Message to be sent in the first (and only in the first) `LiveMusicClientMessage`.\n      Clients should wait for a `LiveMusicSetupComplete` message before\n      sending any additional messages.')
    client_content: Optional[LiveMusicClientContent] = Field(default=None, description='User input to influence music generation.')
    music_generation_config: Optional[LiveMusicGenerationConfig] = Field(default=None, description='Configuration for music generation.')
    playback_control: Optional[LiveMusicPlaybackControl] = Field(default=None, description='Playback control signal for the music generation.')

class LiveMusicServerSetupComplete(_common.BaseModel):
    """Sent in response to a `LiveMusicClientSetup` message from the client."""
    pass

class LiveMusicSourceMetadata(_common.BaseModel):
    """Prompts and config used for generating this audio chunk."""
    client_content: Optional[LiveMusicClientContent] = Field(default=None, description='Weighted prompts for generating this audio chunk.')
    music_generation_config: Optional[LiveMusicGenerationConfig] = Field(default=None, description='Music generation config for generating this audio chunk.')

class AudioChunk(_common.BaseModel):
    """Representation of an audio chunk."""
    data: Optional[bytes] = Field(default=None, description='Raw bytes of audio data.')
    mime_type: Optional[str] = Field(default=None, description='MIME type of the audio chunk.')
    source_metadata: Optional[LiveMusicSourceMetadata] = Field(default=None, description='Prompts and config used for generating this audio chunk.')

class LiveMusicServerContent(_common.BaseModel):
    """Server update generated by the model in response to client messages.

  Content is generated as quickly as possible, and not in real time.
  Clients may choose to buffer and play it out in real time.
  """
    audio_chunks: Optional[list[AudioChunk]] = Field(default=None, description='The audio chunks that the model has generated.')

class LiveMusicFilteredPrompt(_common.BaseModel):
    """A prompt that was filtered with the reason."""
    text: Optional[str] = Field(default=None, description='The text prompt that was filtered.')
    filtered_reason: Optional[str] = Field(default=None, description='The reason the prompt was filtered.')

class LiveMusicServerMessage(_common.BaseModel):
    """Response message for the LiveMusicClientMessage call."""
    setup_complete: Optional[LiveMusicServerSetupComplete] = Field(default=None, description='Message sent in response to a `LiveMusicClientSetup` message from the client.\n      Clients should wait for this message before sending any additional messages.')
    server_content: Optional[LiveMusicServerContent] = Field(default=None, description='Content generated by the model in response to client messages.')
    filtered_prompt: Optional[LiveMusicFilteredPrompt] = Field(default=None, description='A prompt that was filtered with the reason.')

class LiveMusicConnectParameters(_common.BaseModel):
    """Parameters for connecting to the live API."""
    model: Optional[str] = Field(default=None, description="The model's resource name.")

class LiveMusicSetConfigParameters(_common.BaseModel):
    """Parameters for setting config for the live music API."""
    music_generation_config: Optional[LiveMusicGenerationConfig] = Field(default=None, description='Configuration for music generation.')

class LiveMusicSetWeightedPromptsParameters(_common.BaseModel):
    """Parameters for setting weighted prompts for the live music API."""
    weighted_prompts: Optional[list[WeightedPrompt]] = Field(default=None, description='A map of text prompts to weights to use for the generation request.')

class AuthToken(_common.BaseModel):
    """Config for auth_tokens.create parameters."""
    name: Optional[str] = Field(default=None, description='The name of the auth token.')
    expire_time: Optional[str] = Field(default=None, description='Optional. Input only. Immutable. An optional time after which, when using the resulting token, messages in BidiGenerateContent sessions will be rejected. (Gemini may preemptively close the session after this time.) If not set then this defaults to 30 minutes in the future. If set, this value must be less than 20 hours in the future.')
    new_session_expire_time: Optional[str] = Field(default=None, description='Optional. Input only. Immutable. The time after which new Live API sessions using the token resulting from this request will be rejected. If not set this defaults to 60 seconds in the future. If set, this value must be less than 20 hours in the future.')
    uses: Optional[int] = Field(default=None, description='Optional. Input only. Immutable. The number of times the token can be used. If this value is zero then no limit is applied. Resuming a Live API session does not count as a use. If unspecified, the default is 1.')

class LiveConnectConstraints(_common.BaseModel):
    """Config for LiveConnectConstraints for Auth Token creation."""
    model: Optional[str] = Field(default=None, description='ID of the model to configure in the ephemeral token for Live API.\n      For a list of models, see `Gemini models\n      <https://ai.google.dev/gemini-api/docs/models>`.')
    config: Optional[LiveConnectConfig] = Field(default=None, description='Configuration specific to Live API connections created using this token.')

class CreateAuthTokenConfig(_common.BaseModel):
    """Optional parameters."""
    http_options: Optional[HttpOptions] = Field(default=None, description='Used to override HTTP request options.')
    expire_time: Optional[datetime.datetime] = Field(default=None, description='An optional time after which, when using the resulting token,\n      messages in Live API sessions will be rejected. (Gemini may\n      preemptively close the session after this time.)\n\n      If not set then this defaults to 30 minutes in the future. If set, this\n      value must be less than 20 hours in the future.')
    new_session_expire_time: Optional[datetime.datetime] = Field(default=None, description='The time after which new Live API sessions using the token\n      resulting from this request will be rejected.\n\n      If not set this defaults to 60 seconds in the future. If set, this value\n      must be less than 20 hours in the future.')
    uses: Optional[int] = Field(default=None, description='The number of times the token can be used. If this value is zero\n      then no limit is applied. Default is 1. Resuming a Live API session does\n      not count as a use.')
    live_connect_constraints: Optional[LiveConnectConstraints] = Field(default=None, description='Configuration specific to Live API connections created using this token.')
    lock_additional_fields: Optional[list[str]] = Field(default=None, description='Additional fields to lock in the effective LiveConnectParameters.')

class CreateAuthTokenParameters(_common.BaseModel):
    """Config for auth_tokens.create parameters."""
    config: Optional[CreateAuthTokenConfig] = Field(default=None, description='Optional parameters for the request.')

class CountTokensResult(_common.BaseModel):
    """Local tokenizer count tokens result."""
    total_tokens: Optional[int] = Field(default=None, description='The total number of tokens.')

class ComputeTokensResult(_common.BaseModel):
    """Local tokenizer compute tokens result."""
    tokens_info: Optional[list[TokensInfo]] = Field(default=None, description='Lists of tokens info from the input.')

class CreateTuningJobParameters(_common.BaseModel):
    """Fine-tuning job creation parameters - optional fields."""
    base_model: Optional[str] = Field(default=None, description='The base model that is being tuned, e.g., "gemini-flash-latest".')
    training_dataset: Optional[TuningDataset] = Field(default=None, description='Cloud Storage path to file containing training dataset for tuning. The dataset must be formatted as a JSONL file.')
    config: Optional[CreateTuningJobConfig] = Field(default=None, description='Configuration for the tuning job.')

class EmbedContentParameters(_common.BaseModel):
    """Parameters for the embed_content method."""
    model: Optional[str] = Field(default=None, description='ID of the model to use. For a list of models, see `Google models\n    <https://cloud.google.com/vertex-ai/generative-ai/docs/learn/models>`_.')
    contents: Optional[ContentListUnion] = Field(default=None, description='The content to embed. Only the `parts.text` fields will be counted.\n      ')
    config: Optional[EmbedContentConfig] = Field(default=None, description='Configuration that contains optional parameters.\n      ')

class UserContent(Content):
    """UserContent facilitates the creation of a Content object with a user role.

  Example usages:


  - Create a user Content object with a string:
    user_content = UserContent("Why is the sky blue?")
  - Create a user Content object with a file data Part object:
    user_content = UserContent(Part.from_uri(file_uri="gs://bucket/file.txt",
    mime_type="text/plain"))
  - Create a user Content object with byte data Part object:
    user_content = UserContent(Part.from_bytes(data=b"Hello, World!",
    mime_type="text/plain"))

    You can create a user Content object using other classmethods in the Part
    class as well.
    You can also create a user Content using a list of Part objects or strings.
  """
    role: Literal['user'] = Field(default='user', init=False, frozen=True)
    parts: list[Part] = Field()

    def __init__(self, parts: Union['PartUnionDict', list['PartUnionDict'], list['Part']]):
        from . import _transformers as t
        super().__init__(parts=t.t_parts(parts=parts))

class ModelContent(Content):
    """ModelContent facilitates the creation of a Content object with a model role.

  Example usages:

  - Create a model Content object with a string:
    model_content = ModelContent("Why is the sky blue?")
  - Create a model Content object with a file data Part object:
    model_content = ModelContent(Part.from_uri(file_uri="gs://bucket/file.txt",
    mime_type="text/plain"))
  - Create a model Content object with byte data Part object:
    model_content = ModelContent(Part.from_bytes(data=b"Hello, World!",
    mime_type="text/plain"))

    You can create a model Content object using other classmethods in the Part
    class as well.
    You can also create a model Content using a list of Part objects or strings.
  """
    role: Literal['model'] = Field(default='model', init=False, frozen=True)
    parts: list[Part] = Field()

    def __init__(self, parts: Union['PartUnionDict', list['PartUnionDict'], list['Part']]):
        from . import _transformers as t
        super().__init__(parts=t.t_parts(parts=parts))

class CustomOutputFormatConfig(_common.BaseModel):
    """Config for custom output format."""
    return_raw_output: Optional[bool] = Field(default=None, description='Optional. Whether to return raw output.')

class BleuSpec(_common.BaseModel):
    """Spec for bleu metric."""
    use_effective_order: Optional[bool] = Field(default=None, description='Optional. Whether to use_effective_order to compute bleu score.')

class Metric(_common.BaseModel):
    """The metric used for evaluation."""
    name: Optional[str] = Field(default=None, description='The name of the metric.')
    custom_function: Optional[Callable[..., Any]] = Field(default=None, description='The custom function that defines the end-to-end logic for metric computation.')
    prompt_template: Optional[str] = Field(default=None, description='The prompt template for the metric.')
    judge_model_system_instruction: Optional[str] = Field(default=None, description='The system instruction for the judge model.')
    return_raw_output: Optional[bool] = Field(default=None, description='Whether to return the raw output from the judge model.')
    parse_and_reduce_fn: Optional[Callable[..., Any]] = Field(default=None, description='The parse and reduce function for the judge model.')
    aggregate_summary_fn: Optional[Callable[..., Any]] = Field(default=None, description='The aggregate summary function for the judge model.')
    model_config = ConfigDict(extra='allow')
    _is_predefined: bool = PrivateAttr(default=False)
    _config_source: Optional[str] = PrivateAttr(default=None)
    _version: Optional[str] = PrivateAttr(default=None)

    @model_validator(mode='after')
    def validate_name(self) -> 'Metric':
        if not self.name:
            raise ValueError('Metric name cannot be empty.')
        self.name = self.name.lower()
        return self

class PairwiseMetricSpec(_common.BaseModel):
    """Spec for pairwise metric."""
    metric_prompt_template: Optional[str] = Field(default=None, description='Required. Metric prompt template for pairwise metric.')
    baseline_response_field_name: Optional[str] = Field(default=None, description='Optional. The field name of the baseline response.')
    candidate_response_field_name: Optional[str] = Field(default=None, description='Optional. The field name of the candidate response.')
    custom_output_format_config: Optional[CustomOutputFormatConfig] = Field(default=None, description='Optional. CustomOutputFormatConfig allows customization of metric output. When this config is set, the default output is replaced with the raw output string. If a custom format is chosen, the `pairwise_choice` and `explanation` fields in the corresponding metric result will be empty.')
    system_instruction: Optional[str] = Field(default=None, description='Optional. System instructions for pairwise metric.')

class PointwiseMetricSpec(_common.BaseModel):
    """Spec for pointwise metric."""
    metric_prompt_template: Optional[str] = Field(default=None, description='Required. Metric prompt template for pointwise metric.')
    custom_output_format_config: Optional[CustomOutputFormatConfig] = Field(default=None, description='Optional. CustomOutputFormatConfig allows customization of metric output. By default, metrics return a score and explanation. When this config is set, the default output is replaced with either: - The raw output string. - A parsed output based on a user-defined schema. If a custom format is chosen, the `score` and `explanation` fields in the corresponding metric result will be empty.')
    system_instruction: Optional[str] = Field(default=None, description='Optional. System instructions for pointwise metric.')

class RougeSpec(_common.BaseModel):
    """Spec for rouge metric."""
    rouge_type: Optional[str] = Field(default=None, description='Optional. Supported rouge types are rougen[1-9], rougeL, and rougeLsum.')
    split_summaries: Optional[bool] = Field(default=None, description='Optional. Whether to split summaries while using rougeLsum.')
    use_stemmer: Optional[bool] = Field(default=None, description='Optional. Whether to use stemmer to compute rouge score.')

class PredefinedMetricSpec(_common.BaseModel):
    """Spec for predefined metric."""
    metric_spec_name: Optional[str] = Field(default=None, description='The name of a pre-defined metric, such as "instruction_following_v1" or\n      "text_quality_v1".')
    metric_spec_parameters: Optional[dict[str, Any]] = Field(default=None, description='The parameters needed to run the pre-defined metric.')
    step_autorater_configs: Optional[dict[str, AutoraterConfig]] = Field(default=None, description='Optional. Per-step autorater overrides for this predefined metric. Keys are evaluation stage names (snake_case). Valid keys: "intent_extraction", "rubric_generation", "rubric_validation". Unknown keys return INVALID_ARGUMENT.')

class RubricGenerationSpec(_common.BaseModel):
    """Specification for how rubrics should be generated."""
    prompt_template: Optional[str] = Field(default=None, description='Template for the prompt used to generate rubrics.')
    rubric_content_type: Optional[RubricContentType] = Field(default=None, description='The type of rubric content to be generated.')
    rubric_type_ontology: Optional[list[str]] = Field(default=None, description='An optional, pre-defined list of allowed types for generated rubrics.\n      If this field is provided, it implies `include_rubric_type` should be true,\n      and the generated rubric types should be chosen from this ontology.')

class EvaluationParserConfigCustomCodeParserConfig(_common.BaseModel):
    """Configuration for parsing the LLM response using custom code.

  This data type is not supported in Gemini API.
  """
    parsing_function: Optional[str] = Field(default=None, description='Required. Python function for parsing results. The function should be defined within this string. The function takes a list of strings (LLM responses) and should return either a list of dictionaries (for rubrics) or a single dictionary (for a metric result). Example function signature: def parse(responses: list[str]) -> list[dict[str, Any]] | dict[str, Any]: When parsing rubrics, return a list of dictionaries, where each dictionary represents a Rubric. Example for rubrics: [ { "content": {"property": {"description": "The response is factual."}}, "type": "FACTUALITY", "importance": "HIGH" }, { "content": {"property": {"description": "The response is fluent."}}, "type": "FLUENCY", "importance": "MEDIUM" } ] When parsing critique results, return a dictionary representing a MetricResult. Example for a metric result: { "score": 0.8, "explanation": "The model followed most instructions.", "rubric_verdicts": [...] } ... code for result extraction and aggregation')
    code_execution_region: Optional[str] = Field(default=None, description="Optional. The region to use for code execution. If set, the Code Execution Sandbox will be invoked in the specified region regardless of the request's originating region. Must be a region where the Code Execution Sandbox is available. For the current list of [supported regions](https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/locations). If unset, the request's originating region is used.")

class EvaluationParserConfig(_common.BaseModel):
    """Config for parsing LLM responses.

  It can be used to parse the LLM response to be evaluated, or the LLM response
  from LLM-based metrics/Autoraters. This data type is not supported in Gemini
  API.
  """
    custom_code_parser_config: Optional[EvaluationParserConfigCustomCodeParserConfig] = Field(default=None, description='Optional. Use custom code to parse the LLM response.')

class LLMBasedMetricSpec(_common.BaseModel):
    """Specification for an LLM based metric."""
    metric_prompt_template: Optional[str] = Field(default=None, description='Template for the prompt sent to the judge model.')
    system_instruction: Optional[str] = Field(default=None, description='System instruction for the judge model.')
    judge_autorater_config: Optional[AutoraterConfig] = Field(default=None, description='Optional configuration for the judge LLM (Autorater).')
    rubric_group_key: Optional[str] = Field(default=None, description='Use a pre-defined group of rubrics associated with the input.\n      Refers to a key in the rubric_groups map of EvaluationInstance.')
    predefined_rubric_generation_spec: Optional[PredefinedMetricSpec] = Field(default=None, description='Dynamically generate rubrics using a predefined spec.')
    rubric_generation_spec: Optional[RubricGenerationSpec] = Field(default=None, description='Dynamically generate rubrics using this specification.')
    additional_config: Optional[dict[str, Any]] = Field(default=None, description='Optional. Optional additional configuration for the metric.')
    result_parser_config: Optional[EvaluationParserConfig] = Field(default=None, description='Optional. The parser config for the metric result.')

class CustomCodeExecutionSpec(_common.BaseModel):
    """Specifies a metric that is computed by running user-defined Python functions remotely."""
    evaluation_function: Optional[str] = Field(default=None, description='A string representing a user-defined function for evaluation.\n  Expected user to define the following function, e.g.:\n    def evaluate(instance: dict[str, Any]) -> float:\n  Please include this function signature in the code snippet.\n  Instance is the evaluation instance, any fields populated in the instance\n  are available to the function as instance[field_name].')
    code_execution_region: Optional[str] = Field(default=None, description="Optional. The region to use for code execution. If set, the Code Execution Sandbox will be invoked in the specified region regardless of the request's originating region. Must be a region where the Code Execution Sandbox is available. For the current list of [supported regions](https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/locations). If unset, the request's originating region is used; requests from regions where the sandbox is unavailable will fail with UNIMPLEMENTED.")

class ComputationBasedMetricSpec(_common.BaseModel):
    """Specification for a computation based metric."""
    type: Optional[ComputationBasedMetricType] = Field(default=None, description='The type of the computation based metric.')
    parameters: Optional[dict[str, Any]] = Field(default=None, description='A map of parameters for the metric. ROUGE example: {"rouge_type": "rougeL", "split_summaries": True, "use_stemmer": True}. BLEU example: {"use_effective_order": True}.')

class UnifiedMetric(_common.BaseModel):
    """The unified metric used for evaluation."""
    bleu_spec: Optional[BleuSpec] = Field(default=None, description='The Bleu metric spec.')
    rouge_spec: Optional[RougeSpec] = Field(default=None, description='The rouge metric spec.')
    pointwise_metric_spec: Optional[PointwiseMetricSpec] = Field(default=None, description='The pointwise metric spec.')
    llm_based_metric_spec: Optional[LLMBasedMetricSpec] = Field(default=None, description='The spec for an LLM based metric.')
    custom_code_execution_spec: Optional[CustomCodeExecutionSpec] = Field(default=None, description='The spec for a custom code execution metric.')
    predefined_metric_spec: Optional[PredefinedMetricSpec] = Field(default=None, description='The spec for a pre-defined metric.')
    computation_based_metric_spec: Optional[ComputationBasedMetricSpec] = Field(default=None, description='The spec for a computation based metric.')

class UploadToFileSearchStoreResponse(_common.BaseModel):
    """The response when long-running operation for uploading a file to a FileSearchStore complete."""
    sdk_http_response: Optional[HttpResponse] = Field(default=None, description='Used to retain the full HTTP response.')
    parent: Optional[str] = Field(default=None, description='The name of the FileSearchStore containing Documents.')
    document_name: Optional[str] = Field(default=None, description='The identifier for the Document imported.')

class UploadToFileSearchStoreOperation(_common.BaseModel, Operation):
    """Long-running operation for uploading a file to a FileSearchStore."""
    response: Optional[UploadToFileSearchStoreResponse] = Field(default=None, description='The result of the UploadToFileSearchStore operation, available when the operation is done.')

class DownloadMediaConfig(_common.BaseModel):
    """Used to override the default configuration."""
    http_options: Optional[HttpOptions] = Field(default=None, description='Used to override HTTP request options.')
