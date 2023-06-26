use std::fmt::Write;

use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyString};

use crate::build_tools::py_schema_err;
use crate::build_tools::{is_strict, schema_or_config};
use crate::errors::{ErrorType, LocItem, ValError, ValLineError, ValResult};
use crate::input::{GenericMapping, Input};
use crate::lookup_key::LookupKey;
use crate::recursion_guard::RecursionGuard;
use crate::tools::SchemaDict;

use super::custom_error::CustomError;
use super::literal::LiteralLookup;
use super::{build_validator, BuildValidator, CombinedValidator, Definitions, DefinitionsBuilder, Extra, Validator};

#[derive(Debug, Clone)]
pub struct UnionValidator {
    choices: Vec<CombinedValidator>,
    custom_error: Option<CustomError>,
    strict: bool,
    name: String,
    strict_required: bool,
    ultra_strict_required: bool,
}

impl BuildValidator for UnionValidator {
    const EXPECTED_TYPE: &'static str = "union";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let py = schema.py();
        let choices: Vec<CombinedValidator> = schema
            .get_as_req::<&PyList>(intern!(py, "choices"))?
            .iter()
            .map(|choice| build_validator(choice, config, definitions))
            .collect::<PyResult<Vec<CombinedValidator>>>()?;

        let auto_collapse = || schema.get_as_req(intern!(py, "auto_collapse")).unwrap_or(true);
        match choices.len() {
            0 => py_schema_err!("One or more union choices required"),
            1 if auto_collapse() => Ok(choices.into_iter().next().unwrap()),
            _ => {
                let descr = choices.iter().map(Validator::get_name).collect::<Vec<_>>().join(",");

                Ok(Self {
                    choices,
                    custom_error: CustomError::build(schema, config, definitions)?,
                    strict: is_strict(schema, config)?,
                    name: format!("{}[{descr}]", Self::EXPECTED_TYPE),
                    strict_required: true,
                    ultra_strict_required: false,
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
        definitions: &'data Definitions<CombinedValidator>,
        recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        if self.ultra_strict_required {
            // do an ultra strict check first
            let ultra_strict_extra = extra.as_strict(true);
            if let Some(res) = self
                .choices
                .iter()
                .map(|validator| validator.validate(py, input, &ultra_strict_extra, definitions, recursion_guard))
                .find(ValResult::is_ok)
            {
                return res;
            }
        }

        if extra.strict.unwrap_or(self.strict) {
            let mut errors: Option<Vec<ValLineError>> = match self.custom_error {
                None => Some(Vec::with_capacity(self.choices.len())),
                _ => None,
            };
            let strict_extra = extra.as_strict(false);

            for validator in &self.choices {
                let line_errors = match validator.validate(py, input, &strict_extra, definitions, recursion_guard) {
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
            if self.strict_required {
                // 1st pass: check if the value is an exact instance of one of the Union types,
                // e.g. use validate in strict mode
                let strict_extra = extra.as_strict(false);
                if let Some(res) = self
                    .choices
                    .iter()
                    .map(|validator| validator.validate(py, input, &strict_extra, definitions, recursion_guard))
                    .find(ValResult::is_ok)
                {
                    return res;
                }
            }

            let mut errors: Option<Vec<ValLineError>> = match self.custom_error {
                None => Some(Vec::with_capacity(self.choices.len())),
                _ => None,
            };

            // 2nd pass: check if the value can be coerced into one of the Union types, e.g. use validate
            for validator in &self.choices {
                let line_errors = match validator.validate(py, input, extra, definitions, recursion_guard) {
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

    fn different_strict_behavior(
        &self,
        definitions: Option<&DefinitionsBuilder<CombinedValidator>>,
        ultra_strict: bool,
    ) -> bool {
        self.choices
            .iter()
            .any(|v| v.different_strict_behavior(definitions, ultra_strict))
    }

    fn get_name(&self) -> &str {
        &self.name
    }

    fn complete(&mut self, definitions: &DefinitionsBuilder<CombinedValidator>) -> PyResult<()> {
        self.choices.iter_mut().try_for_each(|v| v.complete(definitions))?;
        self.strict_required = self.different_strict_behavior(Some(definitions), false);
        self.ultra_strict_required = self.different_strict_behavior(Some(definitions), true);
        Ok(())
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

#[derive(Debug, Clone)]
pub struct TaggedUnionValidator {
    discriminator: Discriminator,
    lookup: LiteralLookup<CombinedValidator>,
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
        definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let py = schema.py();
        let discriminator = Discriminator::new(py, schema.get_as_req(intern!(py, "discriminator"))?)?;
        let discriminator_repr = discriminator.to_string_py(py)?;

        let choices = PyDict::new(py);
        let mut tags_repr = String::with_capacity(50);
        let mut descr = String::with_capacity(50);
        let mut first = true;
        let mut discriminators = Vec::with_capacity(choices.len());
        let schema_choices: &PyDict = schema.get_as_req(intern!(py, "choices"))?;
        let mut lookup_map = Vec::with_capacity(choices.len());
        for (choice_key, choice_schema) in schema_choices.iter() {
            discriminators.push(choice_key);
            let validator = build_validator(choice_schema, config, definitions)?;
            let tag_repr = choice_key.repr()?.to_string();
            if first {
                first = false;
                write!(tags_repr, "{tag_repr}").unwrap();
                descr.push_str(validator.get_name());
            } else {
                write!(tags_repr, ", {tag_repr}").unwrap();
                // no spaces in get_name() output to make loc easy to read
                write!(descr, ",{}", validator.get_name()).unwrap();
            }
            lookup_map.push((choice_key, validator));
        }

        let lookup = LiteralLookup::new(py, lookup_map.into_iter())?;

        let key = intern!(py, "from_attributes");
        let from_attributes = schema_or_config(schema, config, key, key)?.unwrap_or(true);

        let descr = match discriminator {
            Discriminator::SelfSchema => "self-schema".to_string(),
            _ => descr,
        };

        Ok(Self {
            discriminator,
            lookup,
            from_attributes,
            strict: is_strict(schema, config)?,
            custom_error: CustomError::build(schema, config, definitions)?,
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
        definitions: &'data Definitions<CombinedValidator>,
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
                                Ok(value.to_object(py).into_ref(py))
                            }
                            None => Err(self.tag_not_found(input)),
                        }
                    }};
                }
                let from_attributes = extra.from_attributes.unwrap_or(self.from_attributes);
                let dict = input.validate_model_fields(self.strict, from_attributes)?;
                let tag = match dict {
                    GenericMapping::PyDict(dict) => find_validator!(py_get_dict_item, dict),
                    GenericMapping::PyGetAttr(obj, kwargs) => find_validator!(py_get_attr, obj, kwargs),
                    GenericMapping::PyMapping(mapping) => find_validator!(py_get_mapping_item, mapping),
                    GenericMapping::JsonObject(mapping) => find_validator!(json_get, mapping),
                }?;
                self.find_call_validator(py, tag, input, extra, definitions, recursion_guard)
            }
            Discriminator::Function(ref func) => {
                let tag = func.call1(py, (input.to_object(py),))?;
                if tag.is_none(py) {
                    Err(self.tag_not_found(input))
                } else {
                    self.find_call_validator(py, tag.into_ref(py), input, extra, definitions, recursion_guard)
                }
            }
            Discriminator::SelfSchema => self.find_call_validator(
                py,
                self.self_schema_tag(py, input)?.as_ref(),
                input,
                extra,
                definitions,
                recursion_guard,
            ),
        }
    }

    fn different_strict_behavior(
        &self,
        definitions: Option<&DefinitionsBuilder<CombinedValidator>>,
        ultra_strict: bool,
    ) -> bool {
        self.lookup
            .values
            .iter()
            .any(|v| v.different_strict_behavior(definitions, ultra_strict))
    }

    fn get_name(&self) -> &str {
        &self.name
    }

    fn complete(&mut self, definitions: &DefinitionsBuilder<CombinedValidator>) -> PyResult<()> {
        self.lookup
            .values
            .iter_mut()
            .try_for_each(|validator| validator.complete(definitions))
    }
}

impl TaggedUnionValidator {
    fn self_schema_tag<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
    ) -> ValResult<'data, &'data PyString> {
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
                    "plain" => Ok(intern!(py, "function-plain")),
                    "wrap" => Ok(intern!(py, "function-wrap")),
                    _ => Ok(intern!(py, "function")),
                }
            } else {
                // tag == "tuple"
                if let Some(mode) = mode {
                    if mode.as_cow()?.as_ref() == "positional" {
                        return Ok(intern!(py, "tuple-positional"));
                    }
                }
                Ok(intern!(py, "tuple-variable"))
            }
        } else {
            Ok(PyString::new(py, tag))
        }
    }

    fn find_call_validator<'s, 'data>(
        &'s self,
        py: Python<'data>,
        tag: &'data PyAny,
        input: &'data impl Input<'data>,
        extra: &Extra,
        definitions: &'data Definitions<CombinedValidator>,
        recursion_guard: &'s mut RecursionGuard,
    ) -> ValResult<'data, PyObject> {
        if let Ok(Some((tag, validator))) = self.lookup.validate(py, tag) {
            return match validator.validate(py, input, extra, definitions, recursion_guard) {
                Ok(res) => Ok(res),
                Err(err) => Err(err.with_outer_location(LocItem::try_from(tag.to_object(py).into_ref(py))?)),
            };
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
