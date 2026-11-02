
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from ...._models import BaseModel
from .beta_plugin_marketplace_validation_plugin_error import BetaPluginMarketplaceValidationPluginError
from .beta_plugin_marketplace_validation_plugin_warnings import BetaPluginMarketplaceValidationPluginWarnings

class BetaPluginMarketplaceValidationReport(BaseModel):
    """
    The outcome of validating plugin marketplace content: a report, not a
    stored object, so nothing in it can be retrieved afterwards.
    """
    commit_sha: Optional[str] = None
    manifest_error: Optional[str] = None
    manifest_error_code: Optional[str] = None
    plugin_errors: List[BetaPluginMarketplaceValidationPluginError]
    plugin_warnings: List[BetaPluginMarketplaceValidationPluginWarnings]
    ref: Optional[str] = None
    total_plugin_count: int
    type: Literal['plugin_marketplace_validation_report']
    valid: bool
