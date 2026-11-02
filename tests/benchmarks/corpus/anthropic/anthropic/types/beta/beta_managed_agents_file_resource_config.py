
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class BetaManagedAgentsFileResourceConfig(BaseModel):
    """A file mounted into each session's container."""
    file_id: str
    type: Literal['file']
    mount_path: Optional[str] = None
