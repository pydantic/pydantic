use pyo3::exceptions::{PyKeyError, PyTypeError};
use pyo3::prelude::*;
use pyo3::types::PyDict;
use pyo3::FromPyObject;

pub trait SchemaDict<'py> {
    fn get_as<T>(&'py self, key: &str) -> PyResult<Option<T>>
    where
        T: FromPyObject<'py>;

    fn get_as_req<T>(&'py self, key: &str) -> PyResult<T>
    where
        T: FromPyObject<'py>;
}

impl<'py> SchemaDict<'py> for PyDict {
    fn get_as<T>(&'py self, key: &str) -> PyResult<Option<T>>
    where
        T: FromPyObject<'py>,
    {
        match self.get_item(key) {
            Some(t) => Ok(Some(<T>::extract(t)?)),
            None => Ok(None),
        }
    }

    fn get_as_req<T>(&'py self, key: &str) -> PyResult<T>
    where
        T: FromPyObject<'py>,
    {
        match self.get_item(key) {
            Some(t) => <T>::extract(t),
            None => py_error!(PyKeyError; r#""{}" is required"#, key),
        }
    }
}

impl<'py> SchemaDict<'py> for Option<&PyDict> {
    fn get_as<T>(&'py self, key: &str) -> PyResult<Option<T>>
    where
        T: FromPyObject<'py>,
    {
        match self {
            Some(d) => d.get_as(key),
            None => Ok(None),
        }
    }

    #[cfg_attr(has_no_coverage, no_coverage)]
    fn get_as_req<T>(&'py self, key: &str) -> PyResult<T>
    where
        T: FromPyObject<'py>,
    {
        match self {
            Some(d) => d.get_as_req(key),
            None => py_error!(PyTypeError; r#""{}" is required, so its source cannot be omitted"#, key),
        }
    }
}

pub fn schema_or_config<'py, T>(
    schema: &'py PyDict,
    config: Option<&'py PyDict>,
    schema_key: &str,
    config_key: &str,
) -> PyResult<Option<T>>
where
    T: FromPyObject<'py>,
{
    match schema.get_as(schema_key)? {
        Some(v) => Ok(Some(v)),
        None => match config {
            Some(config) => config.get_as(config_key),
            None => Ok(None),
        },
    }
}

pub fn is_strict(schema: &PyDict, config: Option<&PyDict>) -> PyResult<bool> {
    Ok(schema_or_config(schema, config, "strict", "strict")?.unwrap_or(false))
}

macro_rules! py_error {
    ($msg:expr) => {
        crate::build_tools::py_error!(crate::SchemaError; $msg)
    };
    ($msg:expr, $( $msg_args:expr ),+ ) => {
        crate::build_tools::py_error!(crate::SchemaError; $msg, $( $msg_args ),+)
    };

    ($error_type:ty; $msg:expr) => {
        Err(<$error_type>::new_err($msg))
    };

    ($error_type:ty; $msg:expr, $( $msg_args:expr ),+ ) => {
        Err(<$error_type>::new_err(format!($msg, $( $msg_args ),+)))
    };
}
pub(crate) use py_error;
