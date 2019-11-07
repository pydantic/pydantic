"""
Test mypy failure with dataclass.
"""
from typing import Optional

from pydantic.dataclasses import dataclass


class Config:
    validate_assignment = True


@dataclass(config=Config)
class AddProject:
    name: str
    slug: Optional[str]
    description: Optional[str]


p = AddProject(name='x', slug='y', description='z')
