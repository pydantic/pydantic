Language definitions that are based on the [ISO 639-3](https://en.wikipedia.org/wiki/ISO_639-3) & [ISO 639-5](https://en.wikipedia.org/wiki/ISO_639-5).

## LanguageInfo

```python
LanguageInfo(
    alpha2: Union[str, None], alpha3: str, name: str
)

```

LanguageInfo is a dataclass that contains the language information.

Parameters:

| Name | Type | Description | Default | | --- | --- | --- | --- | | `alpha2` | `Union[str, None]` | The language code in the ISO 639-1 alpha-2 format. | *required* | | `alpha3` | `str` | The language code in the ISO 639-3 alpha-3 format. | *required* | | `name` | `str` | The language name. | *required* |

## LanguageAlpha2

Bases: `str`

LanguageAlpha2 parses languages codes in the [ISO 639-1 alpha-2](https://en.wikipedia.org/wiki/ISO_639-1) format.

```py
from pydantic import BaseModel

from pydantic_extra_types.language_code import LanguageAlpha2


class Movie(BaseModel):
    audio_lang: LanguageAlpha2
    subtitles_lang: LanguageAlpha2


movie = Movie(audio_lang='de', subtitles_lang='fr')
print(movie)
# > audio_lang='de' subtitles_lang='fr'

```

### alpha3

```python
alpha3: str

```

The language code in the [ISO 639-3 alpha-3](https://en.wikipedia.org/wiki/ISO_639-3) format.

### name

```python
name: str

```

The language name.

## LanguageName

Bases: `str`

LanguageName parses languages names listed in the [ISO 639-3 standard](https://en.wikipedia.org/wiki/ISO_639-3) format.

```py
from pydantic import BaseModel

from pydantic_extra_types.language_code import LanguageName


class Movie(BaseModel):
    audio_lang: LanguageName
    subtitles_lang: LanguageName


movie = Movie(audio_lang='Dutch', subtitles_lang='Mandarin Chinese')
print(movie)
# > audio_lang='Dutch' subtitles_lang='Mandarin Chinese'

```

### alpha2

```python
alpha2: Union[str, None]

```

The language code in the [ISO 639-1 alpha-2](https://en.wikipedia.org/wiki/ISO_639-1) format. Does not exist for all languages.

### alpha3

```python
alpha3: str

```

The language code in the [ISO 639-3 alpha-3](https://en.wikipedia.org/wiki/ISO_639-3) format.

## ISO639_3

Bases: `str`

ISO639_3 parses Language in the [ISO 639-3 alpha-3](https://en.wikipedia.org/wiki/ISO_639-3_alpha-3) format.

```py
from pydantic import BaseModel

from pydantic_extra_types.language_code import ISO639_3


class Language(BaseModel):
    alpha_3: ISO639_3


lang = Language(alpha_3='ssr')
print(lang)
# > alpha_3='ssr'

```

## ISO639_5

Bases: `str`

ISO639_5 parses Language in the [ISO 639-5 alpha-3](https://en.wikipedia.org/wiki/ISO_639-5_alpha-3) format.

```py
from pydantic import BaseModel

from pydantic_extra_types.language_code import ISO639_5


class Language(BaseModel):
    alpha_3: ISO639_5


lang = Language(alpha_3='gem')
print(lang)
# > alpha_3='gem'

```
