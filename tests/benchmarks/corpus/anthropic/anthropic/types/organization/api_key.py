
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union, Optional
from datetime import datetime
from typing_extensions import Literal, Annotated, TypeAlias
from ..._models import BaseModel, UnionDiscriminator
from .api_key_created_by import APIKeyCreatedBy
from .api_key_user_actor import APIKeyUserActor
from .api_key_workspace_scope import APIKeyWorkspaceScope
from .api_key_organization_scope import APIKeyOrganizationScope
from .api_key_service_account_actor import APIKeyServiceAccountActor
Principal: TypeAlias = Annotated[Union[APIKeyUserActor, APIKeyServiceAccountActor, None], UnionDiscriminator('type')]
Scope: TypeAlias = Annotated[Union[APIKeyOrganizationScope, APIKeyWorkspaceScope], UnionDiscriminator('type')]

class APIKey(BaseModel):
    id: str
    created_at: datetime
    created_by: Optional[APIKeyCreatedBy] = None
    expires_at: Optional[datetime] = None
    name: str
    partial_key_hint: Optional[str] = None
    principal: Optional[Principal] = None
    scope: Scope
    status: Literal['active', 'archived', 'expired', 'inactive']
    type: Literal['api_key']
