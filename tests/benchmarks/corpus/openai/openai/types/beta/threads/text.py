# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List
from ...._models import BaseModel
from .annotation import Annotation

class Text(BaseModel):
    annotations: List[Annotation]
    value: str
