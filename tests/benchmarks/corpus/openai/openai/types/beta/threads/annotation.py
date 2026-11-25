# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Annotated, TypeAlias
from ...._utils import PropertyInfo
from .file_path_annotation import FilePathAnnotation
from .file_citation_annotation import FileCitationAnnotation
Annotation: TypeAlias = Annotated[Union[FileCitationAnnotation, FilePathAnnotation], PropertyInfo(discriminator='type')]
