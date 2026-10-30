# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Union
from typing_extensions import Annotated, TypeAlias
from ...._utils import PropertyInfo
from .file_path_delta_annotation import FilePathDeltaAnnotation
from .file_citation_delta_annotation import FileCitationDeltaAnnotation
AnnotationDelta: TypeAlias = Annotated[Union[FileCitationDeltaAnnotation, FilePathDeltaAnnotation], PropertyInfo(discriminator='type')]
