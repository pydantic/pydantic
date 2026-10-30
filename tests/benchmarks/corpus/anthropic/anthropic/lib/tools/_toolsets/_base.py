
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from __future__ import annotations
from typing import Generic, TypeVar
from typing_extensions import Literal, TypeAlias
from ...._models import BaseModel, GenericModel
_NameT = TypeVar('_NameT', bound=str, covariant=True)
_InputT = TypeVar('_InputT', bound=BaseModel, covariant=True)

class BetaScreenshotResult(BaseModel):
    """A screenshot or zoom image from a browser or computer toolset, rendered as one image block. The image must
    already fit the model's image limits: the API rejects an oversized one rather than scaling it down."""
    data: str
    media_type: Literal['image/png', 'image/jpeg', 'image/gif', 'image/webp'] = 'image/png'
ResultKind: TypeAlias = Literal['navigate', 'screenshot', 'point', 'text', 'tab', 'tabs', 'none']

class Member(GenericModel, Generic[_NameT, _InputT]):
    """One member of a toolset: the model its `tool_use.input` is parsed into, its result kind, the confirmation the
    model reads after a pure action (`{field}` placeholders are filled from the input, `{ref}` reads the browser's
    `target.ref`, and a line the action returned follows it), and whether it is on by default."""
    name: _NameT
    input: type[_InputT]
    result: ResultKind
    text: str | None = None
    enabled_by_default: bool = True
