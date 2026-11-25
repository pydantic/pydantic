# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias
from ....._utils import PropertyInfo
from ....._models import BaseModel
from ...hosted_plugin import HostedPlugin

class FileHostedTemplateFileResourceFileID(BaseModel):
    """A project-scoped Files API reference resolved separately for each session."""
    file_id: str
    path: str
    type: Literal['file_id']

class FileHostedTemplateFileResourceInline(BaseModel):
    """Metadata for confidential inline file contents."""
    path: str
    size_bytes: int
    type: Literal['inline']
File: TypeAlias = Annotated[Union[FileHostedTemplateFileResourceFileID, FileHostedTemplateFileResourceInline], PropertyInfo(discriminator='type')]

class Network(BaseModel):
    """Runtime network access for each OpenAI-hosted environment."""
    access: Literal['enabled', 'disabled', 'restricted']
    allowed_domains: List[str]

class Packages(BaseModel):
    """Packages installed in each fresh OpenAI-hosted environment."""
    npm: List[str]
    python: List[str]
    system: List[str]

class SkillHostedTemplateSkillResourceSkillReference(BaseModel):
    """A skill resolved afresh from the Skills API whenever a session starts."""
    skill_id: str
    type: Literal['skill_reference']
    version: Optional[str] = None

class SkillHostedTemplateSkillResourceInline(BaseModel):
    """Safe metadata for an inline skill archive."""
    description: str
    name: str
    type: Literal['inline']
Skill: TypeAlias = Annotated[Union[SkillHostedTemplateSkillResourceSkillReference, SkillHostedTemplateSkillResourceInline], PropertyInfo(discriminator='type')]

class Desktop(BaseModel):
    """Desktop configuration for each OpenAI-hosted environment."""
    enabled: bool

class EnvironmentTemplate(BaseModel):
    """
    Reusable configuration that provisions a fresh OpenAI-hosted environment for each session.
    """
    id: str
    capability_directories: List[str]
    created_at: int
    files: List[File]
    name: Optional[str] = None
    network: Network
    object: Literal['agent.environment.template']
    packages: Packages
    plugins: List[HostedPlugin]
    skills: List[Skill]
    updated_at: int
    desktop: Optional[Desktop] = None
