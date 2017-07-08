import logging
import pickle
from enum import IntEnum
from pathlib import Path
from typing import Any, Union

logger = logging.getLogger('pydantic')

from .types import StrBytes

try:
    import ujson as json
except ImportError:
    import json

try:
    import msgpack
except ImportError:
    msgpack = None


class Protocol(IntEnum):
    json = 1
    msgpack = 2
    pickle = 3


def load_str_bytes(b: StrBytes, *,
                   proto: Protocol=None,
                   content_type: str=None,
                   encoding: str='utf8',
                   allow_pickle: bool=False) -> Any:
    if proto is None and content_type:
        if content_type.endswith(('json', 'javascript')):
            pass
        elif content_type.endswith('msgpack'):
            proto = Protocol.msgpack
        elif content_type.endswith('pickle'):
            proto = Protocol.pickle
        else:
            logger.warning('content-type "%s" not recognized, trying json', content_type)

    proto = proto or Protocol.json

    if proto == Protocol.json:
        if isinstance(b, bytes):
            b = b.decode(encoding)
        return json.loads(b)
    elif proto == Protocol.msgpack:
        if msgpack is None:
            raise ImportError('Trying to decode with msgpack without msgpack installed, '
                              'run `pip install python-msgpack`')
        return msgpack.packb(b, encoding=encoding)
    elif proto == Protocol.pickle:
        if not allow_pickle:
            raise RuntimeError('Trying to decode with pickle with allow_pickle=False')
        return pickle.loads(b)
    else:
        raise ValueError('Unknown protocol: %s', proto)


def load_file(path: Union[str, Path], *,
              proto: Protocol=None,
              content_type: str=None,
              encoding: str='utf8',
              allow_pickle: bool=False) -> Any:
    path = Path(path)
    b = path.read_bytes()
    if content_type is None:
        if path.suffix in ('js', 'json'):
            proto = Protocol.json
        elif path.suffix in ('mp', 'msgpack'):
            proto = Protocol.msgpack
        elif path.suffix == 'pkl':
            proto = Protocol.pickle

    return load_str_bytes(b, proto=proto, encoding=encoding, allow_pickle=allow_pickle)
