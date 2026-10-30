
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ..._models import BaseModel, UnionDiscriminator
from .organization_rate_limit_value import OrganizationRateLimitValue
from .organization_rate_limit_batch_group import OrganizationRateLimitBatchGroup
from .organization_rate_limit_files_group import OrganizationRateLimitFilesGroup
from .organization_rate_limit_model_group import OrganizationRateLimitModelGroup
from .organization_rate_limit_skills_group import OrganizationRateLimitSkillsGroup
from .organization_rate_limit_web_search_group import OrganizationRateLimitWebSearchGroup
from .organization_rate_limit_token_count_group import OrganizationRateLimitTokenCountGroup
Group: TypeAlias = Annotated[Union[OrganizationRateLimitModelGroup, OrganizationRateLimitBatchGroup, OrganizationRateLimitTokenCountGroup, OrganizationRateLimitFilesGroup, OrganizationRateLimitSkillsGroup, OrganizationRateLimitWebSearchGroup], UnionDiscriminator('type')]

class OrganizationRateLimit(BaseModel):
    id: str
    group: Group
    limits: List[OrganizationRateLimitValue]
    models: Optional[List[str]] = None
    type: Literal['rate_limit']
