def schema(*, strict: bool = False) -> dict:
    class MyModel:
        # __slots__ is not required, but it avoids __fields_set__ falling into __dict__
        __slots__ = '__dict__', '__fields_set__'

    def append_func(input_value, **kwargs):
        return f'{input_value} Changed'

    def wrap_function(input_value, *, validator, **kwargs):
        return f'Input {validator(input_value)} Changed'

    return {
        'type': 'model',
        'cls': MyModel,
        'config': {'strict': strict},
        'schema': {
            'type': 'typed-dict',
            'return_fields_set': True,
            'fields': {
                'field_str': {'schema': {'type': 'str'}},
                'field_str_con': {'schema': {'type': 'str', 'min_length': 3, 'max_length': 5, 'pattern': '^[a-z]+$'}},
                'field_int': {'schema': {'type': 'int'}},
                'field_int_con': {'schema': {'type': 'int', 'gt': 1, 'lt': 10, 'multiple_of': 2}},
                'field_float': {'schema': {'type': 'float'}},
                'field_float_con': {'schema': {'type': 'float', 'ge': 1.0, 'le': 10.0, 'multiple_of': 0.5}},
                'field_bool': {'schema': {'type': 'bool'}},
                'field_bytes': {'schema': {'type': 'bytes'}},
                'field_bytes_con': {'schema': {'type': 'bytes', 'min_length': 6, 'max_length': 1000}},
                'field_date': {'schema': {'type': 'date'}},
                'field_date_con': {'schema': {'type': 'date', 'ge': '2020-01-01', 'lt': '2020-01-02'}},
                'field_time': {'schema': {'type': 'time'}},
                'field_time_con': {'schema': {'type': 'time', 'ge': '06:00:00', 'lt': '12:13:14'}},
                'field_datetime': {'schema': {'type': 'datetime'}},
                'field_datetime_con': {
                    'schema': {'type': 'datetime', 'ge': '2000-01-01T06:00:00', 'lt': '2020-01-02T12:13:14'}
                },
                'field_list_any': {'schema': {'type': 'list'}},
                'field_list_str': {'schema': {'type': 'list', 'items_schema': {'type': 'str'}}},
                'field_list_str_con': {
                    'schema': {'type': 'list', 'items_schema': {'type': 'str'}, 'min_length': 3, 'max_length': 42}
                },
                'field_set_any': {'schema': {'type': 'set'}},
                'field_set_int': {'schema': {'type': 'set', 'items_schema': {'type': 'int'}}},
                'field_set_int_con': {
                    'schema': {'type': 'set', 'items_schema': {'type': 'int'}, 'min_length': 3, 'max_length': 42}
                },
                'field_frozenset_any': {'schema': {'type': 'frozenset'}},
                'field_frozenset_bytes': {'schema': {'type': 'frozenset', 'items_schema': {'type': 'bytes'}}},
                'field_frozenset_bytes_con': {
                    'schema': {
                        'type': 'frozenset',
                        'items_schema': {'type': 'bytes'},
                        'min_length': 3,
                        'max_length': 42,
                    }
                },
                'field_tuple_var_len_any': {'schema': {'type': 'tuple'}},
                'field_tuple_var_len_float': {'schema': {'type': 'tuple', 'items_schema': {'type': 'float'}}},
                'field_tuple_var_len_float_con': {
                    'schema': {'type': 'tuple', 'items_schema': {'type': 'float'}, 'min_length': 3, 'max_length': 42}
                },
                'field_tuple_fix_len': {
                    'schema': {
                        'type': 'tuple',
                        'mode': 'positional',
                        'items_schema': [{'type': 'str'}, {'type': 'int'}, {'type': 'float'}, {'type': 'bool'}],
                    }
                },
                'field_dict_any': {'schema': {'type': 'dict'}},
                'field_dict_str_float': {
                    'schema': {'type': 'dict', 'keys_schema': {'type': 'str'}, 'values_schema': {'type': 'float'}}
                },
                'field_literal_1_int': {'schema': {'type': 'literal', 'expected': [1]}},
                'field_literal_1_str': {'schema': {'type': 'literal', 'expected': ['foobar']}},
                'field_literal_mult_int': {'schema': {'type': 'literal', 'expected': [1, 2, 3]}},
                'field_literal_mult_str': {'schema': {'type': 'literal', 'expected': ['foo', 'bar', 'baz']}},
                'field_literal_assorted': {'schema': {'type': 'literal', 'expected': [1, 'foo', True]}},
                'field_list_nullable_int': {
                    'schema': {'type': 'list', 'items_schema': {'type': 'nullable', 'schema': {'type': 'int'}}}
                },
                'field_union': {
                    'schema': {
                        'type': 'union',
                        'choices': [
                            {'type': 'str'},
                            {
                                'type': 'typed-dict',
                                'fields': {
                                    'field_str': {'schema': {'type': 'str'}},
                                    'field_int': {'schema': {'type': 'int'}},
                                    'field_float': {'schema': {'type': 'float'}},
                                },
                            },
                            {
                                'type': 'typed-dict',
                                'fields': {
                                    'field_float': {'schema': {'type': 'float'}},
                                    'field_bytes': {'schema': {'type': 'bytes'}},
                                    'field_date': {'schema': {'type': 'date'}},
                                },
                            },
                        ],
                    }
                },
                'field_functions_model': {
                    'schema': {
                        'type': 'typed-dict',
                        'fields': {
                            'field_before': {
                                'schema': {
                                    'type': 'function',
                                    'mode': 'before',
                                    'function': append_func,
                                    'schema': {'type': 'str'},
                                }
                            },
                            'field_after': {
                                'schema': {
                                    'type': 'function',
                                    'mode': 'after',
                                    'function': append_func,
                                    'schema': {'type': 'str'},
                                }
                            },
                            'field_wrap': {
                                'schema': {
                                    'type': 'function',
                                    'mode': 'wrap',
                                    'function': wrap_function,
                                    'schema': {'type': 'str'},
                                }
                            },
                            'field_plain': {'schema': {'type': 'function', 'mode': 'plain', 'function': append_func}},
                        },
                    }
                },
                'field_recursive': {
                    'schema': {
                        'ref': 'Branch',
                        'type': 'typed-dict',
                        'fields': {
                            'name': {'schema': {'type': 'str'}},
                            'sub_branch': {
                                'schema': {
                                    'type': 'default',
                                    'schema': {
                                        'type': 'nullable',
                                        'schema': {'type': 'definition-ref', 'schema_ref': 'Branch'},
                                    },
                                    'default': None,
                                }
                            },
                        },
                    }
                },
            },
        },
    }


def pydantic_model():
    from datetime import date, datetime, time
    from typing import Any, Literal, Union

    try:
        from pydantic import BaseModel, conbytes, confloat, confrozenset, conint, conlist, conset, constr, validator
    except ImportError:
        return None

    class UnionModel1(BaseModel):
        field_str: str
        field_int: int
        field_float: float

    class UnionModel2(BaseModel):
        field_float: float
        field_bytes: bytes
        field_date: date

    class FunctionModel(BaseModel):
        field_before: str
        field_after: str
        field_wrap: str
        field_plain: Any

        @validator('field_before', pre=True, allow_reuse=True)
        def append_before(cls, v):
            return f'{v} Changed'

        @validator('field_after', 'field_wrap', 'field_plain', allow_reuse=True)  # best attempts at wrap and plain
        def append_after(cls, v):
            return f'{v} Changed'

        @validator('field_wrap', pre=True, allow_reuse=True)  # other part of wrap
        def wrap_before(cls, v):
            return f'Input {v}'

    class BranchModel(BaseModel):
        name: str
        sub_branch: 'BranchModel' = None

    class Model(BaseModel):
        field_str: str
        field_str_con: constr(min_length=3, max_length=5, regex='^[a-z]+$')  # noqa F722
        field_int: int
        field_int_con: conint(gt=1, lt=10, multiple_of=2)
        field_float: float
        field_float_con: confloat(ge=1.0, le=10.0, multiple_of=0.5)
        field_bool: bool
        field_bytes: bytes
        field_bytes_con: conbytes(min_length=6, max_length=1000)
        field_date: date
        field_date_con: date  # todo ge='2020-01-01', lt='2020-01-02'
        field_time: time
        field_time_con: time  # todo ge='06:00:00', lt='12:13:14'
        field_datetime: datetime
        field_datetime_con: datetime  # todo ge='2000-01-01T06:00:00', lt='2020-01-02T12:13:14'
        field_list_any: list
        field_list_str: list[str]
        field_list_str_con: conlist(str, min_items=3, max_items=42)
        field_set_any: set
        field_set_int: set[int]
        field_set_int_con: conset(int, min_items=3, max_items=42)
        field_frozenset_any: frozenset
        field_frozenset_bytes: frozenset[bytes]
        field_frozenset_bytes_con: confrozenset(bytes, min_items=3, max_items=42)
        field_tuple_var_len_any: tuple[Any, ...]
        field_tuple_var_len_float: tuple[float, ...]
        field_tuple_var_len_float_con: tuple[float, ...]  # todo min_items=3, max_items=42
        field_tuple_fix_len: tuple[str, int, float, bool]
        field_dict_any: dict
        field_dict_str_float: dict[str, float]
        field_literal_1_int: Literal[1]
        field_literal_1_str: Literal['foobar']
        field_literal_mult_int: Literal[1, 2, 3]
        field_literal_mult_str: Literal['foo', 'bar', 'baz']
        field_literal_assorted: Literal[1, 'foo', True]
        field_list_nullable_int: list[int | None]
        field_union: Union[str, UnionModel1, UnionModel2]
        field_functions_model: FunctionModel
        field_recursive: BranchModel

    return Model


def input_data_lax():
    return {
        'field_str': 'fo',
        'field_str_con': 'fooba',
        'field_int': 1,
        'field_int_con': 8,
        'field_float': 1.0,
        'field_float_con': 10.0,
        'field_bool': True,
        'field_bytes': b'foobar',
        'field_bytes_con': b'foobar',
        'field_date': '2010-02-03',
        'field_date_con': '2020-01-01',
        'field_time': '12:00:00',
        'field_time_con': '12:00:00',
        'field_datetime': '2020-01-01T12:13:14',
        'field_datetime_con': '2020-01-01T00:00:00',
        'field_list_any': ['a', b'b', True, 1.0, None] * 10,
        'field_list_str': ['a', 'b', 'c'] * 10,
        'field_list_str_con': ['a', 'b', 'c'] * 10,
        'field_set_any': {'a', b'b', True, 1.0, None},
        'field_set_int': set(range(100)),
        'field_set_int_con': set(range(42)),
        'field_frozenset_any': frozenset({'a', b'b', True, 1.0, None}),
        'field_frozenset_bytes': frozenset([f'{i}'.encode() for i in range(100)]),
        'field_frozenset_bytes_con': frozenset([f'{i}'.encode() for i in range(42)]),
        'field_tuple_var_len_any': ('a', b'b', True, 1.0, None),
        'field_tuple_var_len_float': tuple((i + 0.5 for i in range(100))),
        'field_tuple_var_len_float_con': tuple((i + 0.5 for i in range(42))),
        'field_tuple_fix_len': ('a', 1, 1.0, True),
        'field_dict_any': {'a': 'b', 1: True, 1.0: 1.0},
        'field_dict_str_float': {f'{i}': i + 0.5 for i in range(100)},
        'field_literal_1_int': 1,
        'field_literal_1_str': 'foobar',
        'field_literal_mult_int': 3,
        'field_literal_mult_str': 'foo',
        'field_literal_assorted': 'foo',
        'field_list_nullable_int': [1, None, 2, None, 3, None, 4, None],
        'field_union': {'field_str': 'foo', 'field_int': 1, 'field_float': 1.0},
        'field_functions_model': {
            'field_before': 'foo',
            'field_after': 'foo',
            'field_wrap': 'foo',
            'field_plain': 'foo',
        },
        'field_recursive': {
            'name': 'foo',
            'sub_branch': {'name': 'bar', 'sub_branch': {'name': 'baz', 'sub_branch': None}},
        },
    }


def input_data_strict():
    from datetime import date, datetime, time

    input_data = input_data_lax()
    input_data.update(
        field_date=date(2010, 2, 3),
        field_date_con=date(2020, 1, 1),
        field_time=time(12, 0, 0),
        field_time_con=time(12, 0, 0),
        field_datetime=datetime(2020, 1, 1, 12, 13, 14),
        field_datetime_con=datetime(2020, 1, 1),
    )
    return input_data


def input_data_wrong():
    return {
        'field_str': ['fo'],
        'field_str_con': 'f',
        'field_int': 1.5,
        'field_int_con': 11,
        'field_float': False,
        'field_float_con': 10.1,
        'field_bool': 4,
        'field_bytes': 42,
        'field_bytes_con': b'foo',
        'field_date': 'wrong',
        'field_date_con': '2000-01-01',
        'field_time': 'boom',
        'field_time_con': '23:00:00',
        'field_datetime': b'smash',
        'field_datetime_con': '1900-01-01T00:00:00',
        'field_list_any': {1: 2, 3: 4},
        'field_list_str': [(i,) for i in range(100)],
        'field_list_str_con': ['a', 'b'],
        'field_set_any': {'a': b'b', True: 1.0, None: 5},
        'field_set_int': {f'x{i}' for i in range(100)},
        'field_set_int_con': {i for i in range(40)},
        'field_frozenset_any': 'wrong',
        'field_frozenset_bytes': frozenset([i for i in range(100)]),
        'field_frozenset_bytes_con': frozenset({b'a', b'b'}),
        'field_tuple_var_len_any': b'wrong',
        'field_tuple_var_len_float': tuple(f'x{i}' for i in range(100)),
        'field_tuple_var_len_float_con': (1.0, 2.0),
        'field_tuple_fix_len': ('a', 1, 1.0, True, 'more'),
        'field_dict_any': {'a', 'b', 1, True, 1.0, 2.0},
        'field_dict_str_float': {(i,): f'x{i}' for i in range(100)},
        'field_literal_1_int': 2,
        'field_literal_1_str': 'bat',
        'field_literal_mult_int': 42,
        'field_literal_mult_str': 'wrong',
        'field_literal_assorted': 'wrong',
        'field_list_nullable_int': [f'x{i}' for i in range(100)],
        'field_union': {'field_str': ('foo',), 'field_int': 'x', 'field_float': b'y'},
        'field_functions_model': {'field_before': 1, 'field_after': 1, 'field_wrap': 1, 'field_plain': 1},
        'field_recursive': {'name': 'foo', 'sub_branch': {'name': 'bar', 'sub_branch': {}}},
    }
