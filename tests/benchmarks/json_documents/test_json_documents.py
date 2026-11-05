"""JSON benchmarks over documents dominated by one property of the input.

- `twitter`: real API output, partly non-ASCII
- `i18n_users`: text in eight scripts
- `catalog`: long prose fields
- `event_log`: short repeated keys and values
- `canada`: almost only floats
- `citm_catalog`: large, deeply nested object graph

Models are kept plain so that the cost is in handling the document. Each document is measured
with both `validate_json` and `from_json`.
"""

import json
from pathlib import Path
from typing import Literal

import pytest

from pydantic import BaseModel, TypeAdapter

from .vendored import DOCUMENTS, check_vendored_documents, load_vendored

_DATA_DIR = Path(__file__).parent / 'data'


# --------------------------------------------------------------------------------- documents


def _generated_bytes(name: str) -> bytes:
    """Return the generated document, refreshing the cached copy if it is stale."""
    from .generate_data import catalog, event_log, i18n_users

    generator = {'i18n_users': i18n_users, 'catalog': catalog, 'event_log': event_log}[name]
    # Keep non-ASCII text as UTF-8 rather than `\uXXXX` escapes.
    current = json.dumps(generator(), ensure_ascii=False).encode('utf-8')
    path = _DATA_DIR / f'{name}.json'
    if not path.exists() or path.read_bytes() != current:
        path.write_bytes(current)
    return current


@pytest.fixture(scope='module')
def twitter_data_bytes() -> bytes:
    return load_vendored('twitter')


@pytest.fixture(scope='module')
def canada_data_bytes() -> bytes:
    return load_vendored('canada')


@pytest.fixture(scope='module')
def citm_catalog_data_bytes() -> bytes:
    return load_vendored('citm_catalog')


@pytest.fixture(scope='module')
def i18n_users_data_bytes() -> bytes:
    return _generated_bytes('i18n_users')


@pytest.fixture(scope='module')
def catalog_data_bytes() -> bytes:
    return _generated_bytes('catalog')


@pytest.fixture(scope='module')
def event_log_data_bytes() -> bytes:
    return _generated_bytes('event_log')


def test_vendored_documents_match_upstream():
    assert check_vendored_documents() == []
    assert set(DOCUMENTS) == {'twitter', 'canada', 'citm_catalog'}


def test_generated_data_replaces_stale_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from . import generate_data

    cached = tmp_path / 'event_log.json'
    cached.write_bytes(b'[]')
    monkeypatch.setattr('tests.benchmarks.json_documents.test_json_documents._DATA_DIR', tmp_path)
    monkeypatch.setattr(generate_data, 'event_log', lambda: [{'event': 'changed'}])

    expected = b'[{"event": "changed"}]'
    assert _generated_bytes('event_log') == expected
    assert cached.read_bytes() == expected


# ----------------------------------------------------------------------------------- schemas


class TweetMetadata(BaseModel):
    result_type: str
    iso_language_code: str


class TweetUser(BaseModel):
    id: int
    id_str: str
    name: str
    screen_name: str
    location: str
    description: str | None = None
    url: str | None = None
    followers_count: int
    friends_count: int
    statuses_count: int
    created_at: str
    verified: bool
    lang: str | None = None


class Tweet(BaseModel):
    metadata: TweetMetadata
    created_at: str
    id: int
    id_str: str
    text: str
    source: str
    truncated: bool
    user: TweetUser
    retweet_count: int
    favorite_count: int
    favorited: bool
    retweeted: bool
    lang: str


class TweetSearchMetadata(BaseModel):
    completed_in: float
    max_id: int
    max_id_str: str
    query: str
    refresh_url: str
    count: int
    since_id: int
    since_id_str: str


class TwitterSearch(BaseModel):
    statuses: list[Tweet]
    search_metadata: TweetSearchMetadata


class Geometry(BaseModel):
    type: Literal['Polygon']
    coordinates: list[list[list[float]]]


class Feature(BaseModel):
    type: Literal['Feature']
    properties: dict[str, str]
    geometry: Geometry


class FeatureCollection(BaseModel):
    type: Literal['FeatureCollection']
    features: list[Feature]


class CitmEvent(BaseModel):
    description: str | None = None
    id: int
    logo: str | None = None
    name: str
    subTopicIds: list[int]
    subjectCode: str | None = None
    subtitle: str | None = None
    topicIds: list[int]


class CitmPrice(BaseModel):
    amount: int
    audienceSubCategoryId: int
    seatCategoryId: int


class CitmArea(BaseModel):
    areaId: int
    blockIds: list[int]


class CitmSeatCategory(BaseModel):
    areas: list[CitmArea]
    seatCategoryId: int


class CitmPerformance(BaseModel):
    eventId: int
    id: int
    logo: str | None = None
    name: str | None = None
    prices: list[CitmPrice]
    seatCategories: list[CitmSeatCategory]
    seatMapImage: str | None = None
    start: int
    venueCode: str


class CitmCatalog(BaseModel):
    areaNames: dict[str, str]
    audienceSubCategoryNames: dict[str, str]
    blockNames: dict[str, str]
    events: dict[str, CitmEvent]
    performances: list[CitmPerformance]
    seatCategoryNames: dict[str, str]
    subTopicNames: dict[str, str]
    subjectNames: dict[str, str]
    topicNames: dict[str, str]
    topicSubTopics: dict[str, list[int]]
    venueNames: dict[str, str]


class I18nUser(BaseModel):
    id: int
    name: str
    email: str
    city: str
    bio: str
    locale: str
    tags: list[str]
    verified: bool
    score: float


class CatalogProduct(BaseModel):
    sku: str
    title: str
    description: str
    price: float
    in_stock: bool
    categories: list[str]


class LogEvent(BaseModel):
    event: str
    ts: str
    user_id: int
    session: str
    source: str
    ok: bool
    duration_ms: float
    props: dict[str, str]


@pytest.fixture(scope='module')
def twitter_adapter() -> TypeAdapter[TwitterSearch]:
    return TypeAdapter(TwitterSearch)


@pytest.fixture(scope='module')
def canada_adapter() -> TypeAdapter[FeatureCollection]:
    return TypeAdapter(FeatureCollection)


@pytest.fixture(scope='module')
def citm_catalog_adapter() -> TypeAdapter[CitmCatalog]:
    return TypeAdapter(CitmCatalog)


@pytest.fixture(scope='module')
def i18n_users_adapter() -> TypeAdapter[list[I18nUser]]:
    return TypeAdapter(list[I18nUser])


@pytest.fixture(scope='module')
def catalog_adapter() -> TypeAdapter[list[CatalogProduct]]:
    return TypeAdapter(list[CatalogProduct])


@pytest.fixture(scope='module')
def event_log_adapter() -> TypeAdapter[list[LogEvent]]:
    return TypeAdapter(list[LogEvent])


# -------------------------------------------------------------------------------- benchmarks


def test_twitter_validate_json(twitter_adapter, twitter_data_bytes, benchmark):
    benchmark(twitter_adapter.validate_json, twitter_data_bytes)


def test_twitter_from_json(twitter_data_bytes, benchmark):
    from pydantic_core import from_json

    benchmark(from_json, twitter_data_bytes)


def test_canada_validate_json(canada_adapter, canada_data_bytes, benchmark):
    benchmark(canada_adapter.validate_json, canada_data_bytes)


def test_canada_from_json(canada_data_bytes, benchmark):
    from pydantic_core import from_json

    benchmark(from_json, canada_data_bytes)


def test_citm_catalog_validate_json(citm_catalog_adapter, citm_catalog_data_bytes, benchmark):
    benchmark(citm_catalog_adapter.validate_json, citm_catalog_data_bytes)


def test_citm_catalog_from_json(citm_catalog_data_bytes, benchmark):
    from pydantic_core import from_json

    benchmark(from_json, citm_catalog_data_bytes)


def test_i18n_users_validate_json(i18n_users_adapter, i18n_users_data_bytes, benchmark):
    benchmark(i18n_users_adapter.validate_json, i18n_users_data_bytes)


def test_i18n_users_from_json(i18n_users_data_bytes, benchmark):
    from pydantic_core import from_json

    benchmark(from_json, i18n_users_data_bytes)


def test_catalog_validate_json(catalog_adapter, catalog_data_bytes, benchmark):
    benchmark(catalog_adapter.validate_json, catalog_data_bytes)


def test_catalog_from_json(catalog_data_bytes, benchmark):
    from pydantic_core import from_json

    benchmark(from_json, catalog_data_bytes)


def test_event_log_validate_json(event_log_adapter, event_log_data_bytes, benchmark):
    benchmark(event_log_adapter.validate_json, event_log_data_bytes)


def test_event_log_from_json(event_log_data_bytes, benchmark):
    from pydantic_core import from_json

    benchmark(from_json, event_log_data_bytes)
