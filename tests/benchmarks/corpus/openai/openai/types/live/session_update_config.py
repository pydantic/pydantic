# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ..._utils import PropertyInfo
from ..._models import BaseModel
from .decision_trigger import DecisionTrigger
from .client_delegation import ClientDelegation
from .decisions_delegation_update_config import DecisionsDelegationUpdateConfig
from .responses_delegation_update_config import ResponsesDelegationUpdateConfig

class DelegationResponses(BaseModel):
    """
    Update the Responses backend for an existing Live session without changing delegation ownership.
    """
    type: Literal['responses']
    acknowledgement_delay_ms: Optional[int] = None
    responses: Optional[ResponsesDelegationUpdateConfig] = None

class DelegationDecisions(BaseModel):
    type: Literal['decisions']
    acknowledgement_delay_ms: Optional[int] = None
    decisions: Optional[DecisionsDelegationUpdateConfig] = None
Delegation: TypeAlias = Annotated[Union[ClientDelegation, DelegationResponses, DelegationDecisions, None], PropertyInfo(discriminator='type')]

class SessionUpdateConfig(BaseModel):
    """
    Changes to an active Live session's delegation settings and transcript triggers.
    """
    delegation: Optional[Delegation] = None
    triggers: Optional[List[DecisionTrigger]] = None
