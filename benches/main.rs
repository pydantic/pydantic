#![feature(test)]

extern crate test;

use test::{black_box, Bencher};

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyString};

use _pydantic_core::{validate_core_schema, SchemaValidator};

fn build_schema_validator_with_globals(py: Python, code: &str, globals: Option<&PyDict>) -> SchemaValidator {
    let mut schema = py.eval(code, globals, None).unwrap().extract().unwrap();
    schema = validate_core_schema(&schema, None).unwrap().extract().unwrap();
    SchemaValidator::py_new(py, &schema, None).unwrap()
}

fn build_schema_validator(py: Python, code: &str) -> SchemaValidator {
    build_schema_validator_with_globals(py, code, None)
}

fn json<'a>(py: Python<'a>, code: &'a str) -> Bound<'a, PyAny> {
    black_box(PyString::new_bound(py, code).into_any())
}

#[bench]
fn ints_json(bench: &mut Bencher) {
    Python::with_gil(|py| {
        let validator = build_schema_validator(py, "{'type': 'int'}");

        let result = validator.validate_json(py, &json(py, "123"), None, None, None).unwrap();
        let result_int: i64 = result.extract(py).unwrap();
        assert_eq!(result_int, 123);

        bench.iter(|| black_box(validator.validate_json(py, &json(py, "123"), None, None, None).unwrap()))
    })
}

#[bench]
fn ints_python(bench: &mut Bencher) {
    Python::with_gil(|py| {
        let validator = build_schema_validator(py, "{'type': 'int'}");

        let input = 123_i64.into_py(py).into_bound(py);
        let result = validator.validate_python(py, &input, None, None, None, None).unwrap();
        let result_int: i64 = result.extract(py).unwrap();
        assert_eq!(result_int, 123);

        let input = black_box(input);
        bench.iter(|| black_box(validator.validate_python(py, &input, None, None, None, None).unwrap()))
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

        bench.iter(|| black_box(validator.validate_json(py, &json(py, &code), None, None, None).unwrap()))
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
        let input = black_box(input.bind(py));
        bench.iter(|| {
            let v = validator.validate_python(py, &input, None, None, None, None).unwrap();
            black_box(v)
        })
    })
}

#[bench]
fn list_int_python_isinstance(bench: &mut Bencher) {
    Python::with_gil(|py| {
        let (validator, input) = list_int_input(py);
        let input = black_box(input.bind(py));
        let v = validator.isinstance_python(py, &input, None, None, None, None).unwrap();
        assert!(v);

        bench.iter(|| {
            let v = validator.isinstance_python(py, &input, None, None, None, None).unwrap();
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

        match validator.validate_json(py, &json(py, &code), None, None, None) {
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
            || match validator.validate_json(py, &json(py, &code), None, None, None) {
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

    let input = py.eval(&code, None, None).unwrap().extract().unwrap();

    match validator.validate_python(py, &input, None, None, None, None) {
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

        let input = black_box(input.bind(py));
        bench.iter(|| {
            let result = validator.validate_python(py, &input, None, None, None, None);

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
        let input = black_box(input.bind(py));
        let r = validator.isinstance_python(py, &input, None, None, None, None).unwrap();
        assert!(!r);

        bench.iter(|| {
            black_box(validator.isinstance_python(py, &input, None, None, None, None).unwrap());
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

        bench.iter(|| black_box(validator.validate_json(py, &json(py, &code), None, None, None).unwrap()))
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
        let input = py.eval(&code, None, None).unwrap().to_object(py);
        let input = black_box(input.bind(py));
        bench.iter(|| {
            let v = validator.validate_python(py, &input, None, None, None, None).unwrap();
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

        bench.iter(|| black_box(validator.validate_json(py, &json(py, &code), None, None, None).unwrap()))
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
        let input = py.eval(&code, None, None).unwrap().to_object(py);
        let input = black_box(input.bind(py));
        bench.iter(|| {
            let v = validator.validate_python(py, &input, None, None, None, None).unwrap();
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

        let input = py.eval(&code, None, None).unwrap().to_object(py).into_bound(py);

        match validator.validate_python(py, &input, None, None, None, None) {
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
            let result = validator.validate_python(py, &input, None, None, None, None);

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

        bench.iter(|| black_box(validator.validate_json(py, &json(py, &code), None, None, None).unwrap()))
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
        let input = py.eval(&code, None, None).unwrap().to_object(py);
        let input = black_box(input.bind(py));
        bench.iter(|| {
            let v = validator.validate_python(py, &input, None, None, None, None).unwrap();
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

        let input = py.eval(code, None, None).unwrap().to_object(py);
        let input = black_box(input.bind(py));

        match validator.validate_python(py, &input, None, None, None, None) {
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
            let result = validator.validate_python(py, &input, None, None, None, None);

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

        let complete_schema = py.import_bound("complete_schema").unwrap();
        let mut schema = complete_schema.call_method0("schema").unwrap();
        schema = validate_core_schema(&schema, None).unwrap().extract().unwrap();
        let validator = SchemaValidator::py_new(py, &schema, None).unwrap();

        let input = complete_schema.call_method0("input_data_lax").unwrap();
        let input = black_box(input);

        bench.iter(|| {
            black_box(validator.validate_python(py, &input, None, None, None, None).unwrap());
        })
    })
}

#[bench]
fn nested_model_using_definitions(bench: &mut Bencher) {
    Python::with_gil(|py| {
        let sys_path = py.import("sys").unwrap().getattr("path").unwrap();
        sys_path.call_method1("append", ("./tests/benchmarks/",)).unwrap();

        let complete_schema = py.import_bound("nested_schema").unwrap();
        let mut schema = complete_schema.call_method0("schema_using_defs").unwrap();
        schema = validate_core_schema(&schema, None).unwrap().extract().unwrap();
        let validator = SchemaValidator::py_new(py, &schema, None).unwrap();

        let input = complete_schema.call_method0("input_data_valid").unwrap();
        let input = black_box(input);

        validator.validate_python(py, &input, None, None, None, None).unwrap();

        bench.iter(|| {
            black_box(validator.validate_python(py, &input, None, None, None, None).unwrap());
        })
    })
}

#[bench]
fn nested_model_inlined(bench: &mut Bencher) {
    Python::with_gil(|py| {
        let sys_path = py.import("sys").unwrap().getattr("path").unwrap();
        sys_path.call_method1("append", ("./tests/benchmarks/",)).unwrap();

        let complete_schema = py.import_bound("nested_schema").unwrap();
        let mut schema = complete_schema.call_method0("inlined_schema").unwrap();
        schema = validate_core_schema(&schema, None).unwrap().extract().unwrap();
        let validator = SchemaValidator::py_new(py, &schema, None).unwrap();

        let input = complete_schema.call_method0("input_data_valid").unwrap();
        let input = black_box(input);

        validator.validate_python(py, &input, None, None, None, None).unwrap();

        bench.iter(|| {
            black_box(validator.validate_python(py, &input, None, None, None, None).unwrap());
        })
    })
}

#[bench]
fn literal_ints_few_python(bench: &mut Bencher) {
    Python::with_gil(|py| {
        let validator = build_schema_validator(py, "{'type': 'literal', 'expected': list(range(5))}");

        let input = 4_i64.into_py(py);
        let input = input.bind(py);
        let result = validator.validate_python(py, &input, None, None, None, None).unwrap();
        let result_int: i64 = result.extract(py).unwrap();
        assert_eq!(result_int, 4);

        let input = black_box(input);
        bench.iter(|| black_box(validator.validate_python(py, &input, None, None, None, None).unwrap()))
    })
}

#[bench]
fn literal_strings_few_small_python(bench: &mut Bencher) {
    Python::with_gil(|py| {
        let validator = build_schema_validator(py, "{'type': 'literal', 'expected': [f'{idx}' for idx in range(5)]}");

        let input = py.eval("'4'", None, None).unwrap();
        let input = input.to_object(py).into_bound(py);
        let input_str: String = input.extract().unwrap();
        let result = validator.validate_python(py, &input, None, None, None, None).unwrap();
        let result_str: String = result.extract(py).unwrap();
        assert_eq!(result_str, input_str);

        let input = black_box(input);
        bench.iter(|| black_box(validator.validate_python(py, &input, None, None, None, None).unwrap()))
    })
}

#[bench]
fn literal_strings_few_large_python(bench: &mut Bencher) {
    Python::with_gil(|py| {
        let validator = build_schema_validator(
            py,
            "{'type': 'literal', 'expected': ['a' * 25 + f'{idx}' for idx in range(5)]}",
        );

        let input = py.eval("'a' * 25 + '4'", None, None).unwrap();
        let input = input.to_object(py).into_bound(py);
        let input_str: String = input.extract().unwrap();
        let result = validator.validate_python(py, &input, None, None, None, None).unwrap();
        let result_str: String = result.extract(py).unwrap();
        assert_eq!(result_str, input_str);

        let input = black_box(input);
        bench.iter(|| black_box(validator.validate_python(py, &input, None, None, None, None).unwrap()))
    })
}

#[bench]
fn literal_enums_few_python(bench: &mut Bencher) {
    Python::with_gil(|py| {
        let globals = PyDict::new_bound(py);
        py.run(
            r#"
from enum import Enum

class Foo(Enum):
    v1 = object()
    v2 = object()
    v3 = object()
    v4 = object()
"#,
            Some(globals.as_gil_ref()),
            None,
        )
        .unwrap();

        let validator = build_schema_validator_with_globals(
            py,
            "{'type': 'literal', 'expected': [Foo.v1, Foo.v2, Foo.v3, Foo.v4]}",
            Some(globals.as_gil_ref()),
        );

        let input = py.eval("Foo.v4", Some(globals.as_gil_ref()), None).unwrap();
        let input = input.to_object(py).into_bound(py);
        let result = validator.validate_python(py, &input, None, None, None, None).unwrap();
        assert!(input.eq(result).unwrap());

        let input = black_box(input);
        bench.iter(|| black_box(validator.validate_python(py, &input, None, None, None, None).unwrap()))
    })
}

#[bench]
fn literal_ints_many_python(bench: &mut Bencher) {
    Python::with_gil(|py| {
        let validator = build_schema_validator(py, "{'type': 'literal', 'expected': list(range(100))}");

        let input = 99_i64.into_py(py).into_bound(py);
        let result = validator.validate_python(py, &input, None, None, None, None).unwrap();
        let result_int: i64 = result.extract(py).unwrap();
        assert_eq!(result_int, 99);

        let input = black_box(input);
        bench.iter(|| black_box(validator.validate_python(py, &input, None, None, None, None).unwrap()))
    })
}

#[bench]
fn literal_strings_many_small_python(bench: &mut Bencher) {
    Python::with_gil(|py| {
        let validator = build_schema_validator(py, "{'type': 'literal', 'expected': [f'{idx}' for idx in range(100)]}");

        let input = py.eval("'99'", None, None).unwrap();
        let input = input.to_object(py).into_bound(py);
        let input_str: String = input.extract().unwrap();
        let result = validator.validate_python(py, &input, None, None, None, None).unwrap();
        let result_str: String = result.extract(py).unwrap();
        assert_eq!(result_str, input_str);

        let input = black_box(input);
        bench.iter(|| black_box(validator.validate_python(py, &input, None, None, None, None).unwrap()))
    })
}

#[bench]
fn literal_strings_many_large_python(bench: &mut Bencher) {
    Python::with_gil(|py| {
        let validator = build_schema_validator(
            py,
            "{'type': 'literal', 'expected': ['a' * 25 + f'{idx}' for idx in range(100)]}",
        );

        let input = py.eval("'a' * 25 + '99'", None, None).unwrap();
        let input = input.to_object(py).into_bound(py);
        let input_str: String = input.extract().unwrap();
        let result = validator.validate_python(py, &input, None, None, None, None).unwrap();
        let result_str: String = result.extract(py).unwrap();
        assert_eq!(result_str, input_str);

        let input = black_box(input);
        bench.iter(|| black_box(validator.validate_python(py, &input, None, None, None, None).unwrap()))
    })
}

#[bench]
fn literal_ints_many_json(bench: &mut Bencher) {
    Python::with_gil(|py| {
        let validator = build_schema_validator(py, "{'type': 'literal', 'expected': list(range(100))}");

        let input_json = py.eval("'99'", None, None).unwrap();
        let input_json = input_json.to_object(py).into_bound(py);
        let result = validator.validate_json(py, &input_json, None, None, None).unwrap();
        let result_int: i64 = result.extract(py).unwrap();
        assert_eq!(result_int, 99);

        let input_json = black_box(input_json);
        bench.iter(|| black_box(validator.validate_json(py, &input_json, None, None, None).unwrap()))
    })
}

#[bench]
fn literal_strings_many_large_json(bench: &mut Bencher) {
    Python::with_gil(|py| {
        let validator = build_schema_validator(
            py,
            "{'type': 'literal', 'expected': ['a' * 25 + f'{idx}' for idx in range(100)]}",
        );

        let input = py.eval("'a' * 25 + '99'", None, None).unwrap();
        let input = input.to_object(py).into_bound(py);
        let input_json = py.eval("'\"' + 'a' * 25 + '99' + '\"'", None, None).unwrap();
        let input_json = input_json.to_object(py).into_bound(py);
        let input_str: String = input.extract().unwrap();
        let result = validator.validate_json(py, &input_json, None, None, None).unwrap();
        let result_str: String = result.extract(py).unwrap();
        assert_eq!(result_str, input_str);

        let input_json = black_box(input_json);
        bench.iter(|| black_box(validator.validate_json(py, &input_json, None, None, None).unwrap()))
    })
}

#[bench]
fn literal_mixed_few_python(bench: &mut Bencher) {
    Python::with_gil(|py| {
        let globals = PyDict::new_bound(py);
        py.run(
            r#"
from enum import Enum

class Foo(Enum):
    v1 = object()
    v2 = object()
    v3 = object()
    v4 = object()
"#,
            Some(globals.as_gil_ref()),
            None,
        )
        .unwrap();
        let validator = build_schema_validator_with_globals(
            py,
            "{'type': 'literal', 'expected': [None, 'null', -1, Foo.v4]}",
            Some(globals.as_gil_ref()),
        );

        // String
        {
            let input = py.eval("'null'", None, None).unwrap();
            let input = input.to_object(py).into_bound(py);
            let input_str: String = input.extract().unwrap();
            let result = validator.validate_python(py, &input, None, None, None, None).unwrap();
            let result_str: String = result.extract(py).unwrap();
            assert_eq!(result_str, input_str);

            let input = black_box(input);
            bench.iter(|| black_box(validator.validate_python(py, &input, None, None, None, None).unwrap()))
        }

        // Int
        {
            let input = py.eval("-1", None, None).unwrap();
            let input = input.to_object(py).into_bound(py);
            let input_int: i64 = input.extract().unwrap();
            let result = validator.validate_python(py, &input, None, None, None, None).unwrap();
            let result_int: i64 = result.extract(py).unwrap();
            assert_eq!(result_int, input_int);

            let input = black_box(input);
            bench.iter(|| black_box(validator.validate_python(py, &input, None, None, None, None).unwrap()))
        }

        // None
        {
            let input = py.eval("None", None, None).unwrap();
            let input = input.to_object(py).into_bound(py);
            let result = validator.validate_python(py, &input, None, None, None, None).unwrap();
            assert!(input.eq(result).unwrap());

            let input = black_box(input);
            bench.iter(|| black_box(validator.validate_python(py, &input, None, None, None, None).unwrap()))
        }

        // Enum
        {
            let input = py.eval("Foo.v4", Some(globals.as_gil_ref()), None).unwrap();
            let input = input.to_object(py).into_bound(py);
            let result = validator.validate_python(py, &input, None, None, None, None).unwrap();
            assert!(input.eq(result).unwrap());

            let input = black_box(input);
            bench.iter(|| black_box(validator.validate_python(py, &input, None, None, None, None).unwrap()))
        }
    })
}
