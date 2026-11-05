
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Annotated, TypeAlias
from .._models import UnionDiscriminator
from .user_profile_enforcement_action_ban import UserProfileEnforcementActionBan
from .user_profile_enforcement_action_restriction import UserProfileEnforcementActionRestriction
UserProfileEnforcementAction: TypeAlias = Annotated[Union[UserProfileEnforcementActionRestriction, UserProfileEnforcementActionBan], UnionDiscriminator('type')]
