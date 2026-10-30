
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from .._models import BaseModel

class CacheCreation(BaseModel):
    ephemeral_1h_input_tokens: int
    ephemeral_5m_input_tokens: int
