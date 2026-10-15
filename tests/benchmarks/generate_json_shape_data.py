"""Deterministic data for the benchmarks in `test_json_shapes.py`.

Each generator produces a document chosen for what it is *made of* — the proportion of
non-ASCII text, the length of its strings, the number of distinct keys — rather than for the
variety of field types it exercises, which is what `generate_north_star_data.py` covers.

Every generator reseeds before it runs, so the documents are byte-identical between runs and
independent of the order they are generated in.
"""

from typing import Any

from faker import Faker

# A product with a non-English user base does not get one script, it gets several.
LOCALES = ['ja_JP', 'ru_RU', 'de_DE', 'ko_KR', 'zh_CN', 'en_US', 'fr_FR', 'pl_PL']

_fakers = {locale: Faker(locale) for locale in LOCALES}
_en = _fakers['en_US']
_fr = _fakers['fr_FR']


def i18n_users(length: int = 1000) -> list[dict[str, Any]]:
    """User profiles in eight scripts: text that is ~20% non-ASCII once encoded."""
    Faker.seed(0)
    out = []
    for i in range(length):
        locale = LOCALES[i % len(LOCALES)]
        f = _fakers[locale]
        out.append(
            {
                'id': i,
                'name': f.name(),
                'email': f.email(),
                'city': f.city(),
                'bio': f.text(max_nb_chars=200),
                'locale': locale,
                'tags': [f.word() for _ in range(3)],
                'verified': i % 3 == 0,
                'score': round(i * 0.37 % 100, 3),
            }
        )
    return out


def catalog(length: int = 600) -> list[dict[str, Any]]:
    """A product catalogue: long, mostly-ASCII prose with an accented minority."""
    Faker.seed(0)
    out = []
    for i in range(length):
        # a realistic catalogue is not uniformly English
        description = (_fr if i % 4 == 0 else _en).text(max_nb_chars=1200)
        out.append(
            {
                'sku': f'SKU-{i:07d}',
                'title': _en.catch_phrase(),
                'description': description,
                'price': round(i * 3.21 % 999, 2),
                'in_stock': i % 5 != 0,
                'categories': [_en.word() for _ in range(4)],
            }
        )
    return out


def event_log(length: int = 1000) -> list[dict[str, Any]]:
    """Analytics events: short repeated keys and short repeated ASCII values."""
    Faker.seed(0)
    names = ['page_view', 'click', 'purchase', 'signup', 'error', 'scroll']
    sources = ['web', 'ios', 'android', 'api']
    return [
        {
            'event': names[i % len(names)],
            'ts': f'2026-09-{i % 28 + 1:02d}T{i % 24:02d}:00:00Z',
            'user_id': i % 500,
            'session': f'sess_{i % 250:06x}',
            'source': sources[i % len(sources)],
            'ok': i % 7 != 0,
            'duration_ms': round(i * 1.7 % 5000, 2),
            'props': {'ref': sources[i % 4], 'plan': 'pro' if i % 2 else 'free'},
        }
        for i in range(length)
    ]
