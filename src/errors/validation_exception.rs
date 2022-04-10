use pyo3::create_exception;
use pyo3::exceptions::PyValueError;

create_exception!(_pydantic_core, ValidationError, PyValueError);

// TODO impl ValidationError methods
