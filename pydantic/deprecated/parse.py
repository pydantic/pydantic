from __future__ import annotations

import json
import pickle
import warnings
from enum import Enum
from pathlib import Path
from typing import Any, Callable

from typing_extensions import deprecated


class Protocol(str, Enum):
    json = 'json'
    pickle = 'pickle'


@deprecated('load_str_bytes is deprecated.')
def load_str_bytes(
    b: str | bytes,
    *,
    content_type: str | None = None,
    encoding: str = 'utf8',
    proto: Protocol | None = None,
    allow_pickle: bool = False,
    json_loads: Callable[[str], Any] = json.loads,
) -> Any:
    warnings.warn('load_str_bytes is deprecated.', DeprecationWarning, stacklevel=2)
    if proto is None and content_type:
        if content_type.endswith(('json', 'javascript')):
            pass
        elif allow_pickle and content_type.endswith('pickle'):
            proto = Protocol.pickle
        else:
            raise TypeError(f'Unknown content-type: {content_type}')

    proto = proto or Protocol.json

    if proto == Protocol.json:
        if isinstance(b, bytes):
            b = b.decode(encoding)
        return json_loads(b)
    elif proto == Protocol.pickle:
        if not allow_pickle:
            raise RuntimeError('Trying to decode with pickle with allow_pickle=False')
        bb = b if isinstance(b, bytes) else b.encode()
        return pickle.loads(bb)
    else:
        raise TypeError(f'Unknown protocol: {proto}')


@deprecated('load_file is deprecated.')
def load_file(
    path: str | Path,
    *,
    content_type: str | None = None,
    encoding: str = 'utf8',
    proto: Protocol | None = None,
    allow_pickle: bool = False,
    json_loads: Callable[[str], Any] = json.loads,
) -> Any:
    warnings.warn('load_file is deprecated.', DeprecationWarning, stacklevel=2)
    path = Path(path)
    b = path.read_bytes()
    if content_type is None:
        if path.suffix in ('.js', '.json'):
            proto = Protocol.json
        elif path.suffix == '.pkl':
            proto = Protocol.pickle

    return load_str_bytes(
        b, proto=proto, content_type=content_type, encoding=encoding, allow_pickle=allow_pickle, json_loads=json_loads
    )
