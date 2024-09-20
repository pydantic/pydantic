use std::str::FromStr;

use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyString, PyTuple};

use ahash::AHashSet;

use crate::build_tools::py_schema_err;
use crate::build_tools::{schema_or_config_same, ExtraBehavior};
use crate::errors::{ErrorTypeDefaults, ValError, ValLineError, ValResult};
use crate::input::{Arguments, BorrowInput, Input, KeywordArgs, PositionalArgs, ValidationMatch};
use crate::lookup_key::LookupKey;

use crate::tools::SchemaDict;

use super::validation_state::ValidationState;
use super::{build_validator, BuildValidator, CombinedValidator, DefinitionsBuilder, Validator};

#[derive(Debug, PartialEq)]
enum VarKwargsMode {
    Uniform,
    UnpackedTypedDict,
}

impl FromStr for VarKwargsMode {
    type Err = PyErr;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s {
            "uniform" => Ok(Self::Uniform),
            "unpacked-typed-dict" => Ok(Self::UnpackedTypedDict),
            s => py_schema_err!(
                "Invalid var_kwargs mode: `{}`, expected `uniform` or `unpacked-typed-dict`",
                s
            ),
        }
    }
}

#[derive(Debug)]
struct Parameter {
    positional: bool,
    name: String,
    kw_lookup_key: Option<LookupKey>,
    kwarg_key: Option<Py<PyString>>,
    validator: CombinedValidator,
}

#[derive(Debug)]
pub struct ArgumentsValidator {
    parameters: Vec<Parameter>,
    positional_params_count: usize,
    var_args_validator: Option<Box<CombinedValidator>>,
    var_kwargs_mode: VarKwargsMode,
    var_kwargs_validator: Option<Box<CombinedValidator>>,
    loc_by_alias: bool,
    extra: ExtraBehavior,
}

impl BuildValidator for ArgumentsValidator {
    const EXPECTED_TYPE: &'static str = "arguments";

    fn build(
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let py = schema.py();

        let populate_by_name = schema_or_config_same(schema, config, intern!(py, "populate_by_name"))?.unwrap_or(false);

        let arguments_schema: Bound<'_, PyList> = schema.get_as_req(intern!(py, "arguments_schema"))?;
        let mut parameters: Vec<Parameter> = Vec::with_capacity(arguments_schema.len());

        let mut positional_params_count = 0;
        let mut had_default_arg = false;
        let mut had_keyword_only = false;

        for (arg_index, arg) in arguments_schema.iter().enumerate() {
            let arg = arg.downcast::<PyDict>()?;

            let py_name: Bound<PyString> = arg.get_as_req(intern!(py, "name"))?;
            let name = py_name.to_string();
            let mode = arg.get_as::<Bound<'_, PyString>>(intern!(py, "mode"))?;
            let mode = mode
                .as_ref()
                .map(|py_str| py_str.to_str())
                .transpose()?
                .unwrap_or("positional_or_keyword");
            let positional = mode == "positional_only" || mode == "positional_or_keyword";
            if positional {
                positional_params_count = arg_index + 1;
            }

            if mode == "keyword_only" {
                had_keyword_only = true;
            }

            let mut kw_lookup_key = None;
            let mut kwarg_key = None;
            if mode == "keyword_only" || mode == "positional_or_keyword" {
                kw_lookup_key = match arg.get_item(intern!(py, "alias"))? {
                    Some(alias) => {
                        let alt_alias = if populate_by_name { Some(name.as_str()) } else { None };
                        Some(LookupKey::from_py(py, &alias, alt_alias)?)
                    }
                    None => Some(LookupKey::from_string(py, &name)),
                };
                kwarg_key = Some(py_name.into_py(py));
            }

            let schema = arg.get_as_req(intern!(py, "schema"))?;

            let validator = match build_validator(&schema, config, definitions) {
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

            if had_default_arg && !has_default && !had_keyword_only {
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

        let py_var_kwargs_mode: Bound<PyString> = schema
            .get_as(intern!(py, "var_kwargs_mode"))?
            .unwrap_or_else(|| PyString::new_bound(py, "uniform"));

        let var_kwargs_mode = VarKwargsMode::from_str(py_var_kwargs_mode.to_str()?)?;
        let var_kwargs_validator = match schema.get_item(intern!(py, "var_kwargs_schema"))? {
            Some(v) => Some(Box::new(build_validator(&v, config, definitions)?)),
            None => None,
        };

        if var_kwargs_mode == VarKwargsMode::UnpackedTypedDict && var_kwargs_validator.is_none() {
            return py_schema_err!(
                "`var_kwargs_schema` must be specified when `var_kwargs_mode` is `'unpacked-typed-dict'`"
            );
        }

        Ok(Self {
            parameters,
            positional_params_count,
            var_args_validator: match schema.get_item(intern!(py, "var_args_schema"))? {
                Some(v) => Some(Box::new(build_validator(&v, config, definitions)?)),
                None => None,
            },
            var_kwargs_mode,
            var_kwargs_validator,
            loc_by_alias: config.get_as(intern!(py, "loc_by_alias"))?.unwrap_or(true),
            extra: ExtraBehavior::from_schema_or_config(py, schema, config, ExtraBehavior::Forbid)?,
        }
        .into())
    }
}

impl_py_gc_traverse!(Parameter { validator });

impl_py_gc_traverse!(ArgumentsValidator {
    parameters,
    var_args_validator,
    var_kwargs_validator
});

impl Validator for ArgumentsValidator {
    fn validate<'py>(
        &self,
        py: Python<'py>,
        input: &(impl Input<'py> + ?Sized),
        state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<PyObject> {
        let args = input.validate_args()?;

        let mut output_args: Vec<PyObject> = Vec::with_capacity(self.positional_params_count);
        let output_kwargs = PyDict::new_bound(py);
        let mut errors: Vec<ValLineError> = Vec::new();
        let mut used_kwargs: AHashSet<&str> = AHashSet::with_capacity(self.parameters.len());

        // go through arguments getting the value from args or kwargs and validating it
        for (index, parameter) in self.parameters.iter().enumerate() {
            let mut pos_value = None;
            if let Some(args) = args.args() {
                if parameter.positional {
                    pos_value = args.get_item(index);
                }
            }
            let mut kw_value = None;
            if let Some(kwargs) = args.kwargs() {
                if let Some(ref lookup_key) = parameter.kw_lookup_key {
                    if let Some((lookup_path, value)) = kwargs.get_item(lookup_key)? {
                        used_kwargs.insert(lookup_path.first_key());
                        kw_value = Some((lookup_path, value));
                    }
                }
            }

            match (pos_value, kw_value) {
                (Some(_), Some((_, kw_value))) => {
                    errors.push(ValLineError::new_with_loc(
                        ErrorTypeDefaults::MultipleArgumentValues,
                        kw_value.borrow_input(),
                        parameter.name.clone(),
                    ));
                }
                (Some(pos_value), None) => match parameter.validator.validate(py, pos_value.borrow_input(), state) {
                    Ok(value) => output_args.push(value),
                    Err(ValError::LineErrors(line_errors)) => {
                        errors.extend(line_errors.into_iter().map(|err| err.with_outer_location(index)));
                    }
                    Err(err) => return Err(err),
                },
                (None, Some((lookup_path, kw_value))) => {
                    match parameter.validator.validate(py, kw_value.borrow_input(), state) {
                        Ok(value) => output_kwargs.set_item(parameter.kwarg_key.as_ref().unwrap(), value)?,
                        Err(ValError::LineErrors(line_errors)) => {
                            errors.extend(
                                line_errors
                                    .into_iter()
                                    .map(|err| lookup_path.apply_error_loc(err, self.loc_by_alias, &parameter.name)),
                            );
                        }
                        Err(err) => return Err(err),
                    }
                }
                (None, None) => {
                    if let Some(value) = parameter
                        .validator
                        .default_value(py, Some(parameter.name.as_str()), state)?
                    {
                        if let Some(ref kwarg_key) = parameter.kwarg_key {
                            output_kwargs.set_item(kwarg_key, value)?;
                        } else {
                            output_args.push(value);
                        }
                    } else if let Some(ref lookup_key) = parameter.kw_lookup_key {
                        let error_type = if parameter.positional {
                            ErrorTypeDefaults::MissingArgument
                        } else {
                            ErrorTypeDefaults::MissingKeywordOnlyArgument
                        };
                        errors.push(lookup_key.error(error_type, input, self.loc_by_alias, &parameter.name));
                    } else {
                        errors.push(ValLineError::new_with_loc(
                            ErrorTypeDefaults::MissingPositionalOnlyArgument,
                            input,
                            index,
                        ));
                    };
                }
            }
        }
        // if there are args check any where index > positional_params_count since they won't have been checked yet
        if let Some(args) = args.args() {
            let len = args.len();
            if len > self.positional_params_count {
                if let Some(ref validator) = self.var_args_validator {
                    for (index, item) in args.iter().enumerate().skip(self.positional_params_count) {
                        match validator.validate(py, item.borrow_input(), state) {
                            Ok(value) => output_args.push(value),
                            Err(ValError::LineErrors(line_errors)) => {
                                errors.extend(line_errors.into_iter().map(|err| err.with_outer_location(index)));
                            }
                            Err(err) => return Err(err),
                        }
                    }
                } else {
                    for (index, item) in args.iter().enumerate().skip(self.positional_params_count) {
                        errors.push(ValLineError::new_with_loc(
                            ErrorTypeDefaults::UnexpectedPositionalArgument,
                            item,
                            index,
                        ));
                    }
                }
            }
        }

        let remaining_kwargs = PyDict::new_bound(py);

        // if there are kwargs check any that haven't been processed yet
        if let Some(kwargs) = args.kwargs() {
            if kwargs.len() > used_kwargs.len() {
                for result in kwargs.iter() {
                    let (raw_key, value) = result?;
                    let either_str = match raw_key
                        .borrow_input()
                        .validate_str(true, false)
                        .map(ValidationMatch::into_inner)
                    {
                        Ok(k) => k,
                        Err(ValError::LineErrors(line_errors)) => {
                            for err in line_errors {
                                errors.push(
                                    err.with_outer_location(raw_key.clone())
                                        .with_type(ErrorTypeDefaults::InvalidKey),
                                );
                            }
                            continue;
                        }
                        Err(err) => return Err(err),
                    };
                    if !used_kwargs.contains(either_str.as_cow()?.as_ref()) {
                        match self.var_kwargs_mode {
                            VarKwargsMode::Uniform => match &self.var_kwargs_validator {
                                Some(validator) => match validator.validate(py, value.borrow_input(), state) {
                                    Ok(value) => {
                                        output_kwargs
                                            .set_item(either_str.as_py_string(py, state.cache_str()), value)?;
                                    }
                                    Err(ValError::LineErrors(line_errors)) => {
                                        for err in line_errors {
                                            errors.push(err.with_outer_location(raw_key.clone()));
                                        }
                                    }
                                    Err(err) => return Err(err),
                                },
                                None => {
                                    if let ExtraBehavior::Forbid = self.extra {
                                        errors.push(ValLineError::new_with_loc(
                                            ErrorTypeDefaults::UnexpectedKeywordArgument,
                                            value,
                                            raw_key.clone(),
                                        ));
                                    }
                                }
                            },
                            VarKwargsMode::UnpackedTypedDict => {
                                // Save to the remaining kwargs, we will validate as a single dict:
                                remaining_kwargs.set_item(either_str.as_py_string(py, state.cache_str()), value)?;
                            }
                        }
                    }
                }
            }
        }

        if self.var_kwargs_mode == VarKwargsMode::UnpackedTypedDict {
            // `var_kwargs_validator` is guaranteed to be `Some`:
            match self
                .var_kwargs_validator
                .as_ref()
                .unwrap()
                .validate(py, remaining_kwargs.as_any(), state)
            {
                Ok(value) => {
                    output_kwargs.update(value.downcast_bound::<PyDict>(py).unwrap().as_mapping())?;
                }
                Err(ValError::LineErrors(line_errors)) => {
                    errors.extend(line_errors);
                }
                Err(err) => return Err(err),
            }
        }

        if !errors.is_empty() {
            Err(ValError::LineErrors(errors))
        } else {
            Ok((PyTuple::new_bound(py, output_args), output_kwargs).to_object(py))
        }
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }
}
