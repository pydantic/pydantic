
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel
from .compliance_settings_state import ComplianceSettingsState

class OrganizationComplianceSettings(BaseModel):
    state: ComplianceSettingsState
    type: Literal['compliance_settings']
