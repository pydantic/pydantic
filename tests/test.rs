#[cfg(test)]
mod tests {
    use _pydantic_core::SchemaSerializer;
    use pyo3::prelude::*;
    use pyo3::types::PyDict;

    #[test]
    fn test_build_schema_serializer() {
        Python::with_gil(|py| {
            let code = r#"{
                'type': 'typed-dict',
                'fields': {
                    'root': {
                        'type': 'typed-dict-field',
                        'schema': {
                            'type': 'definition-ref',
                            'schema_ref': 'C-ref',
                        },
                    },
                },
                'ref': 'C-ref',
                'serialization': {
                    'type': 'function-wrap',
                    'function': lambda: None,
                },
            }"#;
            let schema: &PyDict = py.eval(code, None, None).unwrap().extract().unwrap();
            SchemaSerializer::py_new(py, schema, None).unwrap();
        })
    }
}
