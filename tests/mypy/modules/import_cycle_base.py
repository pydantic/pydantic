"""Helper module for the `import_cycle.py` test module.

`Base` has a field referencing `Sub`, defined in `import_cycle.py`, thus creating an import cycle.
This results in the mypy plugin deferring the processing of `Base` (as `Sub` isn't yet resolved),
possibly after `Sub` (a subclass of `Base`) has already been processed.
"""

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
    from .import_cycle import Sub


# This base is required to make the issue reproducible (as without it, it adds `**kwargs`)
# to the `__init__()` signature:
class ForbidExtraBase(BaseModel):
    model_config = ConfigDict(extra='forbid')


class Base(ForbidExtraBase):
    name: str | None = None
    parent: 'Sub | None' = None
