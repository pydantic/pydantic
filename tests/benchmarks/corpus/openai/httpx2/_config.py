# Modified HTTPX2 2.16.0 support types; see HTTPX2-LICENSE.
from __future__ import annotations
import dataclasses
from ._types import TimeoutTypes

class UnsetType:
    pass
UNSET = UnsetType()

@dataclasses.dataclass(init=False, repr=False)
class Timeout:
    connect: float | None
    read: float | None
    write: float | None
    pool: float | None

    def __init__(self, timeout: TimeoutTypes | UnsetType=UNSET, *, connect: None | float | UnsetType=UNSET, read: None | float | UnsetType=UNSET, write: None | float | UnsetType=UNSET, pool: None | float | UnsetType=UNSET) -> None:
        if isinstance(timeout, Timeout):
            assert connect is UNSET
            assert read is UNSET
            assert write is UNSET
            assert pool is UNSET
            self.connect = timeout.connect
            self.read = timeout.read
            self.write = timeout.write
            self.pool = timeout.pool
        elif isinstance(timeout, tuple):
            self.connect = timeout[0]
            self.read = timeout[1]
            self.write = None if len(timeout) < 3 else timeout[2]
            self.pool = None if len(timeout) < 4 else timeout[3]
        elif not (isinstance(connect, UnsetType) or isinstance(read, UnsetType) or isinstance(write, UnsetType) or isinstance(pool, UnsetType)):
            self.connect = connect
            self.read = read
            self.write = write
            self.pool = pool
        else:
            if isinstance(timeout, UnsetType):
                raise ValueError('httpx2.Timeout must either include a default, or set all four parameters explicitly.')
            self.connect = timeout if isinstance(connect, UnsetType) else connect
            self.read = timeout if isinstance(read, UnsetType) else read
            self.write = timeout if isinstance(write, UnsetType) else write
            self.pool = timeout if isinstance(pool, UnsetType) else pool

    def as_dict(self) -> dict[str, float | None]:
        return {'connect': self.connect, 'read': self.read, 'write': self.write, 'pool': self.pool}

    def __repr__(self) -> str:
        class_name = self.__class__.__name__
        if len({self.connect, self.read, self.write, self.pool}) == 1:
            return f'{class_name}(timeout={self.connect})'
        return f'{class_name}(connect={self.connect}, read={self.read}, write={self.write}, pool={self.pool})'
