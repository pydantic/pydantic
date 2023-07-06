def schema(*, strict: bool = False) -> dict:
    class MyModel:
        # __slots__ is not required, but it avoids __pydantic_fields_set__ falling into __dict__
        __slots__ = '__dict__', '__pydantic_fields_set__', '__pydantic_extra__', '__pydantic_private__'

    def append_func(input_value, info):
        return f'{input_value} Changed'

    def wrap_function(input_value, validator, info):
        return f'Input {validator(input_value)} Changed'

    return {
        'type': 'model',
        'cls': MyModel,
        'config': {'strict': strict},
        'schema': {
            'type': 'model-fields',
            'fields': {
                'field_str': {'type': 'model-field', 'schema': {'type': 'str'}},
                'field_str_con': {
                    'type': 'model-field',
                    'schema': {'type': 'str', 'min_length': 3, 'max_length': 5, 'pattern': '^[a-z]+$'},
                },
                'field_int': {'type': 'model-field', 'schema': {'type': 'int'}},
                'field_int_con': {
                    'type': 'model-field',
                    'schema': {'type': 'int', 'gt': 1, 'lt': 10, 'multiple_of': 2},
                },
                'field_float': {'type': 'model-field', 'schema': {'type': 'float'}},
                'field_float_con': {
                    'type': 'model-field',
                    'schema': {'type': 'float', 'ge': 1.0, 'le': 10.0, 'multiple_of': 0.5},
                },
                'field_bool': {'type': 'model-field', 'schema': {'type': 'bool'}},
                'field_bytes': {'type': 'model-field', 'schema': {'type': 'bytes'}},
                'field_bytes_con': {
                    'type': 'model-field',
                    'schema': {'type': 'bytes', 'min_length': 6, 'max_length': 1000},
                },
                'field_date': {'type': 'model-field', 'schema': {'type': 'date'}},
                'field_date_con': {
                    'type': 'model-field',
                    'schema': {'type': 'date', 'ge': '2020-01-01', 'lt': '2020-01-02'},
                },
                'field_time': {'type': 'model-field', 'schema': {'type': 'time'}},
                'field_time_con': {
                    'type': 'model-field',
                    'schema': {'type': 'time', 'ge': '06:00:00', 'lt': '12:13:14'},
                },
                'field_datetime': {'type': 'model-field', 'schema': {'type': 'datetime'}},
                'field_datetime_con': {
                    'type': 'model-field',
                    'schema': {'type': 'datetime', 'ge': '2000-01-01T06:00:00', 'lt': '2020-01-02T12:13:14'},
                },
                'field_list_any': {'type': 'model-field', 'schema': {'type': 'list'}},
                'field_list_str': {'type': 'model-field', 'schema': {'type': 'list', 'items_schema': {'type': 'str'}}},
                'field_list_str_con': {
                    'type': 'model-field',
                    'schema': {'type': 'list', 'items_schema': {'type': 'str'}, 'min_length': 3, 'max_length': 42},
                },
                'field_set_any': {'type': 'model-field', 'schema': {'type': 'set'}},
                'field_set_int': {'type': 'model-field', 'schema': {'type': 'set', 'items_schema': {'type': 'int'}}},
                'field_set_int_con': {
                    'type': 'model-field',
                    'schema': {'type': 'set', 'items_schema': {'type': 'int'}, 'min_length': 3, 'max_length': 42},
                },
                'field_frozenset_any': {'type': 'model-field', 'schema': {'type': 'frozenset'}},
                'field_frozenset_bytes': {
                    'type': 'model-field',
                    'schema': {'type': 'frozenset', 'items_schema': {'type': 'bytes'}},
                },
                'field_frozenset_bytes_con': {
                    'type': 'model-field',
                    'schema': {
                        'type': 'frozenset',
                        'items_schema': {'type': 'bytes'},
                        'min_length': 3,
                        'max_length': 42,
                    },
                },
                'field_tuple_var_len_any': {'type': 'model-field', 'schema': {'type': 'tuple-variable'}},
                'field_tuple_var_len_float': {
                    'type': 'model-field',
                    'schema': {'type': 'tuple-variable', 'items_schema': {'type': 'float'}},
                },
                'field_tuple_var_len_float_con': {
                    'type': 'model-field',
                    'schema': {
                        'type': 'tuple-variable',
                        'items_schema': {'type': 'float'},
                        'min_length': 3,
                        'max_length': 42,
                    },
                },
                'field_tuple_fix_len': {
                    'type': 'model-field',
                    'schema': {
                        'type': 'tuple-positional',
                        'items_schema': [{'type': 'str'}, {'type': 'int'}, {'type': 'float'}, {'type': 'bool'}],
                    },
                },
                'field_dict_any': {'type': 'model-field', 'schema': {'type': 'dict'}},
                'field_dict_str_float': {
                    'type': 'model-field',
                    'schema': {'type': 'dict', 'keys_schema': {'type': 'str'}, 'values_schema': {'type': 'float'}},
                },
                'field_literal_1_int': {'type': 'model-field', 'schema': {'type': 'literal', 'expected': [1]}},
                'field_literal_1_str': {'type': 'model-field', 'schema': {'type': 'literal', 'expected': ['foobar']}},
                'field_literal_mult_int': {'type': 'model-field', 'schema': {'type': 'literal', 'expected': [1, 2, 3]}},
                'field_literal_mult_str': {
                    'type': 'model-field',
                    'schema': {'type': 'literal', 'expected': ['foo', 'bar', 'baz']},
                },
                'field_literal_assorted': {
                    'type': 'model-field',
                    'schema': {'type': 'literal', 'expected': [1, 'foo', True]},
                },
                'field_list_nullable_int': {
                    'type': 'model-field',
                    'schema': {'type': 'list', 'items_schema': {'type': 'nullable', 'schema': {'type': 'int'}}},
                },
                'field_union': {
                    'type': 'model-field',
                    'schema': {
                        'type': 'union',
                        'choices': [
                            {'type': 'str'},
                            {
                                'type': 'typed-dict',
                                'fields': {
                                    'field_str': {'type': 'typed-dict-field', 'schema': {'type': 'str'}},
                                    'field_int': {'type': 'typed-dict-field', 'schema': {'type': 'int'}},
                                    'field_float': {'type': 'typed-dict-field', 'schema': {'type': 'float'}},
                                },
                            },
                            {
                                'type': 'typed-dict',
                                'fields': {
                                    'field_float': {'type': 'typed-dict-field', 'schema': {'type': 'float'}},
                                    'field_bytes': {'type': 'typed-dict-field', 'schema': {'type': 'bytes'}},
                                    'field_date': {'type': 'typed-dict-field', 'schema': {'type': 'date'}},
                                },
                            },
                        ],
                    },
                },
                'field_functions_model': {
                    'type': 'model-field',
                    'schema': {
                        'type': 'typed-dict',
                        'fields': {
                            'field_before': {
                                'type': 'typed-dict-field',
                                'schema': {
                                    'type': 'function-before',
                                    'function': {'type': 'general', 'function': append_func},
                                    'schema': {'type': 'str'},
                                },
                            },
                            'field_after': {
                                'type': 'typed-dict-field',
                                'schema': {
                                    'type': 'function-after',
                                    'function': {'type': 'general', 'function': append_func},
                                    'schema': {'type': 'str'},
                                },
                            },
                            'field_wrap': {
                                'type': 'typed-dict-field',
                                'schema': {
                                    'type': 'function-wrap',
                                    'function': {'type': 'general', 'function': wrap_function},
                                    'schema': {'type': 'str'},
                                },
                            },
                            'field_plain': {
                                'type': 'typed-dict-field',
                                'schema': {
                                    'type': 'function-plain',
                                    'function': {'type': 'general', 'function': append_func},
                                },
                            },
                        },
                    },
                },
                'field_recursive': {
                    'type': 'model-field',
                    'schema': {
                        'ref': 'Branch',
                        'type': 'typed-dict',
                        'fields': {
                            'name': {'type': 'typed-dict-field', 'schema': {'type': 'str'}},
                            'sub_branch': {
                                'type': 'typed-dict-field',
                                'schema': {
                                    'type': 'default',
                                    'schema': {
                                        'type': 'nullable',
                                        'schema': {'type': 'definition-ref', 'schema_ref': 'Branch'},
                                    },
                                    'default': None,
                                },
                            },
                        },
                    },
                },
            },
        },
    }


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
