# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List
from typing_extensions import Literal
from ...._models import BaseModel
from ..hosted_skill import HostedSkill
from ..hosted_plugin import HostedPlugin
from ..hosted_environment_file import HostedEnvironmentFile

class EnvironmentInfo(BaseModel):
    """Safe metadata for a first-class execution environment."""
    id: str
    files: List[HostedEnvironmentFile]
    object: Literal['agent.environment']
    plugins: List[HostedPlugin]
    skills: List[HostedSkill]
    status: Literal['pending', 'ready', 'connected', 'disconnected', 'suspended', 'expired', 'failed']
    type: Literal['openai_hosted', 'self_hosted']
