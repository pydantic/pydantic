
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ..._models import BaseModel, UnionDiscriminator
from .sessions.beta_managed_agents_file_rubric import BetaManagedAgentsFileRubric
from .sessions.beta_managed_agents_text_rubric import BetaManagedAgentsTextRubric
Rubric: TypeAlias = Annotated[Union[BetaManagedAgentsFileRubric, BetaManagedAgentsTextRubric], UnionDiscriminator('type')]

class BetaManagedAgentsDeploymentUserDefineOutcomeEvent(BaseModel):
    """An outcome the agent should work toward. The agent begins work on receipt."""
    description: str
    rubric: Rubric
    type: Literal['user.define_outcome']
    max_iterations: Optional[int] = None
