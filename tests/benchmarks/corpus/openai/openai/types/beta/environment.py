# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ..._utils import PropertyInfo
from ..._models import BaseModel
from .hosted_skill import HostedSkill
from .hosted_plugin import HostedPlugin
from .hosted_environment_file import HostedEnvironmentFile

class EnvironmentResourceNone(BaseModel):
    """
    The session talks to CCA without selecting or provisioning an execution environment.
    """
    type: Literal['none']

class EnvironmentResourceOpenAIHostedNetwork(BaseModel):
    """The effective network access policy for the environment."""
    access: Literal['enabled', 'disabled', 'restricted']
    allowed_domains: List[str]

class EnvironmentResourceOpenAIHostedPackages(BaseModel):
    """Packages installed in the environment."""
    npm: List[str]
    python: List[str]
    system: List[str]

class EnvironmentResourceOpenAIHostedDesktop(BaseModel):
    """The effective desktop configuration."""
    enabled: bool

class EnvironmentResourceOpenAIHosted(BaseModel):
    """An environment hosted by OpenAI."""
    id: str
    capability_directories: List[str]
    files: List[HostedEnvironmentFile]
    network: EnvironmentResourceOpenAIHostedNetwork
    packages: EnvironmentResourceOpenAIHostedPackages
    plugins: List[HostedPlugin]
    skills: List[HostedSkill]
    type: Literal['openai_hosted']
    container_size: Optional[Literal['small', 'medium', 'large']] = None
    desktop: Optional[EnvironmentResourceOpenAIHostedDesktop] = None

class EnvironmentResourceSelfHosted(BaseModel):
    """An environment hosted by the application."""
    id: str
    capability_directories: List[str]
    remote_url: str
    type: Literal['self_hosted']
    workspace_directory: str
Environment: TypeAlias = Annotated[Union[EnvironmentResourceNone, EnvironmentResourceOpenAIHosted, EnvironmentResourceSelfHosted], PropertyInfo(discriminator='type')]
