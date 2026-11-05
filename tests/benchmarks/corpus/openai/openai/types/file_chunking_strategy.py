# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Annotated, TypeAlias
from .._utils import PropertyInfo
from .other_file_chunking_strategy_object import OtherFileChunkingStrategyObject
from .static_file_chunking_strategy_object import StaticFileChunkingStrategyObject
FileChunkingStrategy: TypeAlias = Annotated[Union[StaticFileChunkingStrategyObject, OtherFileChunkingStrategyObject], PropertyInfo(discriminator='type')]
