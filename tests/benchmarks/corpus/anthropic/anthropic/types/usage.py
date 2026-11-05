
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from .._models import BaseModel
from .cache_creation import CacheCreation
from .server_tool_usage import ServerToolUsage
from .output_tokens_details import OutputTokensDetails

class Usage(BaseModel):
    cache_creation: Optional[CacheCreation] = None
    cache_creation_input_tokens: Optional[int] = None
    cache_read_input_tokens: Optional[int] = None
    inference_geo: Optional[str] = None
    input_tokens: int
    output_tokens: int
    output_tokens_details: Optional[OutputTokensDetails] = None
    server_tool_use: Optional[ServerToolUsage] = None
    service_tier: Optional[Literal['standard', 'priority', 'batch']] = None
    speed: Optional[Literal['standard', 'fast']] = None
