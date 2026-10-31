
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List, Optional
from datetime import datetime
from .._models import BaseModel
from .container_skill import ContainerSkill

class Container(BaseModel):
    """
    Information about the container used in the request (for the code execution tool)
    """
    id: str
    expires_at: datetime
    skills: Optional[List[ContainerSkill]] = None
