
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from ...._models import BaseModel

class BetaManagedAgentsSessionThreadStats(BaseModel):
    """Timing statistics for a session thread."""
    active_seconds: Optional[float] = None
    duration_seconds: Optional[float] = None
    startup_seconds: Optional[float] = None
