
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union, Optional
from datetime import datetime
from typing_extensions import Literal, Annotated, TypeAlias
from ...._models import BaseModel, UnionDiscriminator
from .beta_managed_agents_file_rubric import BetaManagedAgentsFileRubric
from .beta_managed_agents_text_rubric import BetaManagedAgentsTextRubric
Rubric: TypeAlias = Annotated[Union[BetaManagedAgentsFileRubric, BetaManagedAgentsTextRubric], UnionDiscriminator('type')]

class BetaManagedAgentsUserDefineOutcomeEvent(BaseModel):
    """Echo of a `user.define_outcome` input event.

    Carries the server-generated `outcome_id` that subsequent `span.outcome_evaluation_*` events reference.
    """
    id: str
    description: str
    max_iterations: Optional[int] = None
    outcome_id: str
    processed_at: datetime
    rubric: Rubric
    type: Literal['user.define_outcome']
