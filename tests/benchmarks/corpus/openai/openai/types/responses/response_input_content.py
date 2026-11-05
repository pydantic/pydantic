# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Annotated, TypeAlias
from ..._utils import PropertyInfo
from .response_input_file import ResponseInputFile
from .response_input_text import ResponseInputText
from .response_input_image import ResponseInputImage
ResponseInputContent: TypeAlias = Annotated[Union[ResponseInputText, ResponseInputImage, ResponseInputFile], PropertyInfo(discriminator='type')]
