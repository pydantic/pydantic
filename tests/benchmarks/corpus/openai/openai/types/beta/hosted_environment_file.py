# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Literal, Annotated, TypeAlias
from ..._utils import PropertyInfo
from ..._models import BaseModel
from .hosted_environment_file_id import HostedEnvironmentFileID

class HostedEnvironmentFileResourceInline(BaseModel):
    """A file supplied inline when the session was created."""
    id: str
    path: str
    size_bytes: int
    type: Literal['inline']
HostedEnvironmentFile: TypeAlias = Annotated[Union[HostedEnvironmentFileID, HostedEnvironmentFileResourceInline], PropertyInfo(discriminator='type')]
