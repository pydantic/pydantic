# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Union, Optional
from typing_extensions import Literal, TypeAlias
from ..._models import BaseModel

class TracingConfiguration(BaseModel):
    """Granular configuration for tracing."""
    group_id: Optional[str] = None
    metadata: Optional[object] = None
    workflow_name: Optional[str] = None
RealtimeTracingConfig: TypeAlias = Union[Literal['auto'], TracingConfiguration, None]
