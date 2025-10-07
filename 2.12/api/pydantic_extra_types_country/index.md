Country definitions that are based on the [ISO 3166](https://en.wikipedia.org/wiki/List_of_ISO_3166_country_codes).

## CountryAlpha2

Bases: `str`

CountryAlpha2 parses country codes in the [ISO 3166-1 alpha-2](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2) format.

```py
from pydantic import BaseModel

from pydantic_extra_types.country import CountryAlpha2

class Product(BaseModel):
    made_in: CountryAlpha2

product = Product(made_in='ES')
print(product)
#> made_in='ES'

```

### alpha3

```python
alpha3: str

```

The country code in the [ISO 3166-1 alpha-3](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-3) format.

### numeric_code

```python
numeric_code: str

```

The country code in the [ISO 3166-1 numeric](https://en.wikipedia.org/wiki/ISO_3166-1_numeric) format.

### short_name

```python
short_name: str

```

The country short name.

## CountryAlpha3

Bases: `str`

CountryAlpha3 parses country codes in the [ISO 3166-1 alpha-3](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-3) format.

```py
from pydantic import BaseModel

from pydantic_extra_types.country import CountryAlpha3

class Product(BaseModel):
    made_in: CountryAlpha3

product = Product(made_in="USA")
print(product)
#> made_in='USA'

```

### alpha2

```python
alpha2: str

```

The country code in the [ISO 3166-1 alpha-2](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2) format.

### numeric_code

```python
numeric_code: str

```

The country code in the [ISO 3166-1 numeric](https://en.wikipedia.org/wiki/ISO_3166-1_numeric) format.

### short_name

```python
short_name: str

```

The country short name.

## CountryNumericCode

Bases: `str`

CountryNumericCode parses country codes in the [ISO 3166-1 numeric](https://en.wikipedia.org/wiki/ISO_3166-1_numeric) format.

```py
from pydantic import BaseModel

from pydantic_extra_types.country import CountryNumericCode

class Product(BaseModel):
    made_in: CountryNumericCode

product = Product(made_in="840")
print(product)
#> made_in='840'

```

### alpha2

```python
alpha2: str

```

The country code in the [ISO 3166-1 alpha-2](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2) format.

### alpha3

```python
alpha3: str

```

The country code in the [ISO 3166-1 alpha-3](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-3) format.

### short_name

```python
short_name: str

```

The country short name.

## CountryShortName

Bases: `str`

CountryShortName parses country codes in the short name format.

```py
from pydantic import BaseModel

from pydantic_extra_types.country import CountryShortName

class Product(BaseModel):
    made_in: CountryShortName

product = Product(made_in="United States")
print(product)
#> made_in='United States'

```

### alpha2

```python
alpha2: str

```

The country code in the [ISO 3166-1 alpha-2](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2) format.

### alpha3

```python
alpha3: str

```

The country code in the [ISO 3166-1 alpha-3](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-3) format.

### numeric_code

```python
numeric_code: str

```

The country code in the [ISO 3166-1 numeric](https://en.wikipedia.org/wiki/ISO_3166-1_numeric) format.
