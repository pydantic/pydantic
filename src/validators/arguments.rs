use ahash::AHashSet;
use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyString, PyTuple};

use crate::build_tools::{py_err, schema_or_config_same, SchemaDict};
use crate::errors::{ErrorType, ValError, ValLineError, ValResult};
use crate::input::{GenericArguments, Input};
use crate::lookup_key::LookupKey;
use crate::recursion_guard::RecursionGuard;

use super::with_default::get_default;
use super::{build_validator, BuildContext, BuildValidator, CombinedValidator, Extra, Validator};

#[derive(Debug, Clone)]
struct Parameter {
    positional: bool,
    name: String,
    kw_lookup_key: Option<LookupKey>,
    kwarg_key: Option<Py<PyString>>,
    validator: CombinedValidator,
}

#[derive(Debug, Clone)]
pub struct ArgumentsValidator {
    parameters: Vec<Parameter>,
    positional_params_count: usize,
    var_args_validator: Option<Box<CombinedValidator>>,
    var_kwargs_validator: Option<Box<CombinedValidator>>,
}

impl BuildValidator for ArgumentsValidator {
    const EXPECTED_TYPE: &'static str = "arguments";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        build_context: &mut BuildContext<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let py = schema.py();

        let populate_by_name = schema_or_config_same(schema, config, intern!(py, "populate_by_name"))?.unwrap_or(false);

        let arguments_schema: &PyList = schema.get_as_req(intern!(py, "arguments_schema"))?;
        let mut parameters: Vec<Parameter> = Vec::with_capacity(arguments_schema.len());

        let mut positional_params_count = 0;
        let mut had_default_arg = false;

        for (arg_index, arg) in arguments_schema.iter().enumerate() {
            let arg: &PyDict = arg.downcast()?;

            let name: String = arg.get_as_req(intern!(py, "name"))?;
            let mode = arg
                .get_as::<&str>(intern!(py, "mode"))?
                .unwrap_or("positional_or_keyword");
            let positional = mode == "positional_only" || mode == "positional_or_keyword";
            if positional {
                positional_params_count = arg_index + 1;
            }

            let mut kw_lookup_key = None;
            let mut kwarg_key = None;
            if mode == "keyword_only" || mode == "positional_or_keyword" {
                kw_lookup_key = match arg.get_item(intern!(py, "alias")) {
                    Some(alias) => {
                        let alt_alias = if populate_by_name { Some(name.as_str()) } else { None };
                        Some(LookupKey::from_py(py, alias, alt_alias)?)
                    }
                    None => Some(LookupKey::from_string(py, &name)),
                };
                kwarg_key = Some(PyString::intern(py, &name).into());
            }

            let schema: &PyAny = arg.get_as_req(intern!(py, "schema"))?;

            let validator = match build_validator(schema, config, build_context) {
                Ok(v) => v,
                Err(err) => return py_err!("Parameter '{}':\n  {}", name, err),
            };

            let has_default = match validator {
                CombinedValidator::WithDefault(ref v) => {
                    if v.omit_on_error() {
                        return py_err!("Parameter '{}': omit_on_error cannot be used with arguments", name);
                    }
                    v.has_default()
                }
                _ => false,
            };

            if had_default_arg && !has_default {
                return py_err!("Non-default argument '{}' follows default argument", name);
            } else if has_default {
                had_default_arg = true;
            }
            parameters.push(Parameter {
                positional,
                kw_lookup_key,
                name,
                kwarg_key,
                validator,
            });
        }

        Ok(Self {
            parameters,
            positional_params_count,
            var_args_validator: match schema.get_item(intern!(py, "var_args_schema")) {
                Some(v) => Some(Box::new(build_validator(v, config, build_context)?)),
                None => None,
            },
            var_kwargs_validator: match schema.get_item(intern!(py, "var_kwargs_schema")) {
                Some(v) => Some(Box::new(build_validator(v, config, build_context)?)),
                None => None,
            },
        }
        .into())
    }
}

macro_rules! py_get {
    ($obj:ident, $index:ident) => {
        $obj.get_item($index).ok()
    };
}

macro_rules! py_slice {
    ($obj:ident, $from:expr, $to:expr) => {
        $obj.get_slice($from, $to)
    };
}

macro_rules! json_get {
    ($obj:ident, $index:ident) => {
        $obj.get($index)
    };
}

macro_rules! json_slice {
    ($obj:ident, $from:expr, $to:expr) => {
        $obj[$from..$to]
    };
}

impl Validator for ArgumentsValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        extra: &Extra,
        slots: &'data [CombinedValidator],
        recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        let args = input.validate_args()?;

        let mut output_args: Vec<PyObject> = Vec::with_capacity(self.positional_params_count);
        let output_kwargs = PyDict::new(py);
        let mut errors: Vec<ValLineError> = Vec::new();
        let mut used_kwargs: AHashSet<&str> = AHashSet::with_capacity(self.parameters.len());

        macro_rules! process {
            ($args:ident, $get_method:ident, $get_macro:ident, $slice_macro:ident) => {{
                // go through arguments getting the value from args or kwargs and validating it
                for (index, parameter) in self.parameters.iter().enumerate() {
                    let mut pos_value = None;
                    if let Some(args) = $args.args {
                        if parameter.positional {
                            pos_value = $get_macro!(args, index);
                        }
                    }
                    let mut kw_value = None;
                    if let Some(kwargs) = $args.kwargs {
                        if let Some(ref lookup_key) = parameter.kw_lookup_key {
                            if let Some((key, value)) = lookup_key.$get_method(kwargs)? {
                                used_kwargs.insert(key);
                                kw_value = Some(value);
                            }
                        }
                    }

                    match (pos_value, kw_value) {
                        (Some(_), Some(kw_value)) => {
                            errors.push(ValLineError::new_with_loc(
                                ErrorType::MultipleArgumentValues,
                                kw_value,
                                parameter.name.clone(),
                            ));
                        }
                        (Some(pos_value), None) => {
                            match parameter
                                .validator
                                .validate(py, pos_value, extra, slots, recursion_guard)
                            {
                                Ok(value) => output_args.push(value),
                                Err(ValError::LineErrors(line_errors)) => {
                                    errors.extend(line_errors.into_iter().map(|err| err.with_outer_location(index.into())));
                                }
                                Err(err) => return Err(err),
                            }
                        }
                        (None, Some(kw_value)) => {
                            match parameter
                                .validator
                                .validate(py, kw_value, extra, slots, recursion_guard)
                            {
                                Ok(value) => output_kwargs.set_item(parameter.kwarg_key.as_ref().unwrap(), value)?,
                                Err(ValError::LineErrors(line_errors)) => {
                                    errors.extend(
                                        line_errors
                                            .into_iter()
                                            .map(|err| err.with_outer_location(parameter.name.clone().into())),
                                    );
                                }
                                Err(err) => return Err(err),
                            }
                        }
                        (None, None) => {
                            if let Some(value) = get_default(py, &parameter.validator)? {
                                if let Some(ref kwarg_key) = parameter.kwarg_key {
                                    output_kwargs.set_item(kwarg_key, value.as_ref())?;
                                } else {
                                    output_args.push(value.as_ref().clone_ref(py));
                                }
                            } else if parameter.kwarg_key.is_some() {
                                errors.push(ValLineError::new_with_loc(
                                    ErrorType::MissingKeywordArgument,
                                    input,
                                    parameter.name.clone(),
                                ));
                            } else {
                                errors.push(ValLineError::new_with_loc(ErrorType::MissingPositionalArgument, input, index));
                            };
                        }
                    }
                }
                // if there are args check any where index > positional_params_count since they won't have been checked yet
                if let Some(args) = $args.args {
                    let len = args.len();
                    if len > self.positional_params_count {
                        if let Some(ref validator) = self.var_args_validator {
                            for (index, item) in $slice_macro!(args, self.positional_params_count, len).iter().enumerate() {
                                match validator.validate(py, item, extra, slots, recursion_guard) {
                                    Ok(value) => output_args.push(value),
                                    Err(ValError::LineErrors(line_errors)) => {
                                        errors.extend(
                                            line_errors
                                                .into_iter()
                                                .map(|err| err.with_outer_location((index + self.positional_params_count).into())),
                                        );
                                    }
                                    Err(err) => return Err(err),
                                }
                            }
                        } else {
                            for (index, item) in $slice_macro!(args, self.positional_params_count, len).iter().enumerate() {
                                errors.push(ValLineError::new_with_loc(
                                    ErrorType::UnexpectedPositionalArgument,
                                    item,
                                    index + self.positional_params_count,
                                ));
                            }
                        }
                    }
                }
                // if there are kwargs check any that haven't been processed yet
                if let Some(kwargs) = $args.kwargs {
                    for (raw_key, value) in kwargs.iter() {
                        let either_str = match raw_key.strict_str() {
                            Ok(k) => k,
                            Err(ValError::LineErrors(line_errors)) => {
                                for err in line_errors {
                                    errors.push(
                                        err.with_outer_location(raw_key.as_loc_item())
                                            .with_type(ErrorType::InvalidKey),
                                    );
                                }
                                continue;
                            }
                            Err(err) => return Err(err),
                        };
                        if !used_kwargs.contains(either_str.as_cow()?.as_ref()) {
                            match self.var_kwargs_validator {
                                Some(ref validator) => match validator.validate(py, value, extra, slots, recursion_guard) {
                                    Ok(value) => output_kwargs.set_item(either_str.as_py_string(py), value)?,
                                    Err(ValError::LineErrors(line_errors)) => {
                                        for err in line_errors {
                                            errors.push(err.with_outer_location(raw_key.as_loc_item()));
                                        }
                                    }
                                    Err(err) => return Err(err),
                                },
                                None => {
                                    errors.push(ValLineError::new_with_loc(
                                        ErrorType::UnexpectedKeywordArgument,
                                        value,
                                        raw_key.as_loc_item(),
                                    ));
                                }
                            }
                        }
                    }
                }
            }};
        }
        match args {
            GenericArguments::Py(a) => process!(a, py_get_dict_item, py_get, py_slice),
            GenericArguments::Json(a) => process!(a, json_get, json_get, json_slice),
        }
        if !errors.is_empty() {
            Err(ValError::LineErrors(errors))
        } else {
            Ok((PyTuple::new(py, output_args), output_kwargs).to_object(py))
        }
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }
}
