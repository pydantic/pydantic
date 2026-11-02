
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Literal, Annotated, TypeAlias
from ...._models import BaseModel, UnionDiscriminator
from .beta_managed_agents_retry_status_retrying import BetaManagedAgentsRetryStatusRetrying
from .beta_managed_agents_retry_status_terminal import BetaManagedAgentsRetryStatusTerminal
from .beta_managed_agents_retry_status_exhausted import BetaManagedAgentsRetryStatusExhausted
RetryStatus: TypeAlias = Annotated[Union[BetaManagedAgentsRetryStatusRetrying, BetaManagedAgentsRetryStatusExhausted, BetaManagedAgentsRetryStatusTerminal], UnionDiscriminator('type')]

class BetaManagedAgentsCredentialHostUnreachableError(BaseModel):
    """
    An `environment_variable` credential's `auth.networking.allowed_hosts` includes a host the environment's network policy does not permit.
    """
    credential_id: str
    message: str
    retry_status: RetryStatus
    type: Literal['credential_host_unreachable_error']
    vault_id: str
