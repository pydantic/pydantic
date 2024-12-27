"""The descriptors module contains descriptor types used by pydantic."""

from abc import ABC, abstractmethod
from typing import Any

from pydantic_core import PydanticUndefined


class ModelFieldDescriptor(ABC):
    """A base class from which to derive any descriptor you want to use for a model field"""

    def __init__(self, /, default: Any = PydanticUndefined, field=None):
        from ._internal._import_utils import import_cached_field_info

        FieldInfo_ = import_cached_field_info()

        if not isinstance(field, FieldInfo_):
            raise RuntimeError('field must be of type FieldInfo')

        self.name = None
        self.field = field or FieldInfo_(default=default)

    @abstractmethod
    def __get__(self, instance, owner): ...

    @abstractmethod
    def __set__(self, instance, value): ...

    def __set_name__(self, owner, name):
        self.name = name
