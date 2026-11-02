# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from .._models import BaseModel
from .batch_error import BatchError
from .batch_usage import BatchUsage
from .shared.metadata import Metadata
from .batch_request_counts import BatchRequestCounts

class Errors(BaseModel):
    data: Optional[List[BatchError]] = None
    object: Optional[str] = None

class Batch(BaseModel):
    id: str
    completion_window: str
    created_at: int
    endpoint: str
    input_file_id: str
    object: Literal['batch']
    status: Literal['validating', 'failed', 'in_progress', 'finalizing', 'completed', 'expired', 'cancelling', 'cancelled']
    cancelled_at: Optional[int] = None
    cancelling_at: Optional[int] = None
    completed_at: Optional[int] = None
    error_file_id: Optional[str] = None
    errors: Optional[Errors] = None
    expired_at: Optional[int] = None
    expires_at: Optional[int] = None
    failed_at: Optional[int] = None
    finalizing_at: Optional[int] = None
    in_progress_at: Optional[int] = None
    metadata: Optional[Metadata] = None
    model: Optional[str] = None
    output_file_id: Optional[str] = None
    request_counts: Optional[BatchRequestCounts] = None
    usage: Optional[BatchUsage] = None
