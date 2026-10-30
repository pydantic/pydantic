# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from .._models import BaseModel

class Skill(BaseModel):
    id: str
    created_at: int
    default_version: str
    description: str
    latest_version: str
    name: str
    object: Literal['skill']
