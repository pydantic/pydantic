import json
import uuid
from uuid import UUID

import pytest

from pydantic import UUID1, UUID3, UUID4, UUID5, BaseModel, ConfigDict, Field, TypeAdapter, ValidationError


@pytest.mark.parametrize(
    'value,expected',
    [
        ('ebcdab58-6eb8-46fb-a190-d07a33e9eac8', UUID('ebcdab58-6eb8-46fb-a190-d07a33e9eac8')),
        (UUID('ebcdab58-6eb8-46fb-a190-d07a33e9eac8'), UUID('ebcdab58-6eb8-46fb-a190-d07a33e9eac8')),
        (b'ebcdab58-6eb8-46fb-a190-d07a33e9eac8', UUID('ebcdab58-6eb8-46fb-a190-d07a33e9eac8')),
        (b'\x12\x34\x56\x78' * 4, UUID('12345678-1234-5678-1234-567812345678')),
        ('ebcdab58-6eb8-46fb-a190-', ValidationError),
        (123, ValidationError),
    ],
)
def test_uuid_coercions(value, expected):
    class Model(BaseModel):
        v: UUID

    if expected is ValidationError:
        with pytest.raises(ValidationError):
            Model(v=value)
    else:
        assert Model(v=value).v == expected


def test_uuid_error():
    v = TypeAdapter(UUID)

    valid = UUID('49fdfa1d856d4003a83e4b9236532ec6')

    # sanity check
    assert v.validate_python(valid) == valid
    assert v.validate_python(valid.hex) == valid

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python('ebcdab58-6eb8-46fb-a190-d07a3')
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'loc': (),
            'msg': 'Input should be a valid UUID, invalid group length in group 4: expected 12, found 5',
            'input': 'ebcdab58-6eb8-46fb-a190-d07a3',
            'ctx': {'error': 'invalid group length in group 4: expected 12, found 5'},
            'type': 'uuid_parsing',
        }
    ]

    not_a_valid_input_type = object()
    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(not_a_valid_input_type)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'input': not_a_valid_input_type,
            'loc': (),
            'msg': 'UUID input should be a string, bytes or UUID object',
            'type': 'uuid_type',
        },
    ]

    with pytest.raises(ValidationError) as exc_info:
        v.validate_python(valid.hex, strict=True)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'is_instance_of',
            'loc': (),
            'msg': 'Input should be an instance of UUID',
            'input': '49fdfa1d856d4003a83e4b9236532ec6',
            'ctx': {'class': 'UUID'},
        }
    ]

    assert v.validate_json(json.dumps(valid.hex), strict=True) == valid


def test_uuid_json():
    class Model(BaseModel):
        v: UUID
        v1: UUID1
        v3: UUID3
        v4: UUID4

    m = Model(v=uuid.uuid4(), v1=uuid.uuid1(), v3=uuid.uuid3(uuid.NAMESPACE_DNS, 'python.org'), v4=uuid.uuid4())
    assert m.model_dump_json() == f'{{"v":"{m.v}","v1":"{m.v1}","v3":"{m.v3}","v4":"{m.v4}"}}'


def test_uuid_validation():
    class UUIDModel(BaseModel):
        a: UUID1
        b: UUID3
        c: UUID4
        d: UUID5
        e: UUID

    a = uuid.uuid1()
    b = uuid.uuid3(uuid.NAMESPACE_DNS, 'python.org')
    c = uuid.uuid4()
    d = uuid.uuid5(uuid.NAMESPACE_DNS, 'python.org')
    e = UUID('{00000000-7fff-4000-7fff-000000000000}')

    m = UUIDModel(a=a, b=b, c=c, d=d, e=e)
    assert m.model_dump() == {'a': a, 'b': b, 'c': c, 'd': d, 'e': e}

    with pytest.raises(ValidationError) as exc_info:
        UUIDModel(a=d, b=c, c=b, d=a, e=e)
    # insert_assert(exc_info.value.errors(include_url=False))
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'uuid_version',
            'loc': ('a',),
            'msg': 'UUID version 1 expected',
            'input': d,
            'ctx': {'expected_version': 1},
        },
        {
            'type': 'uuid_version',
            'loc': ('b',),
            'msg': 'UUID version 3 expected',
            'input': c,
            'ctx': {'expected_version': 3},
        },
        {
            'type': 'uuid_version',
            'loc': ('c',),
            'msg': 'UUID version 4 expected',
            'input': b,
            'ctx': {'expected_version': 4},
        },
        {
            'type': 'uuid_version',
            'loc': ('d',),
            'msg': 'UUID version 5 expected',
            'input': a,
            'ctx': {'expected_version': 5},
        },
    ]

    with pytest.raises(ValidationError) as exc_info:
        UUIDModel(a=e, b=e, c=e, d=e, e=e)
    assert exc_info.value.errors(include_url=False) == [
        {
            'type': 'uuid_version',
            'loc': ('a',),
            'msg': 'UUID version 1 expected',
            'input': e,
            'ctx': {'expected_version': 1},
        },
        {
            'type': 'uuid_version',
            'loc': ('b',),
            'msg': 'UUID version 3 expected',
            'input': e,
            'ctx': {'expected_version': 3},
        },
        {
            'type': 'uuid_version',
            'loc': ('c',),
            'msg': 'UUID version 4 expected',
            'input': e,
            'ctx': {'expected_version': 4},
        },
        {
            'type': 'uuid_version',
            'loc': ('d',),
            'msg': 'UUID version 5 expected',
            'input': e,
            'ctx': {'expected_version': 5},
        },
    ]


def test_uuid_strict() -> None:
    class StrictByConfig(BaseModel):
        a: UUID1
        b: UUID3
        c: UUID4
        d: UUID5
        e: uuid.UUID

        model_config = ConfigDict(strict=True)

    class StrictByField(BaseModel):
        a: UUID1 = Field(strict=True)
        b: UUID3 = Field(strict=True)
        c: UUID4 = Field(strict=True)
        d: UUID5 = Field(strict=True)
        e: uuid.UUID = Field(strict=True)

    a = uuid.UUID('7fb48116-ca6b-11ed-a439-3274d3adddac')  # uuid1
    b = uuid.UUID('6fa459ea-ee8a-3ca4-894e-db77e160355e')  # uuid3
    c = uuid.UUID('260d1600-3680-4f4f-a968-f6fa622ffd8d')  # uuid4
    d = uuid.UUID('886313e1-3b8a-5372-9b90-0c9aee199e5d')  # uuid5
    e = uuid.UUID('7fb48116-ca6b-11ed-a439-3274d3adddac')  # any uuid

    strict_errors = [
        {
            'type': 'is_instance_of',
            'loc': ('a',),
            'msg': 'Input should be an instance of UUID',
            'input': '7fb48116-ca6b-11ed-a439-3274d3adddac',
            'ctx': {'class': 'UUID'},
        },
        {
            'type': 'is_instance_of',
            'loc': ('b',),
            'msg': 'Input should be an instance of UUID',
            'input': '6fa459ea-ee8a-3ca4-894e-db77e160355e',
            'ctx': {'class': 'UUID'},
        },
        {
            'type': 'is_instance_of',
            'loc': ('c',),
            'msg': 'Input should be an instance of UUID',
            'input': '260d1600-3680-4f4f-a968-f6fa622ffd8d',
            'ctx': {'class': 'UUID'},
        },
        {
            'type': 'is_instance_of',
            'loc': ('d',),
            'msg': 'Input should be an instance of UUID',
            'input': '886313e1-3b8a-5372-9b90-0c9aee199e5d',
            'ctx': {'class': 'UUID'},
        },
        {
            'type': 'is_instance_of',
            'loc': ('e',),
            'msg': 'Input should be an instance of UUID',
            'input': '7fb48116-ca6b-11ed-a439-3274d3adddac',
            'ctx': {'class': 'UUID'},
        },
    ]

    for model in [StrictByConfig, StrictByField]:
        with pytest.raises(ValidationError) as exc_info:
            model(a=str(a), b=str(b), c=str(c), d=str(d), e=str(e))
        assert exc_info.value.errors(include_url=False) == strict_errors

        m = model(a=a, b=b, c=c, d=d, e=e)
        assert isinstance(m.a, type(a)) and m.a == a
        assert isinstance(m.b, type(b)) and m.b == b
        assert isinstance(m.c, type(c)) and m.c == c
        assert isinstance(m.d, type(d)) and m.d == d
        assert isinstance(m.e, type(e)) and m.e == e
