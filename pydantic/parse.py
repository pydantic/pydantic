import pickle
from enum import Enum
from pathlib import Path
from typing import Any, Union

from .types import StrBytes

try:
    import ujson as json
except ImportError:
    import json

try:
    import msgpack
except ImportError:
    msgpack = None


class Protocol(str, Enum):
    json = 'json'
    msgpack = 'msgpack'
    pickle = 'pickle'


def load_str_bytes(b: StrBytes, *,  # noqa: C901 (ignore complexity)
                   content_type: str=None,
                   encoding: str='utf8',
                   proto: Protocol=None,
                   allow_pickle: bool=False) -> Any:
    if proto is None and content_type:
        if content_type.endswith(('json', 'javascript')):
            pass
        elif msgpack and content_type.endswith('msgpack'):
            proto = Protocol.msgpack
        elif allow_pickle and content_type.endswith('pickle'):
            proto = Protocol.pickle
        else:
            raise TypeError(f'Unknown content-type: {content_type}')

    proto = proto or Protocol.json

    if proto == Protocol.json:
        if isinstance(b, bytes):
            b = b.decode(encoding)
        return json.loads(b)
    elif proto == Protocol.msgpack:
        if msgpack is None:
            raise ImportError("msgpack not installed, can't parse data")
        return msgpack.unpackb(b, encoding=encoding)
    elif proto == Protocol.pickle:
        if not allow_pickle:
            raise RuntimeError('Trying to decode with pickle with allow_pickle=False')
        return pickle.loads(b)
    else:
        raise TypeError(f'Unknown protocol: {proto}')


def load_file(path: Union[str, Path], *,
              content_type: str=None,
              encoding: str='utf8',
              proto: Protocol=None,
              allow_pickle: bool=False) -> Any:
    path = Path(path)
    b = path.read_bytes()
    if content_type is None:
        if path.suffix in ('.js', '.json'):
            proto = Protocol.json
        elif path.suffix in ('.mp', '.msgpack'):
            proto = Protocol.msgpack
        elif path.suffix == '.pkl':
            proto = Protocol.pickle

    return load_str_bytes(b, proto=proto, content_type=content_type, encoding=encoding, allow_pickle=allow_pickle)
