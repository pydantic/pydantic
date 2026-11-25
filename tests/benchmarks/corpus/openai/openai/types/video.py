# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Union, Optional
from typing_extensions import Literal
from .._models import BaseModel
from .video_size import VideoSize
from .video_model import VideoModel
from .video_seconds import VideoSeconds
from .video_create_error import VideoCreateError

class Video(BaseModel):
    """Structured information describing a generated video job."""
    id: str
    completed_at: Optional[int] = None
    created_at: int
    error: Optional[VideoCreateError] = None
    expires_at: Optional[int] = None
    model: VideoModel
    object: Literal['video']
    progress: int
    prompt: Optional[str] = None
    remixed_from_video_id: Optional[str] = None
    seconds: Union[str, VideoSeconds]
    size: VideoSize
    status: Literal['queued', 'in_progress', 'completed', 'failed']
