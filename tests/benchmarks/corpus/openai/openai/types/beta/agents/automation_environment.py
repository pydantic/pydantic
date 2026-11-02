# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ...._utils import PropertyInfo
from ...._models import BaseModel
from ..hosted_plugin import HostedPlugin

class AutomationEnvironmentResourceNone(BaseModel):
    type: Literal['none']

class AutomationEnvironmentResourceOpenAIHostedDesktop(BaseModel):
    """Desktop overrides, or null to inherit the template or creation default."""
    enabled: bool

class AutomationEnvironmentResourceOpenAIHostedFileHostedTemplateFileResourceFileID(BaseModel):
    """A project-scoped Files API reference resolved separately for each session."""
    file_id: str
    path: str
    type: Literal['file_id']

class AutomationEnvironmentResourceOpenAIHostedFileHostedTemplateFileResourceInline(BaseModel):
    """Metadata for confidential inline file contents."""
    path: str
    size_bytes: int
    type: Literal['inline']
AutomationEnvironmentResourceOpenaiHostedFile: TypeAlias = Annotated[Union[AutomationEnvironmentResourceOpenAIHostedFileHostedTemplateFileResourceFileID, AutomationEnvironmentResourceOpenAIHostedFileHostedTemplateFileResourceInline], PropertyInfo(discriminator='type')]

class AutomationEnvironmentResourceOpenAIHostedNetwork(BaseModel):
    """Network overrides, or null to inherit the template or creation default."""
    access: Literal['enabled', 'disabled', 'restricted']
    allowed_domains: List[str]

class AutomationEnvironmentResourceOpenAIHostedPackages(BaseModel):
    """Package overrides, or null to inherit the template or creation default."""
    npm: List[str]
    python: List[str]
    system: List[str]

class AutomationEnvironmentResourceOpenAIHostedSkillHostedTemplateSkillResourceSkillReference(BaseModel):
    """A skill resolved afresh from the Skills API whenever a session starts."""
    skill_id: str
    type: Literal['skill_reference']
    version: Optional[str] = None

class AutomationEnvironmentResourceOpenAIHostedSkillHostedTemplateSkillResourceInline(BaseModel):
    """Safe metadata for an inline skill archive."""
    description: str
    name: str
    type: Literal['inline']
AutomationEnvironmentResourceOpenaiHostedSkill: TypeAlias = Annotated[Union[AutomationEnvironmentResourceOpenAIHostedSkillHostedTemplateSkillResourceSkillReference, AutomationEnvironmentResourceOpenAIHostedSkillHostedTemplateSkillResourceInline], PropertyInfo(discriminator='type')]

class AutomationEnvironmentResourceOpenAIHosted(BaseModel):
    """
    Hosted environment selection with confidential setup commands and variables omitted.
    """
    capability_directories: Optional[List[str]] = None
    container_size: Optional[Literal['small', 'medium', 'large']] = None
    desktop: Optional[AutomationEnvironmentResourceOpenAIHostedDesktop] = None
    environment_id: Optional[str] = None
    environment_template_id: Optional[str] = None
    files: Optional[List[AutomationEnvironmentResourceOpenaiHostedFile]] = None
    network: Optional[AutomationEnvironmentResourceOpenAIHostedNetwork] = None
    packages: Optional[AutomationEnvironmentResourceOpenAIHostedPackages] = None
    plugins: Optional[List[HostedPlugin]] = None
    skills: Optional[List[AutomationEnvironmentResourceOpenaiHostedSkill]] = None
    type: Literal['openai_hosted']

class AutomationEnvironmentResourceSelfHosted(BaseModel):
    capability_directories: List[str]
    environment_id: Optional[str] = None
    type: Literal['self_hosted']
    workspace_directory: str
AutomationEnvironment: TypeAlias = Annotated[Union[AutomationEnvironmentResourceNone, AutomationEnvironmentResourceOpenAIHosted, AutomationEnvironmentResourceSelfHosted], PropertyInfo(discriminator='type')]
