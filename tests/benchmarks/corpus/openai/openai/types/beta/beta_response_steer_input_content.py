# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Annotated, TypeAlias
from ..._utils import PropertyInfo
from .beta_response_input_file_content import BetaResponseInputFileContent
from .beta_response_input_text_content import BetaResponseInputTextContent
from .beta_response_input_image_content import BetaResponseInputImageContent
BetaResponseSteerInputContent: TypeAlias = Annotated[Union[BetaResponseInputTextContent, BetaResponseInputImageContent, BetaResponseInputFileContent], PropertyInfo(discriminator='type')]
