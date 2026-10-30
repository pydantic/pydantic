# Frozen from MCP 2.3.0; see corpus README.md and LICENSE.
from pydantic import BaseModel, ConfigDict

class WireModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
