import sys
from dataclasses import dataclass
from typing import Iterator, List
from uuid import UUID

import pytest
from annotated_types import GroupedMetadata
from typing_extensions import Annotated, Literal

from pydantic import UUID1, UUID3, UUID4, UUID5, BaseModel, PositiveInt, StrictStr

hypothesis = pytest.importorskip('hypothesis')
st = pytest.importorskip('hypothesis.strategies')
given = hypothesis.given


@pytest.mark.parametrize(
    'field_type',
    [
        int,
        float,
        str,
        bytes,
        list,
        tuple,
        # Decimal,
        pytest.param(List[int], id='List[int]'),
        pytest.param(StrictStr, id='StrictStr'),
        PositiveInt,
        # 'NegativeInt',
        # 'NonNegativeInt',
        # 'NonPositiveInt',
        # 'PositiveFloat',
        # 'NegativeFloat',
        # 'NonNegativeFloat',
        # 'NonPositiveFloat',
        # 'FiniteFloat',
        UUID1,
        UUID3,
        UUID4,
        UUID5,
        # 'FilePath',
        # 'DirectoryPath',
        # 'NewPath',
        # 'Json',
        # 'SecretStr',
        # 'SecretBytes',
        # 'StrictBool',
        # 'StrictBytes',
        # 'StrictInt',
        # 'StrictFloat',
        # 'PaymentCardNumber',
        # ByteSize,
        # PastDate,
        # 'FutureDate',
        # 'PastDatetime',
        # 'FutureDatetime',
        # 'AwareDatetime',
        # 'NaiveDatetime',
        # 'Base64Bytes',
        # 'Base64Str',
    ],
)
@given(data=st.data())
def test_can_construct(data, field_type):
    from hypothesis import strategies as st

    class Model(BaseModel):
        value: field_type

    instance = data.draw(st.from_type(Model))
    assert isinstance(instance, Model)


@given(data=st.data())
def test_hypothesis_uuid_version(data):
    from hypothesis import strategies as st

    value = data.draw(st.from_type(UUID1))

    assert isinstance(value, UUID)
    assert value.version == 1


@given(data=st.data())
def test_hypothesis_uuid_version_pure(data):
    from hypothesis import strategies as st

    @dataclass
    class UuidVersion(GroupedMetadata):
        uuid_version: Literal[1, 3, 4, 5]

        def __iter__(self) -> Iterator[object]:  # type: ignore
            if 'hypothesis' in sys.modules:
                from hypothesis import strategies as st

                yield st.uuids(version=self.uuid_version)

    value = data.draw(st.from_type(Annotated[UUID, UuidVersion(1)]))

    assert isinstance(value, UUID)
    assert value.version == 1
