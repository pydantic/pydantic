# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from ...._models import BaseModel

class ChatSessionFileUpload(BaseModel):
    """Upload permissions and limits applied to the session."""
    enabled: bool
    max_file_size: Optional[int] = None
    max_files: Optional[int] = None
