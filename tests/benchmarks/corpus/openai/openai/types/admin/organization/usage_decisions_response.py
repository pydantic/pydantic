# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from ...._models import BaseModel

class DataResult(BaseModel):
    """The aggregated Decisions API usage details of the specific time bucket."""
    input_tokens: int
    num_model_requests: int
    object: Literal['organization.usage.decisions.result']
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

class Data(BaseModel):
    end_time: int
    object: Literal['bucket']
    results: List[DataResult]
    start_time: int

class UsageDecisionsResponse(BaseModel):
    data: List[Data]
    has_more: bool
    next_page: Optional[str] = None
    object: Literal['page']
