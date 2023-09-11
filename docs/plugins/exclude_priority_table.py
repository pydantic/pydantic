from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from .utils import generate_table_heading, generate_table_row


def _no_wrap(s: str) -> str:
    open_nowrap_span: str = '<span style="white-space: nowrap;">'
    close_nowrap_span: str = '</span>'

    return f'{open_nowrap_span}{s}{close_nowrap_span}'


@dataclass
class ExcludeSetting:
    name: str
    value: Union[bool, set]
    md_str: Optional[str] = None

    @property
    def markdown_str(self) -> str:
        return self.md_str or f'{self.name}={self.value}'

    @property
    def kwargs_dict(self) -> Dict[str, Union[str, bool, set]]:
        return {} if self.name == 'not_specified' else {self.name: self.value}


field_exclude_settings: List[ExcludeSetting] = [
    ExcludeSetting(name='exclude', value=False),
    ExcludeSetting(name='exclude', value=True),
]
model_dump_exclude_overrides_settings: List[ExcludeSetting] = [
    ExcludeSetting(name='exclude', value={'name'}),
    ExcludeSetting(name='exclude', value={}),
    ExcludeSetting(name='include', value={'name'}),
    ExcludeSetting(name='include', value={}),
]
model_dump_exclude_variants_settings: List[ExcludeSetting] = [
    ExcludeSetting(name='not_specified', value={}, md_str='`<not specified>`'),  # special case
    ExcludeSetting(name='exclude_none', value=True),
    ExcludeSetting(name='exclude_defaults', value=True),
    ExcludeSetting(name='exclude_unset', value=True),
]


def build_exclude_priority_table(
    field_settings: List[ExcludeSetting],
    model_dump_settings: List[ExcludeSetting],
    constructor_kwargs: List[Dict[str, Any]],
) -> str:
    rows = []
    for kwargs_ in constructor_kwargs:
        for idx, model_dump_setting in enumerate(model_dump_settings):
            col_values = []
            for field_setting in field_settings:

                class Dog(BaseModel):
                    """Example class for explanation of `exclude` priority."""

                    name: Optional[str] = Field(default='Unspecified', **field_setting.kwargs_dict)

                my_dog = Dog(**kwargs_)
                result = my_dog.model_dump(**model_dump_setting.kwargs_dict)
                col_values.append(result)

            rows.append(
                generate_table_row(
                    col_values=[
                        _no_wrap(f'`{kwargs_}`') if idx == 0 else '',
                        _no_wrap(f'`{str(model_dump_setting.kwargs_dict)}`'),
                        *[_no_wrap(f'`{str(x)}`') for x in col_values],
                    ]
                )
            )

    table_heading = generate_table_heading(
        col_names=[
            '`init_kws`',
            '`model_dump_kws`',
            *[f'`model_dump` with {_no_wrap(f"`Field({x.markdown_str})`")}' for x in field_settings],
        ]
    )
    table = ''.join([table_heading, *rows])

    return table


exclude_overrides_table = build_exclude_priority_table(
    field_settings=field_exclude_settings,
    model_dump_settings=model_dump_exclude_overrides_settings,
    constructor_kwargs=[{'name': 'Ralph'}],
)
exclude_variants_table = build_exclude_priority_table(
    field_settings=field_exclude_settings,
    model_dump_settings=model_dump_exclude_variants_settings,
    constructor_kwargs=[{'name': 'Ralph'}, {'name': 'Unspecified'}, {'name': None}, {}],
)
