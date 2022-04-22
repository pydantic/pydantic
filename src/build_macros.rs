macro_rules! dict_get {
    ($dict:ident, $key:expr, $type:ty) => {
        match $dict.get_item($key) {
            Some(t) => Some(<$type>::extract(t)?),
            None => None,
        }
    };
}
pub(crate) use dict_get;

macro_rules! dict_get_required {
    ($dict:ident, $key:expr, $type:ty) => {
        match $dict.get_item($key) {
            Some(t) => Ok(<$type>::extract(t)?),
            None => crate::build_macros::py_error!(r#""{}" is required"#, $key),
        }
    };
}
pub(crate) use dict_get_required;

macro_rules! optional_dict_get {
    ($optional_dict:ident, $key:expr, $type:ty) => {
        match $optional_dict {
            Some(d) => crate::build_macros::dict_get!(d, $key, $type),
            None => None,
        }
    };
}
pub(crate) use optional_dict_get;

macro_rules! is_strict {
    ($schema:ident, $config:ident) => {
        match crate::build_macros::dict_get!($schema, "strict", bool) {
            Some(v) => v,
            None => crate::build_macros::optional_dict_get!($config, "strict", bool).unwrap_or(false),
        }
    };
}
pub(crate) use is_strict;

macro_rules! dict {
    ($py:ident, $($k:expr => $v:expr),*) => {{
        pyo3::types::IntoPyDict::into_py_dict([$(($k, $v.into_py($py)),)*], $py).into()
    }};
}
pub(crate) use dict;

macro_rules! py_error {
    ($msg:expr) => {
        crate::build_macros::py_error!(crate::SchemaError; $msg)
    };
    ($msg:expr, $( $msg_args:expr ),+ ) => {
        crate::build_macros::py_error!(crate::SchemaError; $msg, $( $msg_args ),+)
    };

    ($error_type:ty; $msg:expr) => {
        Err(<$error_type>::new_err($msg))
    };

    ($error_type:ty; $msg:expr, $( $msg_args:expr ),+ ) => {
        Err(<$error_type>::new_err(format!($msg, $( $msg_args ),+)))
    };
}
pub(crate) use py_error;
