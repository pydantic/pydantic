
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from __future__ import annotations
from typing_extensions import Literal, Required, TypedDict

class BetaBrowserStateChangeDownloadStartedParam(TypedDict, total=False):
    """A file download that started during this call."""
    download_id: Required[str]
    type: Required[Literal['download_started']]
    url: Required[str]
