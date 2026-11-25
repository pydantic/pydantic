
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Annotated, TypeAlias
from ...._models import UnionDiscriminator
from .beta_compliance_settings_state_enabled import BetaComplianceSettingsStateEnabled
from .beta_compliance_settings_state_disabled import BetaComplianceSettingsStateDisabled
BetaComplianceSettingsState: TypeAlias = Annotated[Union[BetaComplianceSettingsStateEnabled, BetaComplianceSettingsStateDisabled], UnionDiscriminator('type')]
