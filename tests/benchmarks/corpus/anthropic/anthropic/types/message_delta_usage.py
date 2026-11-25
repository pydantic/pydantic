
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from .._models import BaseModel
from .server_tool_usage import ServerToolUsage
from .output_tokens_details import OutputTokensDetails

class MessageDeltaUsage(BaseModel):
    cache_creation_input_tokens: Optional[int] = None
    cache_read_input_tokens: Optional[int] = None
    input_tokens: Optional[int] = None
    output_tokens: int
    output_tokens_details: Optional[OutputTokensDetails] = None
    server_tool_use: Optional[ServerToolUsage] = None
