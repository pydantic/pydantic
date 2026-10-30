# Frozen from MCP 2.3.0; see corpus README.md and LICENSE.
from pydantic import BaseModel, Field

class PKCEParameters(BaseModel):
    code_verifier: str = Field(..., min_length=43, max_length=128)
    code_challenge: str = Field(..., min_length=43, max_length=128)
