script definitions that are based on the [ISO 15924](https://en.wikipedia.org/wiki/ISO_15924)

## ISO_15924

Bases: `str`

ISO_15924 parses script in the [ISO 15924](https://en.wikipedia.org/wiki/ISO_15924) format.

```py
from pydantic import BaseModel

from pydantic_extra_types.language_code import ISO_15924


class Script(BaseModel):
    alpha_4: ISO_15924


script = Script(alpha_4='Java')
print(lang)
# > script='Java'

```
