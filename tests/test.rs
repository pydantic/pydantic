#[cfg(test)]
mod tests {
    use _pydantic_core::{SchemaSerializer, SchemaValidator, WarningsArg};
    use pyo3::ffi::c_str; // can switch to c"" literals on MSRV >= 1.77
    use pyo3::prelude::*;
    use pyo3::types::PyDict;

    #[test]
    fn test_build_schema_serializer() {
        Python::with_gil(|py| {
            // 'type': 'typed-dict',
            //     'fields': {
            //         'root': {
            //             'type': 'typed-dict-field',
            //             'schema': {
            //                 'type': 'definition-ref',
            //                 'schema_ref': 'C-ref',
            //             },
            //         },
            //     },
            //     'ref': 'C-ref',
            //     'serialization': {
            //         'type': 'function-wrap',
            //         'function': lambda: None,
            //     },
            let code = c_str!(
                r"{
                'type': 'definitions',
                'schema': {'type': 'definition-ref', 'schema_ref': 'C-ref'},
                'definitions': [
                    {
                        'type': 'typed-dict',
                        'fields': {
                            'root': {
                                'type': 'typed-dict-field',
                                'schema': {
                                    'type': 'definition-ref',
                                    'schema_ref': 'C-ref',
                                }
                            },
                        },
                        'ref': 'C-ref',
                        'serialization': {
                            'type': 'function-wrap',
                            'function': lambda: None,
                        },
                    },
                ]
            }"
            );
            let schema: Bound<'_, PyDict> = py.eval(code, None, None).unwrap().extract().unwrap();
            SchemaSerializer::py_new(schema, None).unwrap();
        });
    }

    #[test]
    fn test_literal_schema() {
        Python::with_gil(|py| {
            let code = c_str!(
                r#"
schema = {
    "type": "dict",
    "keys_schema": {
        "type": "literal",
        "expected": ["a", "b"],
    },
    "values_schema": {
        "type": "str",
    },
    "strict": False,
}
json_input = '{"a": "something"}'
            "#
            );
            let locals = PyDict::new(py);
            py.run(code, None, Some(&locals)).unwrap();
            let schema = locals.get_item("schema").unwrap().unwrap();
            let json_input = locals.get_item("json_input").unwrap().unwrap();
            let binding = SchemaValidator::py_new(py, &schema, None)
                .unwrap()
                .validate_json(py, &json_input, None, None, None, false.into(), None, None)
                .unwrap();
            let validation_result: Bound<'_, PyAny> = binding.extract(py).unwrap();
            let repr = format!("{}", validation_result.repr().unwrap());
            assert_eq!(repr, "{'a': 'something'}");
        });
    }

    #[test]
    fn test_segfault_for_recursive_schemas() {
        Python::with_gil(|py| {
            let code = c_str!(
                r"
schema = {
    'type': 'definitions',
    'schema': {
        'type': 'definition-ref',
        'schema_ref': '__main__.JSONData:4303261344'
    },
    'definitions': [
        {
            'type': 'union',
            'choices': [
                {
                    'type': 'dict',
                    'keys_schema': {'type': 'str'},
                    'values_schema': {
                        'type': 'definition-ref',
                        'schema_ref': '__main__.JSONData:4303261344'
                    },
                    'strict': False
                },
                {
                    'type': 'list',
                    'items_schema': {
                        'type': 'definition-ref',
                        'schema_ref': '__main__.JSONData:4303261344'
                    },
                    'strict': False
                }
            ],
            'ref': '__main__.JSONData:4303261344'
        }
    ]
}
dump_json_input_1 = 1
dump_json_input_2 = {'a': 'something'}
            "
            );
            let locals = PyDict::new(py);
            py.run(code, None, Some(&locals)).unwrap();
            let schema = locals
                .get_item("schema")
                .unwrap()
                .unwrap()
                .downcast_into::<PyDict>()
                .unwrap();
            let dump_json_input_1 = locals.get_item("dump_json_input_1").unwrap().unwrap();
            let dump_json_input_2 = locals.get_item("dump_json_input_2").unwrap().unwrap();
            let serializer = SchemaSerializer::py_new(schema, None).unwrap();
            let serialization_result = serializer
                .to_json(
                    py,
                    &dump_json_input_1,
                    None,
                    Some(false),
                    None,
                    None,
                    Some(false),
                    false,
                    false,
                    false,
                    false,
                    WarningsArg::Bool(false),
                    None,
                    false,
                    None,
                )
                .unwrap();
            let repr = format!("{}", serialization_result.bind(py).repr().unwrap());
            assert_eq!(repr, "b'1'");

            let serialization_result = serializer
                .to_json(
                    py,
                    &dump_json_input_2,
                    None,
                    Some(false),
                    None,
                    None,
                    Some(false),
                    false,
                    false,
                    false,
                    false,
                    WarningsArg::Bool(false),
                    None,
                    false,
                    None,
                )
                .unwrap();
            let repr = format!("{}", serialization_result.bind(py).repr().unwrap());
            assert_eq!(repr, "b'{\"a\":\"something\"}'");
        });
    }
}
