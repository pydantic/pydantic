"""
An integration-style benchmark of a model with a class of what should
(hopefully) be some of the most common field types used in pydantic validation.

Used to gauge overall pydantic performance.
"""
import json
from datetime import date, datetime, time
from decimal import Decimal
from pathlib import Path
from typing import List, Union
from uuid import UUID

import pytest
from typing_extensions import Annotated, Literal


@pytest.fixture(scope='module')
def pydantic_type_adapter():
    from pydantic import BaseModel, Field, TypeAdapter
    from pydantic.networks import AnyHttpUrl

    class Blog(BaseModel):
        type: Literal['blog']
        title: str
        post_count: int
        readers: int
        avg_post_rating: float
        url: AnyHttpUrl

    class SocialProfileBase(BaseModel):
        type: Literal['profile']
        network: Literal['facebook', 'twitter', 'linkedin']
        username: str
        join_date: date

    class FacebookProfile(SocialProfileBase):
        network: Literal['facebook']
        friends: int

    class TwitterProfile(SocialProfileBase):
        network: Literal['twitter']
        followers: int

    class LinkedinProfile(SocialProfileBase):
        network: Literal['linkedin']
        connections: Annotated[int, Field(le=500)]

    SocialProfile = Annotated[Union[FacebookProfile, TwitterProfile, LinkedinProfile], Field(discriminator='network')]

    Website = Annotated[Union[Blog, SocialProfile], Field(discriminator='type')]

    class Person(BaseModel):
        id: UUID
        name: str
        height: Decimal
        entry_created_date: date
        entry_created_time: time
        entry_updated_at: datetime
        websites: List[Website] = Field(default_factory=list)

    return TypeAdapter(List[Person])


_NORTH_STAR_DATA_PATH = Path(__file__).parent / 'north_star_data.json'


@pytest.fixture(scope='module')
def north_star_data_bytes():
    return _north_star_data_bytes()


def _north_star_data_bytes() -> bytes:
    from .generate_north_star_data import person_data

    needs_generating = not _NORTH_STAR_DATA_PATH.exists()
    if needs_generating:
        data = json.dumps(person_data(length=1000)).encode()
        _NORTH_STAR_DATA_PATH.write_bytes(data)
    else:
        data = _NORTH_STAR_DATA_PATH.read_bytes()

    return data


def test_north_star_validate_json(pydantic_type_adapter, north_star_data_bytes, benchmark):
    benchmark(pydantic_type_adapter.validate_json, north_star_data_bytes)


def test_north_star_validate_json_strict(pydantic_type_adapter, north_star_data_bytes, benchmark):
    coerced_north_star_data = pydantic_type_adapter.dump_json(
        pydantic_type_adapter.validate_json(north_star_data_bytes)
    )
    benchmark(pydantic_type_adapter.validate_json, coerced_north_star_data, strict=True)


def test_north_star_dump_json(pydantic_type_adapter, north_star_data_bytes, benchmark):
    parsed = pydantic_type_adapter.validate_json(north_star_data_bytes)
    benchmark(pydantic_type_adapter.dump_json, parsed)


def test_north_star_validate_python(pydantic_type_adapter, north_star_data_bytes, benchmark):
    benchmark(pydantic_type_adapter.validate_python, json.loads(north_star_data_bytes))


def test_north_star_validate_python_strict(pydantic_type_adapter, north_star_data_bytes, benchmark):
    coerced_north_star_data = pydantic_type_adapter.dump_python(
        pydantic_type_adapter.validate_json(north_star_data_bytes)
    )
    benchmark(pydantic_type_adapter.validate_python, coerced_north_star_data, strict=True)


def test_north_star_dump_python(pydantic_type_adapter, north_star_data_bytes, benchmark):
    parsed = pydantic_type_adapter.validate_python(json.loads(north_star_data_bytes))
    benchmark(pydantic_type_adapter.dump_python, parsed)


def test_north_star_json_loads(north_star_data_bytes, benchmark):
    benchmark(json.loads, north_star_data_bytes)


def test_north_star_json_dumps(north_star_data_bytes, benchmark):
    parsed = json.loads(north_star_data_bytes)
    benchmark(json.dumps, parsed)
