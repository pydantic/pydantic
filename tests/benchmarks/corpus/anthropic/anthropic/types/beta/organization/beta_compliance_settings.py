
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel
from .beta_compliance_settings_state import BetaComplianceSettingsState

class BetaComplianceSettings(BaseModel):
    state: BetaComplianceSettingsState
    type: Literal['compliance_settings']
