#[cfg(test)]
mod tests {
    use _pydantic_core::{SchemaSerializer, SchemaValidator};
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
            let code = r"{
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
            }";
            let schema: &PyDict = py.eval(code, None, None).unwrap().extract().unwrap();
            SchemaSerializer::py_new(py, schema, None).unwrap();
        });
    }

    #[test]
    fn test_serialize_computed_fields() {
        Python::with_gil(|py| {
            let code = r#"
class A:
    @property
    def b(self) -> str:
        return "b"

schema = {
    "cls": A,
    "config": {},
    "schema": {
        "computed_fields": [
            {"property_name": "b", "return_schema": {"type": "any"}, "type": "computed-field"}
        ],
        "fields": {},
        "type": "model-fields",
    },
    "type": "model",
}
a = A()
            "#;
            let locals = PyDict::new(py);
            py.run(code, None, Some(locals)).unwrap();
            let a: &PyAny = locals.get_item("a").unwrap().unwrap().extract().unwrap();
            let schema: &PyDict = locals.get_item("schema").unwrap().unwrap().extract().unwrap();
            let serialized: Vec<u8> = SchemaSerializer::py_new(py, schema, None)
                .unwrap()
                .to_json(py, a, None, None, None, true, false, false, false, false, true, None)
                .unwrap()
                .extract(py)
                .unwrap();
            assert_eq!(serialized, b"{\"b\":\"b\"}");
        });
    }

    #[test]
    fn test_literal_schema() {
        Python::with_gil(|py| {
            let code = r#"
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
            "#;
            let locals = PyDict::new(py);
            py.run(code, None, Some(locals)).unwrap();
            let schema: &PyDict = locals.get_item("schema").unwrap().unwrap().extract().unwrap();
            let json_input: &PyAny = locals.get_item("json_input").unwrap().unwrap().extract().unwrap();
            let binding = SchemaValidator::py_new(py, schema, None)
                .unwrap()
                .validate_json(py, json_input, None, None, None)
                .unwrap();
            let validation_result: &PyAny = binding.extract(py).unwrap();
            let repr = format!("{}", validation_result.repr().unwrap());
            assert_eq!(repr, "{'a': 'something'}");
        });
    }
}
