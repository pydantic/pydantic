
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List
from ...._models import BaseModel
from .beta_plugin_marketplace_validation_plugin_warning import BetaPluginMarketplaceValidationPluginWarning

class BetaPluginMarketplaceValidationPluginWarnings(BaseModel):
    name: str
    warnings: List[BetaPluginMarketplaceValidationPluginWarning]
