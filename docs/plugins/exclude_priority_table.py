from dataclasses import dataclass
from typing import Any, Optional, Union

from pydantic import BaseModel, Field

from .utils import generate_table_heading, generate_table_row


@dataclass
class ExcludeSetting:
    name: str
    value: Union[bool, set]

    @property
    def markdown_str(self) -> str:
        return f'`{self.name}={self.value}`'

    @property
    def kwargs_dict(self) -> dict[str, Union[str, bool, set]]:
        return {self.name: self.value}


field_exclude_settings: list[ExcludeSetting] = [
    ExcludeSetting(name='exclude', value=True),
    ExcludeSetting(name='exclude', value=False),
]
model_dump_exclude_settings: list[ExcludeSetting] = [
    ExcludeSetting(name='exclude', value={'name'}),
    ExcludeSetting(name='exclude', value={}),
    ExcludeSetting(name='include', value={'name'}),
    ExcludeSetting(name='include', value={}),
]
model_dump_exclude_x_settings: list[ExcludeSetting] = [
    ExcludeSetting(name='exclude_none', value=True),
    ExcludeSetting(name='exclude_none', value=False),
    ExcludeSetting(name='exclude_defaults', value=True),
    ExcludeSetting(name='exclude_defaults', value=False),
    ExcludeSetting(name='exclude_unset', value=True),
    ExcludeSetting(name='exclude_unset', value=False),
]


def build_exclude_priority_table(
    field_settings: list[ExcludeSetting], model_dump_settings: list[ExcludeSetting], constructor_kwargs: dict[str, Any]
) -> str:
    rows = []
    for field_setting in field_settings:
        col_values = [field_setting.markdown_str]
        for model_dump_setting in model_dump_settings:

            class Dog(BaseModel):
                """Example class for explanation of `exclude` priority."""

                name: Optional[str] = Field(default=None, **field_setting.kwargs_dict)

            my_dog = Dog(**constructor_kwargs)
            result = my_dog.model_dump(**model_dump_setting.kwargs_dict)
            col_values.append(result)

        rows.append(generate_table_row(col_values=[f'`{x}`' for x in col_values]))

    table_heading = generate_table_heading(col_names=['Field Setting', *[x.markdown_str for x in model_dump_settings]])
    table = ''.join([table_heading, *rows])

    return table


exclude_table = build_exclude_priority_table(
    field_settings=field_exclude_settings,
    model_dump_settings=model_dump_exclude_settings,
    constructor_kwargs={'name': 'Ralph'},
)
exclude_x_table = build_exclude_priority_table(
    field_settings=field_exclude_settings, model_dump_settings=model_dump_exclude_x_settings, constructor_kwargs={}
)
