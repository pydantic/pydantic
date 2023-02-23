use std::borrow::Cow;
use std::fmt;
use std::fmt::Write;

use pyo3::exceptions::PyTypeError;
use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyString};

use ahash::AHashMap;

use crate::build_tools::{is_strict, py_err, schema_or_config, SchemaDict};
use crate::errors::{ErrorType, LocItem, ValError, ValLineError, ValResult};
use crate::input::{GenericMapping, Input};
use crate::lookup_key::LookupKey;
use crate::questions::Question;
use crate::recursion_guard::RecursionGuard;

use super::custom_error::CustomError;
use super::{build_validator, BuildContext, BuildValidator, CombinedValidator, Extra, Validator};

#[derive(Debug, Clone)]
pub struct UnionValidator {
    choices: Vec<CombinedValidator>,
    custom_error: Option<CustomError>,
    strict: bool,
    name: String,
}

impl BuildValidator for UnionValidator {
    const EXPECTED_TYPE: &'static str = "union";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        build_context: &mut BuildContext<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let py = schema.py();
        let choices: Vec<CombinedValidator> = schema
            .get_as_req::<&PyList>(intern!(py, "choices"))?
            .iter()
            .map(|choice| build_validator(choice, config, build_context))
            .collect::<PyResult<Vec<CombinedValidator>>>()?;

        let auto_collapse = || schema.get_as_req(intern!(py, "auto_collapse")).unwrap_or(true);
        match choices.len() {
            0 => py_err!("One or more union choices required"),
            1 if auto_collapse() => Ok(choices.into_iter().next().unwrap()),
            _ => {
                let descr = choices.iter().map(|v| v.get_name()).collect::<Vec<_>>().join(",");

                Ok(Self {
                    choices,
                    custom_error: CustomError::build(schema)?,
                    strict: is_strict(schema, config)?,
                    name: format!("{}[{descr}]", Self::EXPECTED_TYPE),
                }
                .into())
            }
        }
    }
}

impl UnionValidator {
    fn or_custom_error<'s, 'data>(
        &'s self,
        errors: Option<Vec<ValLineError<'data>>>,
        input: &'data impl Input<'data>,
    ) -> ValError<'data> {
        if let Some(errors) = errors {
            ValError::LineErrors(errors)
        } else {
            self.custom_error.as_ref().unwrap().as_val_error(input)
        }
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
            let mut errors: Option<Vec<ValLineError>> = match self.custom_error {
                None => Some(Vec::with_capacity(self.choices.len())),
                _ => None,
            };
            let strict_extra = extra.as_strict();

            for validator in &self.choices {
                let line_errors = match validator.validate(py, input, &strict_extra, slots, recursion_guard) {
                    Err(ValError::LineErrors(line_errors)) => line_errors,
                    otherwise => return otherwise,
                };

                if let Some(ref mut errors) = errors {
                    errors.extend(
                        line_errors
                            .into_iter()
                            .map(|err| err.with_outer_location(validator.get_name().into())),
                    );
                }
            }

            Err(self.or_custom_error(errors, input))
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

            let mut errors: Option<Vec<ValLineError>> = match self.custom_error {
                None => Some(Vec::with_capacity(self.choices.len())),
                _ => None,
            };

            // 2nd pass: check if the value can be coerced into one of the Union types, e.g. use validate
            for validator in &self.choices {
                let line_errors = match validator.validate(py, input, extra, slots, recursion_guard) {
                    Err(ValError::LineErrors(line_errors)) => line_errors,
                    success => return success,
                };

                if let Some(ref mut errors) = errors {
                    errors.extend(
                        line_errors
                            .into_iter()
                            .map(|err| err.with_outer_location(validator.get_name().into())),
                    );
                }
            }

            Err(self.or_custom_error(errors, input))
        }
    }

    fn get_name(&self) -> &str {
        &self.name
    }

    fn ask(&self, question: &Question) -> bool {
        self.choices.iter().all(|v| v.ask(question))
    }

    fn complete(&mut self, build_context: &BuildContext<CombinedValidator>) -> PyResult<()> {
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
        } else if let Ok(py_str) = raw.downcast::<PyString>() {
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

#[derive(Debug, Clone, Eq, PartialEq, Hash)]
enum ChoiceKey {
    Int(i64),
    Str(String),
}

impl ChoiceKey {
    fn from_py(raw: &PyAny) -> PyResult<Self> {
        if let Ok(py_int) = raw.extract::<i64>() {
            Ok(Self::Int(py_int))
        } else if let Ok(py_str) = raw.downcast::<PyString>() {
            Ok(Self::Str(py_str.to_str()?.to_string()))
        } else {
            py_err!(PyTypeError; "Expected int or str, got {}", raw.get_type().name().unwrap_or("<unknown python object>"))
        }
    }

    fn repr(&self) -> String {
        match self {
            Self::Int(i) => i.to_string(),
            Self::Str(s) => format!("'{s}'"),
        }
    }
}

impl fmt::Display for ChoiceKey {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Int(i) => write!(f, "{i}"),
            Self::Str(s) => write!(f, "{s}"),
        }
    }
}

impl From<&ChoiceKey> for LocItem {
    fn from(key: &ChoiceKey) -> Self {
        match key {
            ChoiceKey::Str(s) => s.as_str().into(),
            ChoiceKey::Int(i) => (*i).into(),
        }
    }
}

#[derive(Debug, Clone)]
pub struct TaggedUnionValidator {
    choices: AHashMap<ChoiceKey, CombinedValidator>,
    repeat_choices: Option<AHashMap<ChoiceKey, ChoiceKey>>,
    discriminator: Discriminator,
    from_attributes: bool,
    strict: bool,
    custom_error: Option<CustomError>,
    tags_repr: String,
    discriminator_repr: String,
    name: String,
}

impl BuildValidator for TaggedUnionValidator {
    const EXPECTED_TYPE: &'static str = "tagged-union";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        build_context: &mut BuildContext<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let py = schema.py();
        let discriminator = Discriminator::new(py, schema.get_as_req(intern!(py, "discriminator"))?)?;
        let discriminator_repr = discriminator.to_string_py(py)?;

        let schema_choices: &PyDict = schema.get_as_req(intern!(py, "choices"))?;
        let mut choices = AHashMap::with_capacity(schema_choices.len());
        let mut repeat_choices_vec: Vec<(ChoiceKey, ChoiceKey)> = Vec::new();
        let mut first = true;
        let mut tags_repr = String::with_capacity(50);
        let mut descr = String::with_capacity(50);

        for (key, value) in schema_choices {
            let tag = ChoiceKey::from_py(key)?;

            if let Ok(repeat_tag) = ChoiceKey::from_py(value) {
                repeat_choices_vec.push((tag, repeat_tag));
                continue;
            }

            let validator = build_validator(value, config, build_context)?;
            let tag_repr = tag.repr();
            if first {
                first = false;
                write!(tags_repr, "{tag_repr}").unwrap();
                descr.push_str(validator.get_name());
            } else {
                write!(tags_repr, ", {tag_repr}").unwrap();
                // no spaces in get_name() output to make loc easy to read
                write!(descr, ",{}", validator.get_name()).unwrap();
            }
            choices.insert(tag, validator);
        }
        let repeat_choices = if repeat_choices_vec.is_empty() {
            None
        } else {
            let mut wrong_values = Vec::with_capacity(repeat_choices_vec.len());
            let mut repeat_choices = AHashMap::with_capacity(repeat_choices_vec.len());
            for (tag, repeat_tag) in repeat_choices_vec {
                match choices.get(&repeat_tag) {
                    Some(validator) => {
                        let tag_repr = tag.repr();
                        write!(tags_repr, ", {tag_repr}").unwrap();
                        write!(descr, ",{}", validator.get_name()).unwrap();
                        repeat_choices.insert(tag, repeat_tag);
                    }
                    None => wrong_values.push(format!("`{repeat_tag}`")),
                }
            }
            if !wrong_values.is_empty() {
                return py_err!(
                    "String values in choices don't match any keys: {}",
                    wrong_values.join(", ")
                );
            }
            Some(repeat_choices)
        };

        let key = intern!(py, "from_attributes");
        let from_attributes = schema_or_config(schema, config, key, key)?.unwrap_or(true);

        let descr = match discriminator {
            Discriminator::SelfSchema => "self-schema".to_string(),
            _ => descr,
        };

        Ok(Self {
            choices,
            repeat_choices,
            discriminator,
            from_attributes,
            strict: is_strict(schema, config)?,
            custom_error: CustomError::build(schema)?,
            tags_repr,
            discriminator_repr,
            name: format!("{}[{descr}]", Self::EXPECTED_TYPE),
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
                    ($get_method:ident, $($dict:ident),+) => {{
                        // note all these methods return PyResult<Option<(data, data)>>, the outer Err is just for
                        // errors when getting attributes which should be "raised"
                        match lookup_key.$get_method($( $dict ),+)? {
                            Some((_, value)) => {
                                if let Ok(int) = value.validate_int(self.strict) {
                                    Ok(ChoiceKey::Int(int))
                                } else {
                                    Ok(ChoiceKey::Str(value.validate_str(self.strict)?.as_cow()?.as_ref().to_string()))
                                }
                            }
                            None => Err(self.tag_not_found(input)),
                        }
                    }};
                }
                let dict = input.validate_typed_dict(self.strict, self.from_attributes)?;
                let tag = match dict {
                    GenericMapping::PyDict(dict) => find_validator!(py_get_dict_item, dict),
                    GenericMapping::PyGetAttr(obj, kwargs) => find_validator!(py_get_attr, obj, kwargs),
                    GenericMapping::PyMapping(mapping) => find_validator!(py_get_mapping_item, mapping),
                    GenericMapping::JsonObject(mapping) => find_validator!(json_get, mapping),
                }?;
                self.find_call_validator(py, &tag, input, extra, slots, recursion_guard)
            }
            Discriminator::Function(ref func) => {
                let tag = func.call1(py, (input.to_object(py),))?;
                if tag.is_none(py) {
                    Err(self.tag_not_found(input))
                } else {
                    let tag: &PyAny = tag.downcast(py)?;
                    self.find_call_validator(py, &(ChoiceKey::from_py(tag)?), input, extra, slots, recursion_guard)
                }
            }
            Discriminator::SelfSchema => self.find_call_validator(
                py,
                &ChoiceKey::Str(self.self_schema_tag(py, input)?.into_owned()),
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

    fn ask(&self, question: &Question) -> bool {
        self.choices.values().all(|v| v.ask(question))
    }

    fn complete(&mut self, build_context: &BuildContext<CombinedValidator>) -> PyResult<()> {
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
                match mode.as_cow()?.as_ref() {
                    "plain" => Ok(Cow::Borrowed("function-plain")),
                    "wrap" => Ok(Cow::Borrowed("function-wrap")),
                    _ => Ok(Cow::Borrowed("function")),
                }
            } else {
                // tag == "tuple"
                if let Some(mode) = mode {
                    if mode.as_cow()?.as_ref() == "positional" {
                        return Ok(Cow::Borrowed("tuple-positional"));
                    }
                }
                Ok(Cow::Borrowed("tuple-variable"))
            }
        } else {
            Ok(Cow::Owned(tag.to_string()))
        }
    }

    fn find_call_validator<'s, 'data>(
        &'s self,
        py: Python<'data>,
        tag: &ChoiceKey,
        input: &'data impl Input<'data>,
        extra: &Extra,
        slots: &'data [CombinedValidator],
        recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        if let Some(validator) = self.choices.get(tag) {
            return match validator.validate(py, input, extra, slots, recursion_guard) {
                Ok(res) => Ok(res),
                Err(err) => Err(err.with_outer_location(tag.into())),
            };
        } else if let Some(ref repeat_choices) = self.repeat_choices {
            if let Some(choice_tag) = repeat_choices.get(tag) {
                let validator = &self.choices[choice_tag];
                return match validator.validate(py, input, extra, slots, recursion_guard) {
                    Ok(res) => Ok(res),
                    Err(err) => Err(err.with_outer_location(tag.into())),
                };
            }
        }
        match self.custom_error {
            Some(ref custom_error) => Err(custom_error.as_val_error(input)),
            None => Err(ValError::new(
                ErrorType::UnionTagInvalid {
                    discriminator: self.discriminator_repr.clone(),
                    tag: tag.to_string(),
                    expected_tags: self.tags_repr.clone(),
                },
                input,
            )),
        }
    }

    fn tag_not_found<'s, 'data>(&'s self, input: &'data impl Input<'data>) -> ValError<'data> {
        match self.custom_error {
            Some(ref custom_error) => custom_error.as_val_error(input),
            None => ValError::new(
                ErrorType::UnionTagNotFound {
                    discriminator: self.discriminator_repr.clone(),
                },
                input,
            ),
        }
    }
}
