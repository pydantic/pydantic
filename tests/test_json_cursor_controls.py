"""Control signals from incomplete containers must not hide invalid JSON."""

from typing import Annotated, Any

import pytest
from pydantic_core import PydanticUseDefault, SchemaValidator, core_schema

from pydantic import AfterValidator, ValidationError, create_model


def use_default(value: int | str) -> int | str:
    if value in (0, 'stop'):
        raise PydanticUseDefault
    return value


DefaultingInt = Annotated[int, AfterValidator(use_default)]
DefaultingKey = Annotated[str, AfterValidator(use_default)]


@pytest.mark.parametrize(
    'field_type,malformed,complete',
    [
        (list[DefaultingInt], '{"values":[0}', '{"values":[0,1]}'),
        (dict[str, DefaultingInt], '{"values":{"a":0}', '{"values":{"a":0,"b":1}}'),
        (dict[DefaultingKey, int], '{"values":{"stop":}', '{"values":{"stop":0,"other":1}}'),
    ],
)
def test_container_use_default_preserves_json_errors(field_type: Any, malformed: str, complete: str) -> None:
    model = create_model('Model', values=(field_type, ...))
    ordinary = SchemaValidator(core_schema.chain_schema([model.__pydantic_core_schema__, core_schema.any_schema()]))
    assert 'Chain' in repr(ordinary)
    with pytest.raises(ValidationError) as expected:
        ordinary.validate_json(malformed)
    assert expected.value.errors()[0]['type'] == 'json_invalid'
    with pytest.raises(ValidationError) as actual:
        model.model_validate_json(malformed)
    assert actual.value.json(include_url=False) == expected.value.json(include_url=False)
    # Fully formed JSON still follows the ordinary required-field/default policy.
    with pytest.raises(ValidationError) as expected_complete:
        ordinary.validate_json(complete)
    with pytest.raises(ValidationError) as actual_complete:
        model.model_validate_json(complete)
    assert actual_complete.value.json(include_url=False) == expected_complete.value.json(include_url=False)
