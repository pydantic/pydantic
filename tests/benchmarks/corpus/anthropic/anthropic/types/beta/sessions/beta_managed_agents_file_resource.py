
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from datetime import datetime
from typing_extensions import Literal
from ...._models import BaseModel

class BetaManagedAgentsFileResource(BaseModel):
    id: str
    created_at: datetime
    file_id: str
    mount_path: str
    type: Literal['file']
    updated_at: datetime
