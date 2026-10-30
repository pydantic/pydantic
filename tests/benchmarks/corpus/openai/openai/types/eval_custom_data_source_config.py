# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Dict
from typing_extensions import Literal
from pydantic import Field as FieldInfo
from .._models import BaseModel

class EvalCustomDataSourceConfig(BaseModel):
    """
    A CustomDataSourceConfig which specifies the schema of your `item` and optionally `sample` namespaces.
    The response schema defines the shape of the data that will be:
    - Used to define your testing criteria and
    - What data is required when creating a run
    """
    schema_: Dict[str, object] = FieldInfo(alias='schema')
    type: Literal['custom']
