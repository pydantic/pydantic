# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Dict, Optional
from typing_extensions import Literal
from pydantic import Field as FieldInfo
from .._models import BaseModel
from .shared.metadata import Metadata

class EvalStoredCompletionsDataSourceConfig(BaseModel):
    """Deprecated in favor of LogsDataSourceConfig."""
    schema_: Dict[str, object] = FieldInfo(alias='schema')
    type: Literal['stored_completions']
    metadata: Optional[Metadata] = None
