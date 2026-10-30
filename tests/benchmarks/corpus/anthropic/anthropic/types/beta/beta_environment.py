
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Dict, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ..._models import BaseModel, UnionDiscriminator
from .beta_cloud_config import BetaCloudConfig
from .beta_self_hosted_config import BetaSelfHostedConfig
Config: TypeAlias = Annotated[Union[BetaCloudConfig, BetaSelfHostedConfig], UnionDiscriminator('type')]

class BetaEnvironment(BaseModel):
    """Unified Environment resource for both cloud and self-hosted environments."""
    id: str
    archived_at: Optional[str] = None
    config: Config
    created_at: str
    description: Optional[str] = None
    metadata: Dict[str, str]
    name: str
    type: Literal['environment']
    updated_at: str
    scope: Optional[Literal['organization', 'account']] = None
