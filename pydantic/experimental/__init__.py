"""__init__.py for the experimental submodule of pydantic."""

import warnings

from pydantic.warnings import PydanticExperimentalWarning

warnings.warn(
    'This module is experimental, its contents are subject to change and deprecation.',
    category=PydanticExperimentalWarning,
)
