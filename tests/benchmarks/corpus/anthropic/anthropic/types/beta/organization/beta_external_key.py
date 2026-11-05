
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union, Optional
from datetime import datetime
from typing_extensions import Literal, Annotated, TypeAlias
from ...._models import BaseModel, UnionDiscriminator
from .beta_aws_external_key_config import BetaAWSExternalKeyConfig
from .beta_gcp_external_key_config import BetaGCPExternalKeyConfig
from .beta_azure_external_key_config import BetaAzureExternalKeyConfig
from .beta_external_key_attached_attachment import BetaExternalKeyAttachedAttachment
from .beta_external_key_unattached_attachment import BetaExternalKeyUnattachedAttachment
Attachment: TypeAlias = Annotated[Union[BetaExternalKeyAttachedAttachment, BetaExternalKeyUnattachedAttachment], UnionDiscriminator('type')]
ProviderConfig: TypeAlias = Annotated[Union[BetaAWSExternalKeyConfig, BetaGCPExternalKeyConfig, BetaAzureExternalKeyConfig], UnionDiscriminator('type')]

class BetaExternalKey(BaseModel):
    """CMEK external key config belonging to the caller's organization.

    Configs are organization-scoped. Workspaces attach to a config; once any
    workspace references it, the provider fields become effectively immutable
    (existing encrypted data needs the config for decrypt).
    """
    id: str
    attachment: Attachment
    created_at: datetime
    display_name: Optional[str] = None
    geo: str
    provider_config: ProviderConfig
    type: Literal['external_key']
    updated_at: datetime
