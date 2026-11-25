# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from ....._models import BaseModel

class CodeInterpreter(BaseModel):
    """Permission state for a single hosted tool on a project."""
    enabled: bool

class FileSearch(BaseModel):
    """Permission state for a single hosted tool on a project."""
    enabled: bool

class ImageGeneration(BaseModel):
    """Permission state for a single hosted tool on a project."""
    enabled: bool

class Mcp(BaseModel):
    """Permission state for a single hosted tool on a project."""
    enabled: bool

class WebSearch(BaseModel):
    """Permission state for a single hosted tool on a project."""
    enabled: bool

class ProjectHostedToolPermissions(BaseModel):
    """Represents hosted tool permissions for a project."""
    code_interpreter: CodeInterpreter
    file_search: FileSearch
    image_generation: ImageGeneration
    mcp: Mcp
    web_search: WebSearch
