from dataclasses import dataclass
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field


@dataclass
class ExcludeSetting:
    name: str
    value: Union[bool, set]

    @property
    def markdown_str(self) -> str:
        return f'{self.name}={self.value}'

    @property
    def kwargs_dict(self) -> Dict[str, Union[str, bool, set]]:
        return {} if self.name == 'not_specified' else {self.name: self.value}


model_dump_exclude_variants_settings: List[ExcludeSetting] = [
    ExcludeSetting(name='exclude', value={'name'}),
    ExcludeSetting(name='include', value={}),
    ExcludeSetting(name='exclude_none', value=True),
    ExcludeSetting(name='exclude_defaults', value=True),
    ExcludeSetting(name='exclude_unset', value=True),
]


base_markdown = """
```py
from typing import Optional

from pydantic import BaseModel, Field

class Dog(BaseModel):
    name: Optional[str] = Field(default='Unspecified', exclude=False)

"""


class Dog(BaseModel):
    name: Optional[str] = Field(default='Unspecified', exclude=False)


def _build_exclude_example_markdown(exclude_setting: ExcludeSetting) -> str:
    modified_markdown = base_markdown
    for init_kws in [{'name': 'Ralph'}, {'name': 'Unspecified'}, {'name': None}, {}]:
        my_dog = Dog(**init_kws)

        modified_markdown += f'my_dog = Dog(**{init_kws})\n'
        modified_markdown += f'print(my_dog.model_dump({exclude_setting.markdown_str}))\n'
        modified_markdown += f'#> {my_dog.model_dump(**exclude_setting.kwargs_dict)}\n'

    modified_markdown += '```'

    return modified_markdown


exclude_variations_code_examples = {
    setting.name: _build_exclude_example_markdown(exclude_setting=setting)
    for setting in model_dump_exclude_variants_settings
}
