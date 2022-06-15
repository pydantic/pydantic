use criterion::{black_box, criterion_group, criterion_main, Criterion};
use std::time::Duration;

use pyo3::prelude::*;
use pyo3::types::PyDict;

use _pydantic_core::SchemaValidator;

fn build_schema_validator(py: Python, code: &str) -> SchemaValidator {
    let schema: &PyDict = py.eval(code, None, None).unwrap().extract().unwrap();
    SchemaValidator::py_new(py, schema).unwrap()
}

pub fn benchmark_ints(c: &mut Criterion) {
    let gil = Python::acquire_gil();
    let py = gil.python();
    let validator = build_schema_validator(py, "{'type': 'int'}");

    let result = validator.validate_json(py, black_box("123".to_string())).unwrap();
    let result_int: i64 = result.extract(py).unwrap();
    assert_eq!(result_int, 123);

    c.bench_function("validate_json int", |b| {
        b.iter(|| validator.validate_json(py, black_box("123".to_string())).unwrap())
    });

    let input_python = black_box(123_i64.into_py(py));
    let result = validator.validate_python(py, input_python.as_ref(py)).unwrap();
    let result_int: i64 = result.extract(py).unwrap();
    assert_eq!(result_int, 123);

    c.bench_function("validate_python int", |b| {
        b.iter(|| validator.validate_python(py, input_python.as_ref(py)).unwrap())
    });
}

pub fn benchmark_dict(c: &mut Criterion) {
    let gil = Python::acquire_gil();
    let py = gil.python();
    let validator = build_schema_validator(py, "{'type': 'dict', 'keys': 'str', 'values': 'int'}");

    c.bench_function("validate_json Dict[str, int]", |b| {
        b.iter(|| {
            let input_json = black_box(
                r#"
            {
                "a": 1,
                "b": 2,
                "c": 3,
                "d": 4,
                "e": 5
            }
            "#
                .to_string(),
            );
            validator.validate_json(py, input_json).unwrap()
        })
    });
}

pub fn benchmark_model(c: &mut Criterion) {
    let gil = Python::acquire_gil();
    let py = gil.python();
    let validator = build_schema_validator(
        py,
        r#"{
          'type': 'model',
          'extra': 'ignore',
          'fields': {
            'a': 'int',
            'b': 'int',
            'c': 'int',
            'd': 'int',
            'e': 'int',
          },
        }"#,
    );

    c.bench_function("validate_json model", |b| {
        b.iter(|| {
            let input_json = black_box(
                r#"
                {
                    "a": 1,
                    "b": 2,
                    "c": 3,
                    "d": 4,
                    "e": 5
                }
                "#
                .to_string(),
            );
            validator.validate_json(py, input_json).unwrap()
        })
    });
}

criterion_group! {
    name = benches;
    config = Criterion::default().warm_up_time(Duration::from_secs(1)).measurement_time(Duration::from_secs(3));
    targets =  benchmark_ints, benchmark_dict, benchmark_model
}
criterion_main!(benches);
