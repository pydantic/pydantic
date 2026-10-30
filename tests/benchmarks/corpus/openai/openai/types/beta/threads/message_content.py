# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Annotated, TypeAlias
from ...._utils import PropertyInfo
from .text_content_block import TextContentBlock
from .refusal_content_block import RefusalContentBlock
from .image_url_content_block import ImageURLContentBlock
from .image_file_content_block import ImageFileContentBlock
MessageContent: TypeAlias = Annotated[Union[ImageFileContentBlock, ImageURLContentBlock, TextContentBlock, RefusalContentBlock], PropertyInfo(discriminator='type')]
