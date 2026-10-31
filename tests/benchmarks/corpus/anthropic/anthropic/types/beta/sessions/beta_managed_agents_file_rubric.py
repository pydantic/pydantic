
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class BetaManagedAgentsFileRubric(BaseModel):
    """Rubric referenced by a file uploaded via the Files API."""
    file_id: str
    type: Literal['file']
