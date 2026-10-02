"""Benchmarks over JSON documents chosen for what they are made of.

`test_north_star.py` gauges overall pydantic performance across many field types, and most of
its cost is in those types: only about a tenth of `test_north_star_validate_json` is the JSON
parse itself, the rest being UUID, `Decimal`, date/time and discriminated-union work. It is a
good instrument for what it measures and a poor one for everything else `validate_json` does.

These documents complement it along a different axis. Each is dominated by one property of the
*input* rather than by the schema, and the models are deliberately plain, so the cost lands in
handling the document rather than in the field types:

- `twitter`       real API output, 5.6% non-ASCII; the model reads a subset of the fields, as
                  application code does
- `i18n_users`    eight scripts, ~20% non-ASCII, the shape of a product with international users
- `catalog`       long prose fields, mostly ASCII with an accented minority
- `event_log`     short repeated keys and short ASCII values, the shape of log ingestion
- `canada`        GeoJSON, ~111k floats and almost nothing else
- `citm_catalog`  a large, deeply nested object graph of small models

Before this, no benchmark in the repository contained a single non-ASCII character, none had
long text fields, and none was dominated by floats.

`validate_json` and `from_json` are both measured for each: they take different paths, and a
change can move one without the other.
"""

import json
from pathlib import Path
from typing import Literal

import pytest

from pydantic import BaseModel, TypeAdapter

from .vendored_documents import DOCUMENTS, check_vendored_documents, load_vendored

_BENCHMARK_DIR = Path(__file__).parent


# --------------------------------------------------------------------------------- documents


def _generated_bytes(name: str) -> bytes:
    """Read a generated document, writing it first if this is the first run.

    `ensure_ascii=False` matters: with the default, non-ASCII text is written as `\\uXXXX`
    escapes, which take the escape path through the parser rather than the UTF-8 path, and the
    document stops measuring what it was chosen to measure. Real producers emit UTF-8.
    """
    path = _BENCHMARK_DIR / f'{name}_data.json'
    if not path.exists():
        from .generate_json_shape_data import catalog, event_log, i18n_users

        generator = {'i18n_users': i18n_users, 'catalog': catalog, 'event_log': event_log}[name]
        path.write_text(json.dumps(generator(), ensure_ascii=False), encoding='utf-8')
    return path.read_bytes()


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
    """The vendored documents are committed compressed, so nothing about them is readable in a
    diff. This pins what is actually in them to the hashes recorded in `vendored_documents`,
    which also records the URL each came from and can rebuild them byte for byte.
    """
    assert check_vendored_documents() == []
    assert set(DOCUMENTS) == {'twitter', 'canada', 'citm_catalog'}


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
