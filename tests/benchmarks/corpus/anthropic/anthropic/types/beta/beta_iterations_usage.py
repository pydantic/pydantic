
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List, Union
from typing_extensions import Annotated, TypeAlias
from ..._models import UnionDiscriminator
from .beta_message_iteration_usage import BetaMessageIterationUsage
from .beta_compaction_iteration_usage import BetaCompactionIterationUsage
from .beta_advisor_message_iteration_usage import BetaAdvisorMessageIterationUsage
from .beta_fallback_message_iteration_usage import BetaFallbackMessageIterationUsage
BetaIterationsUsageItem: TypeAlias = Annotated[Union[BetaMessageIterationUsage, BetaCompactionIterationUsage, BetaAdvisorMessageIterationUsage, BetaFallbackMessageIterationUsage], UnionDiscriminator('type')]
BetaIterationsUsage: TypeAlias = List[BetaIterationsUsageItem]
