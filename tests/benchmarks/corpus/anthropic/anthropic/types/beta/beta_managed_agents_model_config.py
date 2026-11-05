
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ..._models import BaseModel, UnionDiscriminator
from .beta_managed_agents_model import BetaManagedAgentsModel
from .beta_managed_agents_effort_low import BetaManagedAgentsEffortLow
from .beta_managed_agents_effort_max import BetaManagedAgentsEffortMax
from .beta_managed_agents_effort_high import BetaManagedAgentsEffortHigh
from .beta_managed_agents_effort_xhigh import BetaManagedAgentsEffortXhigh
from .beta_managed_agents_effort_medium import BetaManagedAgentsEffortMedium
Effort: TypeAlias = Annotated[Union[BetaManagedAgentsEffortLow, BetaManagedAgentsEffortMedium, BetaManagedAgentsEffortHigh, BetaManagedAgentsEffortXhigh, BetaManagedAgentsEffortMax], UnionDiscriminator('type')]

class BetaManagedAgentsModelConfig(BaseModel):
    """Model identifier and configuration."""
    id: BetaManagedAgentsModel
    effort: Optional[Effort] = None
    inference_geo: Optional[str] = None
    speed: Optional[Literal['standard', 'fast']] = None
