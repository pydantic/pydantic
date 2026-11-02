
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ...._models import BaseModel

class BetaPluginContentScan(BaseModel):
    assessment: Optional[Literal['fail', 'pass', 'unknown', 'warn']] = None
    reason: Optional[str] = None
    status: Literal['completed', 'errored', 'processing']
