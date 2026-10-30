# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ....._models import BaseModel

class ProjectRateLimit(BaseModel):
    """Represents a project rate limit config."""
    id: str
    max_requests_per_1_minute: int
    max_tokens_per_1_minute: int
    model: str
    object: Literal['project.rate_limit']
    batch_1_day_max_input_tokens: Optional[int] = None
    max_audio_megabytes_per_1_minute: Optional[int] = None
    max_images_per_1_minute: Optional[int] = None
    max_requests_per_1_day: Optional[int] = None
