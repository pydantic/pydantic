import abc
import sys

import pytest

from pydantic import BaseModel


def test_model_subclassing_abstract_base_classes():
    class Model(BaseModel, abc.ABC):
        some_field: str


@pytest.mark.skipif(sys.version_info < (3, 12), reason='error value different on older versions')
def test_model_subclassing_abstract_base_classes_without_implementation_raises_exception():
    class Model(BaseModel, abc.ABC):
        some_field: str

        @abc.abstractmethod
        def my_abstract_method(self):
            pass

        @classmethod
        @abc.abstractmethod
        def my_abstract_classmethod(cls):
            pass

        @staticmethod
        @abc.abstractmethod
        def my_abstract_staticmethod():
            pass

        @property
        @abc.abstractmethod
        def my_abstract_property(self):
            pass

        @my_abstract_property.setter
        @abc.abstractmethod
        def my_abstract_property(self, val):
            pass

    with pytest.raises(TypeError) as excinfo:
        Model(some_field='some_value')
    assert str(excinfo.value) == (
        "Can't instantiate abstract class Model without an implementation for abstract methods "
        "'my_abstract_classmethod', 'my_abstract_method', 'my_abstract_property', 'my_abstract_staticmethod'"
    )
