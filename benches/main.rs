#![feature(test)]

extern crate test;

use test::{black_box, Bencher};

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyString};

use _pydantic_core::SchemaValidator;

fn build_schema_validator(py: Python, code: &str) -> SchemaValidator {
    let schema: &PyDict = py.eval(code, None, None).unwrap().extract().unwrap();
    SchemaValidator::py_new(py, schema, None).unwrap()
}

fn json<'a>(py: Python<'a>, code: &'a str) -> &'a PyAny {
    black_box(PyString::new(py, code))
}

#[bench]
fn ints_json(bench: &mut Bencher) {
    Python::with_gil(|py| {
        let validator = build_schema_validator(py, "{'type': 'int'}");

        let result = validator.validate_json(py, json(py, "123"), None, None, None).unwrap();
        let result_int: i64 = result.extract(py).unwrap();
        assert_eq!(result_int, 123);

        bench.iter(|| black_box(validator.validate_json(py, json(py, "123"), None, None, None).unwrap()))
    })
}

#[bench]
fn ints_python(bench: &mut Bencher) {
    Python::with_gil(|py| {
        let validator = build_schema_validator(py, "{'type': 'int'}");

        let input = 123_i64.into_py(py);
        let input = input.as_ref(py);
        let result = validator.validate_python(py, input, None, None, None).unwrap();
        let result_int: i64 = result.extract(py).unwrap();
        assert_eq!(result_int, 123);

        let input = black_box(input);
        bench.iter(|| black_box(validator.validate_python(py, input, None, None, None).unwrap()))
    })
}

#[bench]
fn list_int_json(bench: &mut Bencher) {
    Python::with_gil(|py| {
        let validator = build_schema_validator(py, "{'type': 'list', 'items_schema': {'type': 'int'}}");
        let code = format!(
            "[{}]",
            (0..100).map(|x| x.to_string()).collect::<Vec<String>>().join(",")
        );

        bench.iter(|| black_box(validator.validate_json(py, json(py, &code), None, None, None).unwrap()))
    })
}

fn list_int_input(py: Python<'_>) -> (SchemaValidator, PyObject) {
    let validator = build_schema_validator(py, "{'type': 'list', 'items_schema': {'type': 'int'}}");
    let code = format!(
        "[{}]",
        (0..100).map(|x| x.to_string()).collect::<Vec<String>>().join(",")
    );

    let input = py.eval(&code, None, None).unwrap();
    (validator, input.to_object(py))
}

#[bench]
fn list_int_python(bench: &mut Bencher) {
    Python::with_gil(|py| {
        let (validator, input) = list_int_input(py);
        let input = black_box(input.as_ref(py));
        bench.iter(|| {
            let v = validator.validate_python(py, input, None, None, None).unwrap();
            black_box(v)
        })
    })
}

#[bench]
fn list_int_python_isinstance(bench: &mut Bencher) {
    Python::with_gil(|py| {
        let (validator, input) = list_int_input(py);
        let input = black_box(input.as_ref(py));
        let v = validator.isinstance_python(py, input, None, None, None).unwrap();
        assert!(v);

        bench.iter(|| {
            let v = validator.isinstance_python(py, input, None, None, None).unwrap();
            black_box(v)
        })
    })
}

#[bench]
fn list_error_json(bench: &mut Bencher) {
    Python::with_gil(|py| {
        let validator = build_schema_validator(py, "{'type': 'list', 'items_schema': {'type': 'int'}}");
        let code = format!(
            "[{}]",
            (0..100)
                .map(|v| format!(r#""{}""#, as_str(v)))
                .collect::<Vec<String>>()
                .join(", ")
        );

        match validator.validate_json(py, json(py, &code), None, None, None) {
            Ok(_) => panic!("unexpectedly valid"),
            Err(e) => {
                let v = e.value(py);
                // println!("error: {}", v.to_string());
                assert_eq!(v.getattr("title").unwrap().to_string(), "list[int]");
                let error_count: i64 = v.call_method0("error_count").unwrap().extract().unwrap();
                assert_eq!(error_count, 100);
            }
        };

        bench.iter(
            || match validator.validate_json(py, json(py, &code), None, None, None) {
                Ok(_) => panic!("unexpectedly valid"),
                Err(e) => black_box(e),
            },
        )
    })
}

fn list_error_python_input(py: Python<'_>) -> (SchemaValidator, PyObject) {
    let validator = build_schema_validator(py, "{'type': 'list', 'items_schema': {'type': 'int'}}");
    let code = format!(
        "[{}]",
        (0..100)
            .map(|v| format!(r#""{}""#, as_str(v)))
            .collect::<Vec<String>>()
            .join(", ")
    );

    let input = py.eval(&code, None, None).unwrap();

    match validator.validate_python(py, input, None, None, None) {
        Ok(_) => panic!("unexpectedly valid"),
        Err(e) => {
            let v = e.value(py);
            // println!("error: {}", v.to_string());
            assert_eq!(v.getattr("title").unwrap().to_string(), "list[int]");
            let error_count: i64 = v.call_method0("error_count").unwrap().extract().unwrap();
            assert_eq!(error_count, 100);
        }
    };
    (validator, input.to_object(py))
}

#[bench]
fn list_error_python(bench: &mut Bencher) {
    Python::with_gil(|py| {
        let (validator, input) = list_error_python_input(py);

        let input = black_box(input.as_ref(py));
        bench.iter(|| {
            let result = validator.validate_python(py, input, None, None, None);

            match result {
                Ok(_) => panic!("unexpectedly valid"),
                Err(e) => black_box(e),
            }
        })
    })
}

#[bench]
fn list_error_python_isinstance(bench: &mut Bencher) {
    Python::with_gil(|py| {
        let (validator, input) = list_error_python_input(py);
        let r = validator
            .isinstance_python(py, black_box(input.as_ref(py)), None, None, None)
            .unwrap();
        assert!(!r);

        let input = black_box(input.as_ref(py));
        bench.iter(|| {
            black_box(validator.isinstance_python(py, input, None, None, None).unwrap());
        })
    })
}

#[bench]
fn list_any_json(bench: &mut Bencher) {
    Python::with_gil(|py| {
        let validator = build_schema_validator(py, "{'type': 'list'}");
        let code = format!(
            "[{}]",
            (0..100).map(|x| x.to_string()).collect::<Vec<String>>().join(",")
        );

        bench.iter(|| black_box(validator.validate_json(py, json(py, &code), None, None, None).unwrap()))
    })
}

#[bench]
fn list_any_python(bench: &mut Bencher) {
    Python::with_gil(|py| {
        let validator = build_schema_validator(py, "{'type': 'list'}");
        let code = format!(
            "[{}]",
            (0..100).map(|x| x.to_string()).collect::<Vec<String>>().join(",")
        );
        let input = py.eval(&code, None, None).unwrap();
        let input = black_box(input);
        bench.iter(|| {
            let v = validator.validate_python(py, input, None, None, None).unwrap();
            black_box(v)
        })
    })
}

fn as_char(i: u8) -> char {
    (i % 26 + 97) as char
}

fn as_str(i: u8) -> String {
    format!("{}{}", as_char(i / 26), as_char(i))
}

#[bench]
fn dict_json(bench: &mut Bencher) {
    Python::with_gil(|py| {
        let validator = build_schema_validator(
            py,
            "{'type': 'dict', 'keys_schema': {'type': 'str'}, 'values_schema': {'type': 'int'}}",
        );

        let code = format!(
            "{{{}}}",
            (0..100_u8)
                .map(|i| format!(r#""{}": {i}"#, as_str(i)))
                .collect::<Vec<String>>()
                .join(", ")
        );

        bench.iter(|| black_box(validator.validate_json(py, json(py, &code), None, None, None).unwrap()))
    })
}

#[bench]
fn dict_python(bench: &mut Bencher) {
    Python::with_gil(|py| {
        let validator = build_schema_validator(
            py,
            "{'type': 'dict', 'keys_schema': {'type': 'str'}, 'values_schema': {'type': 'int'}}",
        );

        let code = format!(
            "{{{}}}",
            (0..100_u8)
                .map(|i| format!(r#""{}{}": {i}"#, as_char(i / 26), as_char(i)))
                .collect::<Vec<String>>()
                .join(", ")
        );
        let input = py.eval(&code, None, None).unwrap();
        let input = black_box(input);
        bench.iter(|| {
            let v = validator.validate_python(py, input, None, None, None).unwrap();
            black_box(v)
        })
    })
}

#[bench]
fn dict_value_error(bench: &mut Bencher) {
    Python::with_gil(|py| {
        let validator = build_schema_validator(
            py,
            r#"{
                'type': 'dict',
                'keys_schema': {'type': 'str'},
                'values_schema': {'type': 'int', 'lt': 0},
            }"#,
        );

        let code = format!(
            "{{{}}}",
            (0..100_u8)
                .map(|i| format!(r#""{}": {i}"#, as_str(i)))
                .collect::<Vec<String>>()
                .join(", ")
        );

        let input = py.eval(&code, None, None).unwrap();

        match validator.validate_python(py, input, None, None, None) {
            Ok(_) => panic!("unexpectedly valid"),
            Err(e) => {
                let v = e.value(py);
                // println!("error: {}", v.to_string());
                assert_eq!(v.getattr("title").unwrap().to_string(), "dict[str,constrained-int]");
                let error_count: i64 = v.call_method0("error_count").unwrap().extract().unwrap();
                assert_eq!(error_count, 100);
            }
        };

        let input = black_box(input);
        bench.iter(|| {
            let result = validator.validate_python(py, input, None, None, None);

            match result {
                Ok(_) => panic!("unexpectedly valid"),
                Err(e) => black_box(e),
            }
        })
    })
}

#[bench]
fn typed_dict_json(bench: &mut Bencher) {
    Python::with_gil(|py| {
        let validator = build_schema_validator(
            py,
            r#"{
          'type': 'typed-dict',
          'extra_behavior': 'ignore',
          'fields': {
            'a': {'type': 'typed-dict-field', 'schema': {'type': 'int'}},
            'b': {'type': 'typed-dict-field', 'schema': {'type': 'int'}},
            'c': {'type': 'typed-dict-field', 'schema': {'type': 'int'}},
            'd': {'type': 'typed-dict-field', 'schema': {'type': 'int'}},
            'e': {'type': 'typed-dict-field', 'schema': {'type': 'int'}},
            'f': {'type': 'typed-dict-field', 'schema': {'type': 'int'}},
            'g': {'type': 'typed-dict-field', 'schema': {'type': 'int'}},
            'h': {'type': 'typed-dict-field', 'schema': {'type': 'int'}},
            'i': {'type': 'typed-dict-field', 'schema': {'type': 'int'}},
            'j': {'type': 'typed-dict-field', 'schema': {'type': 'int'}},
          },
        }"#,
        );

        let code = r#"{"a": 1, "b": 2, "c": 3, "d": 4, "e": 5, "f": 6, "g": 7, "h": 8, "i": 9, "j": 0}"#.to_string();

        bench.iter(|| black_box(validator.validate_json(py, json(py, &code), None, None, None).unwrap()))
    })
}

#[bench]
fn typed_dict_python(bench: &mut Bencher) {
    Python::with_gil(|py| {
        let validator = build_schema_validator(
            py,
            r#"{
          'type': 'typed-dict',
          'extra_behavior': 'ignore',
          'fields': {
            'a': {'type': 'typed-dict-field', 'schema': {'type': 'int'}},
            'b': {'type': 'typed-dict-field', 'schema': {'type': 'int'}},
            'c': {'type': 'typed-dict-field', 'schema': {'type': 'int'}},
            'd': {'type': 'typed-dict-field', 'schema': {'type': 'int'}},
            'e': {'type': 'typed-dict-field', 'schema': {'type': 'int'}},
            'f': {'type': 'typed-dict-field', 'schema': {'type': 'int'}},
            'g': {'type': 'typed-dict-field', 'schema': {'type': 'int'}},
            'h': {'type': 'typed-dict-field', 'schema': {'type': 'int'}},
            'i': {'type': 'typed-dict-field', 'schema': {'type': 'int'}},
            'j': {'type': 'typed-dict-field', 'schema': {'type': 'int'}},
          },
        }"#,
        );

        let code = r#"{"a": 1, "b": 2, "c": 3, "d": 4, "e": 5, "f": 6, "g": 7, "h": 8, "i": 9, "j": 0}"#.to_string();
        let input = py.eval(&code, None, None).unwrap();
        let input = black_box(input);
        bench.iter(|| {
            let v = validator.validate_python(py, input, None, None, None).unwrap();
            black_box(v)
        })
    })
}

#[bench]
fn typed_dict_deep_error(bench: &mut Bencher) {
    Python::with_gil(|py| {
        let validator = build_schema_validator(
            py,
            r#"{
            'type': 'typed-dict',
            'fields': {
                'field_a': {'type': 'typed-dict-field', 'schema': {'type': 'str'}},
                'field_b': {
                    'type': 'typed-dict-field',
                    'schema': {
                        'type': 'typed-dict',
                        'fields': {
                            'field_c': {'type': 'typed-dict-field','schema': {'type': 'str'}},
                            'field_d': {
                                'type': 'typed-dict-field',
                                'schema': {
                                    'type': 'typed-dict',
                                    'fields': {'field_e': {'type': 'typed-dict-field','schema': {'type': 'str'}}, 'field_f': {'type': 'typed-dict-field','schema': {'type': 'int'}}},
                                }
                            },
                        },
                    }
                },
            },
        }"#,
        );

        let code = "{'field_a': '1', 'field_b': {'field_c': '2', 'field_d': {'field_e': '4', 'field_f': 'xx'}}}";

        let input = py.eval(code, None, None).unwrap();
        let input = black_box(input);

        match validator.validate_python(py, input, None, None, None) {
            Ok(_) => panic!("unexpectedly valid"),
            Err(e) => {
                let v = e.value(py);
                // println!("error: {}", v.to_string());
                assert_eq!(v.getattr("title").unwrap().to_string(), "typed-dict");
                let error_count: i64 = v.call_method0("error_count").unwrap().extract().unwrap();
                assert_eq!(error_count, 1);
            }
        };

        bench.iter(|| {
            let result = validator.validate_python(py, input, None, None, None);

            match result {
                Ok(_) => panic!("unexpectedly valid"),
                Err(e) => black_box(e),
            }
        })
    })
}

#[bench]
fn complete_model(bench: &mut Bencher) {
    Python::with_gil(|py| {
        let sys_path = py.import("sys").unwrap().getattr("path").unwrap();
        sys_path.call_method1("append", ("./tests/benchmarks/",)).unwrap();

        let complete_schema = py.import("complete_schema").unwrap();
        let schema = complete_schema.call_method0("schema").unwrap();
        let validator = SchemaValidator::py_new(py, schema, None).unwrap();

        let input = complete_schema.call_method0("input_data_lax").unwrap();
        let input = black_box(input);

        bench.iter(|| {
            black_box(validator.validate_python(py, input, None, None, None).unwrap());
        })
    })
}
