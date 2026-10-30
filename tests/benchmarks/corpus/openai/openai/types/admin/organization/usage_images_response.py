# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ...._utils import PropertyInfo
from ...._models import BaseModel
from .cost_quantity_unit import CostQuantityUnit

class DataResultOrganizationUsageCompletionsResult(BaseModel):
    """The aggregated completions usage details of the specific time bucket."""
    input_tokens: int
    num_model_requests: int
    object: Literal['organization.usage.completions.result']
    output_tokens: int
    api_key_id: Optional[str] = None
    api_source: Optional[Literal['agents_api', 'unlabeled']] = None
    batch: Optional[bool] = None
    input_audio_tokens: Optional[int] = None
    input_cache_write_12h_tokens: Optional[int] = None
    input_cache_write_30m_tokens: Optional[int] = None
    input_cache_write_tokens: Optional[int] = None
    input_cached_audio_tokens: Optional[int] = None
    input_cached_image_tokens: Optional[int] = None
    input_cached_text_tokens: Optional[int] = None
    input_cached_tokens: Optional[int] = None
    input_image_tokens: Optional[int] = None
    input_text_tokens: Optional[int] = None
    input_uncached_tokens: Optional[int] = None
    model: Optional[str] = None
    output_audio_tokens: Optional[int] = None
    output_image_tokens: Optional[int] = None
    output_text_tokens: Optional[int] = None
    project_id: Optional[str] = None
    service_tier: Optional[str] = None
    user_id: Optional[str] = None

class DataResultOrganizationUsageEmbeddingsResult(BaseModel):
    """The aggregated embeddings usage details of the specific time bucket."""
    input_tokens: int
    num_model_requests: int
    object: Literal['organization.usage.embeddings.result']
    api_key_id: Optional[str] = None
    model: Optional[str] = None
    project_id: Optional[str] = None
    user_id: Optional[str] = None

class DataResultOrganizationUsageModerationsResult(BaseModel):
    """The aggregated moderations usage details of the specific time bucket."""
    input_tokens: int
    num_model_requests: int
    object: Literal['organization.usage.moderations.result']
    api_key_id: Optional[str] = None
    model: Optional[str] = None
    project_id: Optional[str] = None
    user_id: Optional[str] = None

class DataResultOrganizationUsageImagesResult(BaseModel):
    """The aggregated images usage details of the specific time bucket."""
    images: int
    num_model_requests: int
    object: Literal['organization.usage.images.result']
    api_key_id: Optional[str] = None
    model: Optional[str] = None
    project_id: Optional[str] = None
    size: Optional[str] = None
    source: Optional[str] = None
    user_id: Optional[str] = None

class DataResultOrganizationUsageAudioSpeechesResult(BaseModel):
    """The aggregated audio speeches usage details of the specific time bucket."""
    characters: int
    num_model_requests: int
    object: Literal['organization.usage.audio_speeches.result']
    api_key_id: Optional[str] = None
    model: Optional[str] = None
    project_id: Optional[str] = None
    user_id: Optional[str] = None

class DataResultOrganizationUsageAudioTranscriptionsResult(BaseModel):
    """The aggregated audio transcriptions usage details of the specific time bucket."""
    num_model_requests: int
    object: Literal['organization.usage.audio_transcriptions.result']
    seconds: int
    api_key_id: Optional[str] = None
    model: Optional[str] = None
    project_id: Optional[str] = None
    user_id: Optional[str] = None

class DataResultOrganizationUsageVectorStoresResult(BaseModel):
    """The aggregated vector stores usage details of the specific time bucket."""
    object: Literal['organization.usage.vector_stores.result']
    usage_bytes: int
    project_id: Optional[str] = None

class DataResultOrganizationUsageCodeInterpreterSessionsResult(BaseModel):
    """
    The aggregated code interpreter sessions usage details of the specific time bucket.
    """
    num_sessions: int
    object: Literal['organization.usage.code_interpreter_sessions.result']
    project_id: Optional[str] = None

class DataResultOrganizationUsageFileSearchesResult(BaseModel):
    """The aggregated file search calls usage details of the specific time bucket."""
    num_requests: int
    object: Literal['organization.usage.file_searches.result']
    api_key_id: Optional[str] = None
    project_id: Optional[str] = None
    user_id: Optional[str] = None
    vector_store_id: Optional[str] = None

class DataResultOrganizationUsageWebSearchesResult(BaseModel):
    """The aggregated web search calls usage details of the specific time bucket."""
    num_model_requests: int
    num_requests: int
    object: Literal['organization.usage.web_searches.result']
    api_key_id: Optional[str] = None
    api_source: Optional[Literal['agents_api', 'unlabeled']] = None
    context_level: Optional[str] = None
    model: Optional[str] = None
    project_id: Optional[str] = None
    user_id: Optional[str] = None

class DataResultOrganizationCostsResultAmount(BaseModel):
    """The monetary value in its associated currency."""
    currency: Optional[str] = None
    value: Optional[float] = None

class DataResultOrganizationCostsResult(BaseModel):
    """The aggregated costs details of the specific time bucket."""
    object: Literal['organization.costs.result']
    amount: Optional[DataResultOrganizationCostsResultAmount] = None
    api_key_id: Optional[str] = None
    api_source: Optional[Literal['agents_api', 'unlabeled']] = None
    line_item: Optional[str] = None
    project_id: Optional[str] = None
    quantity: Optional[float] = None
    quantity_unit: Optional[CostQuantityUnit] = None
    user_id: Optional[str] = None
DataResult: TypeAlias = Annotated[Union[DataResultOrganizationUsageCompletionsResult, DataResultOrganizationUsageEmbeddingsResult, DataResultOrganizationUsageModerationsResult, DataResultOrganizationUsageImagesResult, DataResultOrganizationUsageAudioSpeechesResult, DataResultOrganizationUsageAudioTranscriptionsResult, DataResultOrganizationUsageVectorStoresResult, DataResultOrganizationUsageCodeInterpreterSessionsResult, DataResultOrganizationUsageFileSearchesResult, DataResultOrganizationUsageWebSearchesResult, DataResultOrganizationCostsResult], PropertyInfo(discriminator='object')]

class Data(BaseModel):
    end_time: int
    object: Literal['bucket']
    results: List[DataResult]
    start_time: int

class UsageImagesResponse(BaseModel):
    data: List[Data]
    has_more: bool
    next_page: Optional[str] = None
    object: Literal['page']
