use std::fmt::Write;

use pyo3::exceptions::PyKeyError;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

use ahash::AHashMap;

use crate::build_tools::{is_strict, py_error, schema_or_config, SchemaDict};
use crate::errors::{ErrorKind, ValError, ValLineError, ValResult};
use crate::input::{GenericMapping, Input};
use crate::lookup_key::LookupKey;
use crate::recursion_guard::RecursionGuard;

use super::{build_validator, BuildContext, BuildValidator, CombinedValidator, Extra, Validator};

#[derive(Debug, Clone)]
pub struct UnionValidator {
    choices: Vec<CombinedValidator>,
    strict: bool,
    name: String,
}

impl BuildValidator for UnionValidator {
    const EXPECTED_TYPE: &'static str = "union";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        build_context: &mut BuildContext,
    ) -> PyResult<CombinedValidator> {
        let choices: Vec<CombinedValidator> = schema
            .get_as_req::<&PyList>("choices")?
            .iter()
            .map(|choice| build_validator(choice, config, build_context).map(|result| result.0))
            .collect::<PyResult<Vec<CombinedValidator>>>()?;

        let descr = choices.iter().map(|v| v.get_name()).collect::<Vec<_>>().join(",");

        Ok(Self {
            choices,
            strict: is_strict(schema, config)?,
            name: format!("{}[{}]", Self::EXPECTED_TYPE, descr),
        }
        .into())
    }
}

impl Validator for UnionValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        extra: &Extra,
        slots: &'data [CombinedValidator],
        recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        if extra.strict.unwrap_or(self.strict) {
            let mut errors: Vec<ValLineError> = Vec::with_capacity(self.choices.len());
            let strict_strict = extra.as_strict();

            for validator in &self.choices {
                let line_errors = match validator.validate(py, input, &strict_strict, slots, recursion_guard) {
                    Err(ValError::LineErrors(line_errors)) => line_errors,
                    otherwise => return otherwise,
                };

                errors.extend(
                    line_errors
                        .into_iter()
                        .map(|err| err.with_outer_location(validator.get_name().into())),
                );
            }

            Err(ValError::LineErrors(errors))
        } else {
            // 1st pass: check if the value is an exact instance of one of the Union types,
            // e.g. use validate in strict mode
            let strict_strict = extra.as_strict();
            if let Some(res) = self
                .choices
                .iter()
                .map(|validator| validator.validate(py, input, &strict_strict, slots, recursion_guard))
                .find(ValResult::is_ok)
            {
                return res;
            }

            let mut errors: Vec<ValLineError> = Vec::with_capacity(self.choices.len());

            // 2nd pass: check if the value can be coerced into one of the Union types, e.g. use validate
            for validator in &self.choices {
                let line_errors = match validator.validate(py, input, extra, slots, recursion_guard) {
                    Err(ValError::LineErrors(line_errors)) => line_errors,
                    success => return success,
                };

                errors.extend(
                    line_errors
                        .into_iter()
                        .map(|err| err.with_outer_location(validator.get_name().into())),
                );
            }

            Err(ValError::LineErrors(errors))
        }
    }

    fn get_name(&self) -> &str {
        &self.name
    }

    fn complete(&mut self, build_context: &BuildContext) -> PyResult<()> {
        self.choices.iter_mut().try_for_each(|v| v.complete(build_context))
    }
}

#[derive(Debug, Clone)]
pub struct TaggedUnionValidator {
    choices: AHashMap<String, CombinedValidator>,
    lookup_key: LookupKey,
    from_attributes: bool,
    strict: bool,
    tags_repr: String,
    key_repr: String,
    name: String,
}

impl BuildValidator for TaggedUnionValidator {
    const EXPECTED_TYPE: &'static str = "tagged-union";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        build_context: &mut BuildContext,
    ) -> PyResult<CombinedValidator> {
        let py = schema.py();
        let lookup_key = match LookupKey::from_py(py, schema, None, "tag_key")? {
            Some(lookup_key) => lookup_key,
            None => return py_error!(PyKeyError; "'tag_key' or 'tag_keys' must be set on a tagged union"),
        };

        let mut choices = AHashMap::new();
        let mut first = true;
        let mut tags_repr = String::with_capacity(50);
        let mut descr = String::with_capacity(50);

        for item in schema.get_as_req::<&PyDict>("choices")?.items().iter() {
            let tag: String = item.get_item(0)?.extract()?;
            let value = item.get_item(1)?;
            let validator = build_validator(value, config, build_context)?.0;
            if first {
                first = false;
                write!(tags_repr, r#""{}""#, tag).unwrap();
                descr.push_str(validator.get_name());
            } else {
                write!(tags_repr, r#", "{}""#, tag).unwrap();
                // no spaces in get_name() output to make loc easy to read
                write!(descr, ",{}", validator.get_name()).unwrap();
            }
            choices.insert(tag, validator);
        }

        let from_attributes = schema_or_config(schema, config, "from_attributes", "from_attributes")?.unwrap_or(false);
        let key_repr = lookup_key.to_string();

        Ok(Self {
            choices,
            lookup_key,
            from_attributes,
            strict: is_strict(schema, config)?,
            tags_repr,
            key_repr,
            name: format!("{}[{}]", Self::EXPECTED_TYPE, descr),
        }
        .into())
    }
}

impl Validator for TaggedUnionValidator {
    fn validate<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        extra: &Extra,
        slots: &'data [CombinedValidator],
        recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        let dict = input.validate_typed_dict(self.strict, self.from_attributes)?;

        macro_rules! find_validator {
            ($dict:ident, $get_method:ident) => {{
                match self.lookup_key.$get_method($dict)? {
                    Some((_, value)) => {
                        let tag = if self.strict {
                            value.strict_str()?
                        } else {
                            value.lax_str()?
                        };
                        self.choices.get_key_value(tag.as_cow().as_ref())
                    }
                    None => None,
                }
            }};
        }

        // note all these methods return PyResult<Option<(data, data)>>, the outer Err is just for
        // errors when getting attributes which should be "raised"
        let tag_validator: Option<(&String, &CombinedValidator)> = match dict {
            GenericMapping::PyDict(d) => find_validator!(d, py_get_item),
            GenericMapping::PyGetAttr(d) => find_validator!(d, py_get_attr),
            GenericMapping::JsonObject(d) => find_validator!(d, json_get),
        };
        if let Some((tag, validator)) = tag_validator {
            match validator.validate(py, input, extra, slots, recursion_guard) {
                Ok(res) => Ok(res),
                Err(err) => Err(err.with_outer_location(tag.as_str().into())),
            }
        } else {
            Err(ValError::new(
                ErrorKind::UnionTagNotFound {
                    key: self.key_repr.clone(),
                    tags: self.tags_repr.clone(),
                },
                input,
            ))
        }
    }

    fn get_name(&self) -> &str {
        &self.name
    }

    fn complete(&mut self, build_context: &BuildContext) -> PyResult<()> {
        self.choices
            .iter_mut()
            .try_for_each(|(_, validator)| validator.complete(build_context))
    }
}
