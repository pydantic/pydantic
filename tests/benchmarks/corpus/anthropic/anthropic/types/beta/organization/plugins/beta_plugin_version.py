
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List, Union, Optional
from datetime import datetime
from typing_extensions import Literal, Annotated, TypeAlias
from ....._models import BaseModel, UnionDiscriminator
from ..beta_plugin_api_actor import BetaPluginAPIActor
from ..beta_plugin_component import BetaPluginComponent
from ..beta_plugin_user_actor import BetaPluginUserActor
from ..beta_plugin_content_scan import BetaPluginContentScan
CreatedBy: TypeAlias = Annotated[Union[BetaPluginUserActor, BetaPluginAPIActor, None], UnionDiscriminator('type')]

class BetaPluginVersion(BaseModel):
    id: str
    components: Optional[List[BetaPluginComponent]] = None
    content_scan: Optional[BetaPluginContentScan] = None
    created_at: datetime
    created_by: Optional[CreatedBy] = None
    description: Optional[str] = None
    display_name: Optional[str] = None
    manifest_version: Optional[str] = None
    plugin_id: str
    reach: Optional[Literal['contained', 'privileged', 'remote']] = None
    release_notes: Optional[str] = None
    type: Literal['plugin_version']
