use std::borrow::Cow;
use std::fmt::Write;

use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyString};

use ahash::AHashMap;

use crate::build_tools::{is_strict, schema_or_config, SchemaDict};
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
            .get_as_req::<&PyList>(intern!(schema.py(), "choices"))?
            .iter()
            .map(|choice| build_validator(choice, config, build_context))
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
            let strict_extra = extra.as_strict();

            for validator in &self.choices {
                let line_errors = match validator.validate(py, input, &strict_extra, slots, recursion_guard) {
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
            let strict_extra = extra.as_strict();
            if let Some(res) = self
                .choices
                .iter()
                .map(|validator| validator.validate(py, input, &strict_extra, slots, recursion_guard))
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

    fn ask(&self, question: &str) -> bool {
        self.choices.iter().all(|v| v.ask(question))
    }

    fn complete(&mut self, build_context: &BuildContext) -> PyResult<()> {
        self.choices.iter_mut().try_for_each(|v| v.complete(build_context))
    }
}

#[derive(Debug, Clone)]
enum Discriminator {
    /// use `LookupKey` to find the tag, same as we do to find values in typed_dict aliases
    LookupKey(LookupKey),
    /// call a function to find the tag to use
    Function(PyObject),
    /// Custom discriminator specifically for the root `Schema` union in self-schema
    SelfSchema,
}

impl Discriminator {
    fn new(py: Python, raw: &PyAny) -> PyResult<Self> {
        if raw.is_callable() {
            return Ok(Self::Function(raw.to_object(py)));
        } else if let Ok(py_str) = raw.cast_as::<PyString>() {
            if py_str.to_str()? == "self-schema-discriminator" {
                return Ok(Self::SelfSchema);
            }
        }

        let lookup_key = LookupKey::from_py(py, raw, None)?;
        Ok(Self::LookupKey(lookup_key))
    }

    fn to_string_py(&self, py: Python) -> PyResult<String> {
        match self {
            Self::Function(f) => Ok(format!("{}()", f.getattr(py, "__name__")?)),
            Self::LookupKey(lookup_key) => Ok(lookup_key.to_string()),
            Self::SelfSchema => Ok("self-schema".to_string()),
        }
    }
}

#[derive(Debug, Clone)]
pub struct TaggedUnionValidator {
    choices: AHashMap<String, CombinedValidator>,
    discriminator: Discriminator,
    from_attributes: bool,
    strict: bool,
    tags_repr: String,
    discriminator_repr: String,
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
        let discriminator = Discriminator::new(py, schema.get_as_req(intern!(py, "discriminator"))?)?;
        let discriminator_repr = discriminator.to_string_py(py)?;

        let mut choices = AHashMap::new();
        let mut first = true;
        let mut tags_repr = String::with_capacity(50);
        let mut descr = String::with_capacity(50);

        for item in schema.get_as_req::<&PyDict>(intern!(py, "choices"))?.items().iter() {
            let tag: String = item.get_item(0)?.extract()?;
            let value = item.get_item(1)?;
            let validator = build_validator(value, config, build_context)?;
            if first {
                first = false;
                write!(tags_repr, "'{}'", tag).unwrap();
                descr.push_str(validator.get_name());
            } else {
                write!(tags_repr, ", '{}'", tag).unwrap();
                // no spaces in get_name() output to make loc easy to read
                write!(descr, ",{}", validator.get_name()).unwrap();
            }
            choices.insert(tag, validator);
        }

        let key = intern!(py, "from_attributes");
        let from_attributes = schema_or_config(schema, config, key, key)?.unwrap_or(false);

        Ok(Self {
            choices,
            discriminator,
            from_attributes,
            strict: is_strict(schema, config)?,
            tags_repr,
            discriminator_repr,
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
        match self.discriminator {
            Discriminator::LookupKey(ref lookup_key) => {
                macro_rules! find_validator {
                    ($dict:ident, $get_method:ident) => {{
                        // note all these methods return PyResult<Option<(data, data)>>, the outer Err is just for
                        // errors when getting attributes which should be "raised"
                        match lookup_key.$get_method($dict)? {
                            Some((_, value)) => {
                                if self.strict {
                                    value.strict_str()
                                } else {
                                    value.lax_str()
                                }
                            }
                            None => Err(self.tag_not_found(input)),
                        }
                    }};
                }
                let dict = input.validate_typed_dict(self.strict, self.from_attributes)?;
                let tag = match dict {
                    GenericMapping::PyDict(dict) => find_validator!(dict, py_get_item),
                    GenericMapping::PyGetAttr(obj) => find_validator!(obj, py_get_attr),
                    GenericMapping::JsonObject(mapping) => find_validator!(mapping, json_get),
                }?;
                self.find_call_validator(py, tag.as_cow()?, input, extra, slots, recursion_guard)
            }
            Discriminator::Function(ref func) => {
                let tag = func.call1(py, (input.to_object(py),))?;
                if tag.is_none(py) {
                    Err(self.tag_not_found(input))
                } else {
                    let tag: &PyString = tag.cast_as(py)?;
                    self.find_call_validator(py, tag.to_string_lossy(), input, extra, slots, recursion_guard)
                }
            }
            Discriminator::SelfSchema => self.find_call_validator(
                py,
                self.self_schema_tag(py, input)?,
                input,
                extra,
                slots,
                recursion_guard,
            ),
        }
    }

    fn get_name(&self) -> &str {
        &self.name
    }

    fn ask(&self, question: &str) -> bool {
        self.choices.values().all(|v| v.ask(question))
    }

    fn complete(&mut self, build_context: &BuildContext) -> PyResult<()> {
        self.choices
            .iter_mut()
            .try_for_each(|(_, validator)| validator.complete(build_context))
    }
}

impl TaggedUnionValidator {
    fn self_schema_tag<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
    ) -> ValResult<'data, Cow<'data, str>> {
        if input.strict_str().is_ok() {
            // input is a string, must be a bare type
            Ok(Cow::Borrowed("plain-string"))
        } else {
            let dict = input.strict_dict()?;
            let either_tag = match dict {
                GenericMapping::PyDict(dict) => match dict.get_item(intern!(py, "type")) {
                    Some(t) => t.strict_str()?,
                    None => return Err(self.tag_not_found(input)),
                },
                _ => unreachable!(),
            };
            let tag_cow = either_tag.as_cow()?;
            let tag = tag_cow.as_ref();
            // custom logic to distinguish between different function and tuple schemas
            if tag == "function" || tag == "tuple" {
                let mode = match dict {
                    GenericMapping::PyDict(dict) => match dict.get_item(intern!(py, "mode")) {
                        Some(m) => Some(m.strict_str()?),
                        None => None,
                    },
                    _ => unreachable!(),
                };
                if tag == "function" {
                    let mode = mode.ok_or_else(|| self.tag_not_found(input))?;
                    if mode.as_cow()?.as_ref() == "plain" {
                        return Ok(Cow::Borrowed("function-plain"));
                    }
                } else {
                    // tag == "tuple"
                    if let Some(mode) = mode {
                        if mode.as_cow()?.as_ref() == "positional" {
                            return Ok(Cow::Borrowed("tuple-positional"));
                        }
                    }
                    return Ok(Cow::Borrowed("tuple-variable"));
                }
            }
            return Ok(Cow::Owned(tag.to_string()));
        }
    }

    fn find_call_validator<'s, 'data>(
        &'s self,
        py: Python<'data>,
        tag: Cow<str>,
        input: &'data impl Input<'data>,
        extra: &Extra,
        slots: &'data [CombinedValidator],
        recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        if let Some(validator) = self.choices.get(tag.as_ref()) {
            match validator.validate(py, input, extra, slots, recursion_guard) {
                Ok(res) => Ok(res),
                Err(err) => Err(err.with_outer_location(tag.as_ref().into())),
            }
        } else {
            Err(ValError::new(
                ErrorKind::UnionTagInvalid {
                    discriminator: self.discriminator_repr.clone(),
                    tag: tag.to_string(),
                    expected_tags: self.tags_repr.clone(),
                },
                input,
            ))
        }
    }

    fn tag_not_found<'s, 'data>(&'s self, input: &'data impl Input<'data>) -> ValError<'data> {
        ValError::new(
            ErrorKind::UnionTagNotFound {
                discriminator: self.discriminator_repr.clone(),
            },
            input,
        )
    }
}
