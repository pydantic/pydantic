
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from ...._models import BaseModel

class BetaPluginMarketplaceValidationPluginError(BaseModel):
    error: str
    error_code: str
    name: str
