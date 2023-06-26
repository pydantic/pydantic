use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyString, PyTuple};

use ahash::AHashSet;

use crate::build_tools::py_schema_err;
use crate::build_tools::schema_or_config_same;
use crate::errors::{ErrorType, ValError, ValLineError, ValResult};
use crate::input::{GenericArguments, Input};
use crate::lookup_key::LookupKey;
use crate::recursion_guard::RecursionGuard;
use crate::tools::SchemaDict;

use super::{build_validator, BuildValidator, CombinedValidator, Definitions, DefinitionsBuilder, Extra, Validator};

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
    loc_by_alias: bool,
}

impl BuildValidator for ArgumentsValidator {
    const EXPECTED_TYPE: &'static str = "arguments";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        definitions: &mut DefinitionsBuilder<CombinedValidator>,
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

            let validator = match build_validator(schema, config, definitions) {
                Ok(v) => v,
                Err(err) => return py_schema_err!("Parameter '{}':\n  {}", name, err),
            };

            let has_default = match validator {
                CombinedValidator::WithDefault(ref v) => {
                    if v.omit_on_error() {
                        return py_schema_err!("Parameter '{}': omit_on_error cannot be used with arguments", name);
                    }
                    v.has_default()
                }
                _ => false,
            };

            if had_default_arg && !has_default {
                return py_schema_err!("Non-default argument '{}' follows default argument", name);
            } else if has_default {
                had_default_arg = true;
            }
            parameters.push(Parameter {
                positional,
                name,
                kw_lookup_key,
                kwarg_key,
                validator,
            });
        }

        Ok(Self {
            parameters,
            positional_params_count,
            var_args_validator: match schema.get_item(intern!(py, "var_args_schema")) {
                Some(v) => Some(Box::new(build_validator(v, config, definitions)?)),
                None => None,
            },
            var_kwargs_validator: match schema.get_item(intern!(py, "var_kwargs_schema")) {
                Some(v) => Some(Box::new(build_validator(v, config, definitions)?)),
                None => None,
            },
            loc_by_alias: config.get_as(intern!(py, "loc_by_alias"))?.unwrap_or(true),
        }
        .into())
    }
}

macro_rules! py_get {
    ($obj:ident, $index:ident) => {
        $obj.get_item($index).ok()
    };
}
pub(super) use py_get;

macro_rules! py_slice {
    ($obj:ident, $from:expr, $to:expr) => {
        $obj.get_slice($from, $to)
    };
}
pub(super) use py_slice;

macro_rules! json_get {
    ($obj:ident, $index:ident) => {
        $obj.get($index)
    };
}
pub(super) use json_get;

macro_rules! json_slice {
    ($obj:ident, $from:expr, $to:expr) => {
        $obj[$from..$to]
    };
}
pub(super) use json_slice;

impl Validator for ArgumentsValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        extra: &Extra,
        definitions: &'data Definitions<CombinedValidator>,
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
                            if let Some((lookup_path, value)) = lookup_key.$get_method(kwargs)? {
                                used_kwargs.insert(lookup_path.first_key());
                                kw_value = Some((lookup_path, value));
                            }
                        }
                    }

                    match (pos_value, kw_value) {
                        (Some(_), Some((_, kw_value))) => {
                            errors.push(ValLineError::new_with_loc(
                                ErrorType::MultipleArgumentValues,
                                kw_value,
                                parameter.name.clone(),
                            ));
                        }
                        (Some(pos_value), None) => {
                            match parameter
                                .validator
                                .validate(py, pos_value, extra, definitions, recursion_guard)
                            {
                                Ok(value) => output_args.push(value),
                                Err(ValError::LineErrors(line_errors)) => {
                                    errors.extend(line_errors.into_iter().map(|err| err.with_outer_location(index.into())));
                                }
                                Err(err) => return Err(err),
                            }
                        }
                        (None, Some((lookup_path, kw_value))) => {
                            match parameter
                                .validator
                                .validate(py, kw_value, extra, definitions, recursion_guard)
                            {
                                Ok(value) => output_kwargs.set_item(parameter.kwarg_key.as_ref().unwrap(), value)?,
                                Err(ValError::LineErrors(line_errors)) => {
                                    errors.extend(line_errors.into_iter().map(|err| {
                                        lookup_path.apply_error_loc(err, self.loc_by_alias, &parameter.name)
                                    }));
                                }
                                Err(err) => return Err(err),
                            }
                        }
                        (None, None) => {
                            if let Some(value) = parameter.validator.default_value(py, Some(parameter.name.as_str()), extra, definitions, recursion_guard)? {
                                if let Some(ref kwarg_key) = parameter.kwarg_key {
                                    output_kwargs.set_item(kwarg_key, value)?;
                                } else {
                                    output_args.push(value);
                                }
                            } else if let Some(ref lookup_key) = parameter.kw_lookup_key {
                                let error_type = if parameter.positional {
                                    ErrorType::MissingArgument
                                } else {
                                    ErrorType::MissingKeywordOnlyArgument
                                };
                                errors.push(lookup_key.error(
                                    error_type,
                                    input,
                                    self.loc_by_alias,
                                    &parameter.name,
                                ));
                            } else {
                                errors.push(ValLineError::new_with_loc(ErrorType::MissingPositionalOnlyArgument, input, index));
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
                                match validator.validate(py, item, extra, definitions, recursion_guard) {
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
                    if kwargs.len() > used_kwargs.len() {
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
                                    Some(ref validator) => match validator.validate(py, value, extra, definitions, recursion_guard) {
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

    fn different_strict_behavior(
        &self,
        definitions: Option<&DefinitionsBuilder<CombinedValidator>>,
        ultra_strict: bool,
    ) -> bool {
        self.parameters
            .iter()
            .any(|p| p.validator.different_strict_behavior(definitions, ultra_strict))
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }

    fn complete(&mut self, definitions: &DefinitionsBuilder<CombinedValidator>) -> PyResult<()> {
        self.parameters
            .iter_mut()
            .try_for_each(|parameter| parameter.validator.complete(definitions))?;
        if let Some(v) = &mut self.var_args_validator {
            v.complete(definitions)?;
        }
        if let Some(v) = &mut self.var_kwargs_validator {
            v.complete(definitions)?;
        };
        Ok(())
    }
}
