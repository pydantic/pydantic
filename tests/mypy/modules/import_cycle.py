"""https://github.com/pydantic/pydantic/issues/11329."""

from .import_cycle_base import Base


class Sub(Base):
    side: float


Sub(side=1.0, name='x')
Sub(side=1.0, nam='x')
