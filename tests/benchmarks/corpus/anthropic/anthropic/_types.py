
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from __future__ import annotations
from typing import IO, Tuple, Union, Mapping, Optional, Sequence
from httpx2 import Timeout
Query = Mapping[str, object]
Body = object
AnyMapping = Mapping[str, object]
HttpxFileContent = Union[IO[bytes], bytes]
HttpxFileTypes = Union[HttpxFileContent, Tuple[Optional[str], HttpxFileContent], Tuple[Optional[str], HttpxFileContent, Optional[str]], Tuple[Optional[str], HttpxFileContent, Optional[str], Mapping[str, str]]]
HttpxRequestFiles = Union[Mapping[str, HttpxFileTypes], Sequence[Tuple[str, HttpxFileTypes]]]

class NotGiven:
    """
    For parameters with a meaningful None value, we need to distinguish between
    the user explicitly passing None, and the user not passing the parameter at
    all.

    User code shouldn't need to use not_given directly.

    For example:

    ```py
    def create(timeout: Timeout | None | NotGiven = not_given): ...


    create(timeout=1)  # 1s timeout
    create(timeout=None)  # No timeout
    create()  # Default timeout behavior
    ```
    """

class Omit:
    """
    To explicitly omit something from being sent in a request, use `omit`.

    ```py
    # as the default `Content-Type` header is `application/json` that will be sent
    client.post("/upload/files", files={"file": b"my raw file content"})

    # you can't explicitly override the header as it has to be dynamically generated
    # to look something like: 'multipart/form-data; boundary=0d8382fcf5f8c3be01ca2e11002d2983'
    client.post(..., headers={"Content-Type": "multipart/form-data"})

    # instead you can remove the default `application/json` header by passing omit
    client.post(..., headers={"Content-Type": omit})
    ```
    """
Headers = Mapping[str, Union[str, Omit]]
