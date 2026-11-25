
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Annotated, TypeAlias
from ...._models import UnionDiscriminator
from .beta_managed_agents_api_actor import BetaManagedAgentsAPIActor
from .beta_managed_agents_user_actor import BetaManagedAgentsUserActor
from .beta_managed_agents_session_actor import BetaManagedAgentsSessionActor
from .beta_managed_agents_service_account_actor import BetaManagedAgentsServiceAccountActor
BetaManagedAgentsActor: TypeAlias = Annotated[Union[BetaManagedAgentsSessionActor, BetaManagedAgentsAPIActor, BetaManagedAgentsUserActor, BetaManagedAgentsServiceAccountActor], UnionDiscriminator('type')]
