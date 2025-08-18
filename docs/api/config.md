::: pydantic.config
    options:
      group_by_category: false
      members:
        - ConfigDict
        - with_config
        - ExtraValues
        - BaseConfig

::: pydantic.alias_generators
    options:
      show_root_heading: true
## Example

You can use `populate_by_name=True` (deprecated) to populate a field either by its alias or by its field name.

```python
from pydantic import BaseModel, ConfigDict, Field

class Model(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    my_field: str = Field(alias='my_alias')

m = Model(my_alias='foo')
print(m)
#> my_field='foo'

m = Model(my_field='foo')
print(m)
#> my_field='foo'
```
