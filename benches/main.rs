#![feature(test)]

extern crate test;

use test::{black_box, Bencher};

use pyo3::prelude::*;
use pyo3::types::PyDict;

use _pydantic_core::SchemaValidator;

fn build_schema_validator(py: Python, code: &str) -> SchemaValidator {
    let schema: &PyDict = py.eval(code, None, None).unwrap().extract().unwrap();
    SchemaValidator::py_new(py, schema).unwrap()
}

#[bench]
fn ints_json(bench: &mut Bencher) {
    let gil = Python::acquire_gil();
    let py = gil.python();
    let validator = build_schema_validator(py, "{'type': 'int'}");

    let result = validator.validate_json(py, black_box("123".to_string())).unwrap();
    let result_int: i64 = result.extract(py).unwrap();
    assert_eq!(result_int, 123);

    bench.iter(|| black_box(validator.validate_json(py, black_box("123".to_string())).unwrap()))
}

#[bench]
fn ints_python(bench: &mut Bencher) {
    let gil = Python::acquire_gil();
    let py = gil.python();
    let validator = build_schema_validator(py, "{'type': 'int'}");

    let input_python = black_box(123_i64.into_py(py));
    let result = validator.validate_python(py, input_python.as_ref(py)).unwrap();
    let result_int: i64 = result.extract(py).unwrap();
    assert_eq!(result_int, 123);

    bench.iter(|| black_box(validator.validate_python(py, input_python.as_ref(py)).unwrap()))
}

#[bench]
fn list_int_json(bench: &mut Bencher) {
    let gil = Python::acquire_gil();
    let py = gil.python();
    let validator = build_schema_validator(py, "{'type': 'list', 'items': 'int'}");
    let code = format!(
        "[{}]",
        (0..100).map(|x| x.to_string()).collect::<Vec<String>>().join(",")
    );

    bench.iter(|| {
        let input_json = black_box(code.clone());
        black_box(validator.validate_json(py, input_json).unwrap())
    })
}

#[bench]
fn list_int_python(bench: &mut Bencher) {
    let gil = Python::acquire_gil();
    let py = gil.python();
    let validator = build_schema_validator(py, "{'type': 'list', 'items': 'int'}");
    let code = format!(
        "[{}]",
        (0..100).map(|x| x.to_string()).collect::<Vec<String>>().join(",")
    );

    let input_python = py.eval(&code, None, None).unwrap();
    let input_python = black_box(input_python.to_object(py));
    bench.iter(|| {
        let v = validator
            .validate_python(py, black_box(input_python.as_ref(py)))
            .unwrap();
        black_box(v)
    })
}

#[bench]
fn list_error_json(bench: &mut Bencher) {
    let gil = Python::acquire_gil();
    let py = gil.python();
    let validator = build_schema_validator(py, "{'type': 'list', 'items': 'int'}");
    let code = format!(
        "[{}]",
        (0..100)
            .map(|v| format!(r#""{}""#, as_str(v)))
            .collect::<Vec<String>>()
            .join(", ")
    );

    let input_json = black_box(code.clone());
    match validator.validate_json(py, input_json) {
        Ok(_) => panic!("unexpectedly valid"),
        Err(e) => {
            let v = e.value(py);
            // println!("error: {}", v.to_string());
            assert_eq!(v.getattr("title").unwrap().to_string(), "list[int]");
            let error_count: i64 = v.call_method0("error_count").unwrap().extract().unwrap();
            assert_eq!(error_count, 100);
        }
    };

    bench.iter(|| {
        let input_json = black_box(code.clone());
        match validator.validate_json(py, input_json) {
            Ok(_) => panic!("unexpectedly valid"),
            Err(e) => black_box(e),
        }
    })
}

#[bench]
fn list_error_python(bench: &mut Bencher) {
    let gil = Python::acquire_gil();
    let py = gil.python();
    let validator = build_schema_validator(py, "{'type': 'list', 'items': 'int'}");
    let code = format!(
        "[{}]",
        (0..100)
            .map(|v| format!(r#""{}""#, as_str(v)))
            .collect::<Vec<String>>()
            .join(", ")
    );

    let input_python = py.eval(&code, None, None).unwrap();
    let input_python = black_box(input_python.to_object(py));

    match validator.validate_python(py, input_python.as_ref(py)) {
        Ok(_) => panic!("unexpectedly valid"),
        Err(e) => {
            let v = e.value(py);
            // println!("error: {}", v.to_string());
            assert_eq!(v.getattr("title").unwrap().to_string(), "list[int]");
            let error_count: i64 = v.call_method0("error_count").unwrap().extract().unwrap();
            assert_eq!(error_count, 100);
        }
    };

    bench.iter(|| {
        let result = validator.validate_python(py, black_box(input_python.as_ref(py)));

        match result {
            Ok(_) => panic!("unexpectedly valid"),
            Err(e) => black_box(e),
        }
    })
}

#[bench]
fn list_any_json(bench: &mut Bencher) {
    let gil = Python::acquire_gil();
    let py = gil.python();
    let validator = build_schema_validator(py, "{'type': 'list'}");
    let code = format!(
        "[{}]",
        (0..100).map(|x| x.to_string()).collect::<Vec<String>>().join(",")
    );

    bench.iter(|| {
        let input_json = black_box(code.clone());
        black_box(validator.validate_json(py, input_json).unwrap())
    })
}

#[bench]
fn list_any_python(bench: &mut Bencher) {
    let gil = Python::acquire_gil();
    let py = gil.python();
    let validator = build_schema_validator(py, "{'type': 'list'}");
    let code = format!(
        "[{}]",
        (0..100).map(|x| x.to_string()).collect::<Vec<String>>().join(",")
    );
    let input_python = py.eval(&code, None, None).unwrap();
    let input_python = black_box(input_python.to_object(py));
    bench.iter(|| {
        let v = validator
            .validate_python(py, black_box(input_python.as_ref(py)))
            .unwrap();
        black_box(v)
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
    let gil = Python::acquire_gil();
    let py = gil.python();
    let validator = build_schema_validator(py, "{'type': 'dict', 'keys': 'str', 'values': 'int'}");

    let code = format!(
        "{{{}}}",
        (0..100_u8)
            .map(|i| format!(r#""{}": {}"#, as_str(i), i))
            .collect::<Vec<String>>()
            .join(", ")
    );

    bench.iter(|| {
        let input_json = black_box(code.to_string());
        black_box(validator.validate_json(py, input_json).unwrap())
    })
}

#[bench]
fn dict_python(bench: &mut Bencher) {
    let gil = Python::acquire_gil();
    let py = gil.python();
    let validator = build_schema_validator(py, "{'type': 'dict', 'keys': 'str', 'values': 'int'}");

    let code = format!(
        "{{{}}}",
        (0..100_u8)
            .map(|i| format!(r#""{}{}": {}"#, as_char(i / 26), as_char(i), i))
            .collect::<Vec<String>>()
            .join(", ")
    );
    let input_python = py.eval(&code, None, None).unwrap();
    let input_python = black_box(input_python.to_object(py));
    bench.iter(|| {
        let v = validator
            .validate_python(py, black_box(input_python.as_ref(py)))
            .unwrap();
        black_box(v)
    })
}

#[bench]
fn dict_value_error(bench: &mut Bencher) {
    let gil = Python::acquire_gil();
    let py = gil.python();
    let validator = build_schema_validator(
        py,
        r#"{
            'type': 'dict',
            'keys': 'str',
            'values': {
                'type': 'int',
                'lt': 0,
            },
        }"#,
    );

    let code = format!(
        "{{{}}}",
        (0..100_u8)
            .map(|i| format!(r#""{}": {}"#, as_str(i), i))
            .collect::<Vec<String>>()
            .join(", ")
    );

    let input_python = py.eval(&code, None, None).unwrap();
    let input_python = black_box(input_python.to_object(py));

    match validator.validate_python(py, input_python.as_ref(py)) {
        Ok(_) => panic!("unexpectedly valid"),
        Err(e) => {
            let v = e.value(py);
            // println!("error: {}", v.to_string());
            assert_eq!(v.getattr("title").unwrap().to_string(), "dict[str, constrained-int]");
            let error_count: i64 = v.call_method0("error_count").unwrap().extract().unwrap();
            assert_eq!(error_count, 100);
        }
    };

    bench.iter(|| {
        let result = validator.validate_python(py, black_box(input_python.as_ref(py)));

        match result {
            Ok(_) => panic!("unexpectedly valid"),
            Err(e) => black_box(e),
        }
    })
}

#[bench]
fn model_json(bench: &mut Bencher) {
    let gil = Python::acquire_gil();
    let py = gil.python();
    let validator = build_schema_validator(
        py,
        r#"{
          'type': 'model',
          'extra': 'ignore',
          'fields': {
            'a': {'schema': 'int'},
            'b': {'schema': 'int'},
            'c': {'schema': 'int'},
            'd': {'schema': 'int'},
            'e': {'schema': 'int'},
            'f': {'schema': 'int'},
            'g': {'schema': 'int'},
            'h': {'schema': 'int'},
            'i': {'schema': 'int'},
            'j': {'schema': 'int'},
          },
        }"#,
    );

    let code = r#"{"a": 1, "b": 2, "c": 3, "d": 4, "e": 5, "f": 6, "g": 7, "h": 8, "i": 9, "j": 0}"#.to_string();

    bench.iter(|| {
        let input_json = black_box(code.clone());
        black_box(validator.validate_json(py, input_json).unwrap())
    })
}

#[bench]
fn model_python(bench: &mut Bencher) {
    let gil = Python::acquire_gil();
    let py = gil.python();
    let validator = build_schema_validator(
        py,
        r#"{
          'type': 'model',
          'extra': 'ignore',
          'fields': {
            'a': {'schema': 'int'},
            'b': {'schema': 'int'},
            'c': {'schema': 'int'},
            'd': {'schema': 'int'},
            'e': {'schema': 'int'},
            'f': {'schema': 'int'},
            'g': {'schema': 'int'},
            'h': {'schema': 'int'},
            'i': {'schema': 'int'},
            'j': {'schema': 'int'},
          },
        }"#,
    );

    let code = r#"{"a": 1, "b": 2, "c": 3, "d": 4, "e": 5, "f": 6, "g": 7, "h": 8, "i": 9, "j": 0}"#.to_string();
    let input_python = py.eval(&code, None, None).unwrap();
    let input_python = black_box(input_python.to_object(py));
    bench.iter(|| {
        let v = validator
            .validate_python(py, black_box(input_python.as_ref(py)))
            .unwrap();
        black_box(v)
    })
}
