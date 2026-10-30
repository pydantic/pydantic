# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ..._utils import PropertyInfo
from ..._models import BaseModel
from .container_auto import ContainerAuto
from .local_environment import LocalEnvironment
from .container_reference import ContainerReference
Environment: TypeAlias = Annotated[Union[ContainerAuto, LocalEnvironment, ContainerReference, None], PropertyInfo(discriminator='type')]

class FunctionShellTool(BaseModel):
    """A tool that allows the model to execute shell commands."""
    type: Literal['shell']
    allowed_callers: Optional[List[Literal['direct', 'programmatic']]] = None
    environment: Optional[Environment] = None
