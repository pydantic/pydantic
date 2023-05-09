import sys
from dataclasses import InitVar

import pytest

import pydantic.dataclasses
from pydantic import fields


def test_field_info_annotation_keyword_argument():
    """This tests that `FieldInfo.from_field` raises an error if passed the `annotation` kwarg.

    At the time of writing this test there is no way `FieldInfo.from_field` could receive the `annotation` kwarg from
    anywhere inside Pydantic code. However, it is possible that this API is still being in use by applications and
    third-party tools.
    """
    with pytest.raises(TypeError) as e:
        fields.FieldInfo.from_field(annotation=())

    assert e.value.args == ('"annotation" is not permitted as a Field keyword argument',)


@pytest.mark.skipif(sys.version_info >= (3, 8), reason='No error is thrown for `InitVar` for Python 3.8+')
def test_init_var_does_not_work():
    with pytest.raises(RuntimeError) as e:

        @pydantic.dataclasses.dataclass
        class Model:
            some_field: InitVar[str]

    assert e.value.args == ('InitVar is not supported in Python 3.7 as type information is lost',)
