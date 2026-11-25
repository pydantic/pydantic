
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal, TypeAlias
UserProfileEnforcementActionReason: TypeAlias = Literal['unsupported_region', 'fraud_or_abuse', 'high_harm', 'usage_policy_violation', 'account_compromise', 'unspecified']
