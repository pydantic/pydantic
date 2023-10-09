import pickle
import re
from datetime import datetime, timedelta, timezone

import pytest

from pydantic_core import core_schema, validate_core_schema
from pydantic_core._pydantic_core import SchemaValidator, ValidationError


def test_basic_schema_validator():
    v = SchemaValidator(
        validate_core_schema(
            {'type': 'dict', 'strict': True, 'keys_schema': {'type': 'int'}, 'values_schema': {'type': 'int'}}
        )
    )
    v = pickle.loads(pickle.dumps(v))
    assert v.validate_python({'1': 2, '3': 4}) == {1: 2, 3: 4}
    assert v.validate_python({}) == {}
    with pytest.raises(ValidationError, match=re.escape('[type=dict_type, input_value=[], input_type=list]')):
        v.validate_python([])


def test_schema_validator_containing_config():
    """
    Verify that the config object is not lost during (de)serialization.
    """
    v = SchemaValidator(
        core_schema.model_fields_schema({'f': core_schema.model_field(core_schema.str_schema())}),
        config=core_schema.CoreConfig(extra_fields_behavior='allow'),
    )
    v = pickle.loads(pickle.dumps(v))

    m, model_extra, fields_set = v.validate_python({'f': 'x', 'extra_field': '123'})
    assert m == {'f': 'x'}
    # If the config was lost during (de)serialization, the below checks would fail as
    # the default behavior is to ignore extra fields.
    assert model_extra == {'extra_field': '123'}
    assert fields_set == {'f', 'extra_field'}

    v.validate_assignment(m, 'f', 'y')
    assert m == {'f': 'y'}


def test_schema_validator_tz_pickle() -> None:
    """
    https://github.com/pydantic/pydantic-core/issues/589
    """
    v = SchemaValidator(core_schema.datetime_schema())
    original = datetime(2022, 6, 8, 12, 13, 14, tzinfo=timezone(timedelta(hours=-12, minutes=-15)))
    validated = v.validate_python('2022-06-08T12:13:14-12:15')
    assert validated == original
    assert pickle.loads(pickle.dumps(validated)) == validated == original
