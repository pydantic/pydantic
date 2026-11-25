
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union, Optional
from datetime import datetime
from typing_extensions import Literal, Annotated, TypeAlias
from ...._models import BaseModel, UnionDiscriminator
from .beta_api_key_created_by import BetaAPIKeyCreatedBy
from .beta_api_key_user_actor import BetaAPIKeyUserActor
from .beta_api_key_workspace_scope import BetaAPIKeyWorkspaceScope
from .beta_api_key_organization_scope import BetaAPIKeyOrganizationScope
from .beta_api_key_service_account_actor import BetaAPIKeyServiceAccountActor
Principal: TypeAlias = Annotated[Union[BetaAPIKeyUserActor, BetaAPIKeyServiceAccountActor, None], UnionDiscriminator('type')]
Scope: TypeAlias = Annotated[Union[BetaAPIKeyOrganizationScope, BetaAPIKeyWorkspaceScope], UnionDiscriminator('type')]

class BetaAPIKey(BaseModel):
    id: str
    created_at: datetime
    created_by: Optional[BetaAPIKeyCreatedBy] = None
    expires_at: Optional[datetime] = None
    name: str
    partial_key_hint: Optional[str] = None
    principal: Optional[Principal] = None
    scope: Scope
    status: Literal['active', 'archived', 'expired', 'inactive']
    type: Literal['api_key']
