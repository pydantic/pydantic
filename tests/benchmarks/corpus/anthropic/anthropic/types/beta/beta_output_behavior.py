
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Annotated, TypeAlias
from ..._models import UnionDiscriminator
from .beta_output_behavior_create_new import BetaOutputBehaviorCreateNew
from .beta_output_behavior_update_existing import BetaOutputBehaviorUpdateExisting
BetaOutputBehavior: TypeAlias = Annotated[Union[BetaOutputBehaviorCreateNew, BetaOutputBehaviorUpdateExisting], UnionDiscriminator('type')]
