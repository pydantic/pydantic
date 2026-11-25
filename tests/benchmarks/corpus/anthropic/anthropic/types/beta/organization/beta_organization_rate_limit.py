
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ...._models import BaseModel, UnionDiscriminator
from .beta_organization_rate_limit_value import BetaOrganizationRateLimitValue
from .beta_organization_rate_limit_batch_group import BetaOrganizationRateLimitBatchGroup
from .beta_organization_rate_limit_files_group import BetaOrganizationRateLimitFilesGroup
from .beta_organization_rate_limit_model_group import BetaOrganizationRateLimitModelGroup
from .beta_organization_rate_limit_skills_group import BetaOrganizationRateLimitSkillsGroup
from .beta_organization_rate_limit_web_search_group import BetaOrganizationRateLimitWebSearchGroup
from .beta_organization_rate_limit_token_count_group import BetaOrganizationRateLimitTokenCountGroup
Group: TypeAlias = Annotated[Union[BetaOrganizationRateLimitModelGroup, BetaOrganizationRateLimitBatchGroup, BetaOrganizationRateLimitTokenCountGroup, BetaOrganizationRateLimitFilesGroup, BetaOrganizationRateLimitSkillsGroup, BetaOrganizationRateLimitWebSearchGroup], UnionDiscriminator('type')]

class BetaOrganizationRateLimit(BaseModel):
    id: str
    group: Group
    limits: List[BetaOrganizationRateLimitValue]
    models: Optional[List[str]] = None
    type: Literal['rate_limit']
