
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union, Optional
from datetime import datetime
from typing_extensions import Literal, Annotated, TypeAlias
from ..._models import BaseModel, UnionDiscriminator
from .aws_external_key_config import AWSExternalKeyConfig
from .gcp_external_key_config import GCPExternalKeyConfig
from .azure_external_key_config import AzureExternalKeyConfig
from .external_key_attached_attachment import ExternalKeyAttachedAttachment
from .external_key_unattached_attachment import ExternalKeyUnattachedAttachment
Attachment: TypeAlias = Annotated[Union[ExternalKeyAttachedAttachment, ExternalKeyUnattachedAttachment], UnionDiscriminator('type')]
ProviderConfig: TypeAlias = Annotated[Union[AWSExternalKeyConfig, GCPExternalKeyConfig, AzureExternalKeyConfig], UnionDiscriminator('type')]

class ExternalKey(BaseModel):
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
