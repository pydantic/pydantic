import json
import pickle
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from .types import StrBytes


class Protocol(str, Enum):
    json = 'json'
    pickle = 'pickle'


class UserProtocol:
    registered: List['UserProtocol'] = []

    def __init__(
        self,
        loader: Callable[[StrBytes], Any],
        proto_name: str,
        content_type_matcher: Optional[Callable[[str], bool]] = None,
        suffix_matcher: Optional[Callable[[str], bool]] = None,
    ):
        self.loader = loader
        self.proto_name = proto_name
        self.content_type_matcher = content_type_matcher
        self.suffix_matcher = suffix_matcher

    def content_match(self, content_type: Optional[str] = None) -> bool:
        if (self.content_type_matcher is None) or (content_type is None):
            return False
        return self.content_type_matcher(content_type)

    def suffix_match(self, suffix: str) -> bool:
        if self.suffix_matcher is None:
            return False
        return self.suffix_matcher(suffix)

    def load(self, b: StrBytes) -> Any:
        return self.loader(b)


def register_loader(
    loader: Callable[[StrBytes], Any],
    proto_name: str,
    content_type_matcher: Optional[Callable[[str], bool]] = None,
    suffix_matcher: Optional[Callable[[str], bool]] = None,
):
    """Register a loader for a particular protocol."""
    up = UserProtocol(loader, proto_name, content_type_matcher=content_type_matcher, suffix_matcher=suffix_matcher)
    UserProtocol.registered.append(up)


def load_str_bytes(
    b: StrBytes,
    *,
    content_type: str = None,
    encoding: str = 'utf8',
    proto: Union[Protocol, str, None] = None,
    allow_pickle: bool = False,
    json_loads: Callable[[str], Any] = json.loads,
) -> Any:
    if proto is None and content_type:
        if content_type.endswith(('json', 'javascript')):
            pass
        elif allow_pickle and content_type.endswith('pickle'):
            proto = Protocol.pickle
        else:
            for rp in UserProtocol.registered:
                if rp.content_match(content_type=content_type):
                    proto = rp.proto_name
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
        for rp in UserProtocol.registered:
            if proto == rp.proto_name:
                return rp.load(b)
        raise TypeError(f'Unknown protocol: {proto}')


def load_file(
    path: Union[str, Path],
    *,
    content_type: str = None,
    encoding: str = 'utf8',
    proto: Union[Protocol, str, None] = None,
    allow_pickle: bool = False,
    json_loads: Callable[[str], Any] = json.loads,
) -> Any:
    path = Path(path)
    b = path.read_bytes()
    if content_type is None:
        if path.suffix in ('.js', '.json'):
            proto = Protocol.json
        elif path.suffix == '.pkl':
            proto = Protocol.pickle
        else:
            for rp in UserProtocol.registered:
                if rp.suffix_match(suffix=path.suffix):
                    proto = rp.proto_name

    return load_str_bytes(
        b,
        proto=proto,
        content_type=content_type,
        encoding=encoding,
        allow_pickle=allow_pickle,
        json_loads=json_loads,
    )
