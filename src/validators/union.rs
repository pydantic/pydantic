use std::fmt::Write;
use std::str::FromStr;

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyString, PyTuple};
use pyo3::{intern, PyTraverseError, PyVisit};
use smallvec::SmallVec;

use crate::build_tools::py_schema_err;
use crate::build_tools::{is_strict, schema_or_config};
use crate::errors::{AsLocItem, ErrorType, ValError, ValLineError, ValResult};
use crate::input::{GenericMapping, Input};
use crate::lookup_key::LookupKey;
use crate::py_gc::PyGcTraverse;
use crate::tools::SchemaDict;

use super::custom_error::CustomError;
use super::literal::LiteralLookup;
use super::{
    build_validator, BuildValidator, CombinedValidator, DefinitionsBuilder, Exactness, ValidationState, Validator,
};

#[derive(Debug)]
enum UnionMode {
    Smart,
    LeftToRight,
}

impl FromStr for UnionMode {
    type Err = PyErr;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s {
            "smart" => Ok(Self::Smart),
            "left_to_right" => Ok(Self::LeftToRight),
            s => py_schema_err!("Invalid union mode: `{}`, expected `smart` or `left_to_right`", s),
        }
    }
}

#[derive(Debug)]
pub struct UnionValidator {
    mode: UnionMode,
    choices: Vec<(CombinedValidator, Option<String>)>,
    custom_error: Option<CustomError>,
    strict: bool,
    name: String,
}

impl BuildValidator for UnionValidator {
    const EXPECTED_TYPE: &'static str = "union";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let py = schema.py();
        let choices: Vec<(CombinedValidator, Option<String>)> = schema
            .get_as_req::<&PyList>(intern!(py, "choices"))?
            .iter()
            .map(|choice| {
                let mut label: Option<String> = None;
                let choice: &PyAny = match choice.downcast::<PyTuple>() {
                    Ok(py_tuple) => {
                        let choice = py_tuple.get_item(0)?;
                        label = Some(py_tuple.get_item(1)?.to_string());
                        choice
                    }
                    Err(_) => choice,
                };
                Ok((build_validator(choice, config, definitions)?, label))
            })
            .collect::<PyResult<Vec<(CombinedValidator, Option<String>)>>>()?;

        let auto_collapse = || schema.get_as_req(intern!(py, "auto_collapse")).unwrap_or(true);
        let mode = schema
            .get_as::<&str>(intern!(py, "mode"))?
            .map_or(Ok(UnionMode::Smart), UnionMode::from_str)?;
        match choices.len() {
            0 => py_schema_err!("One or more union choices required"),
            1 if auto_collapse() => Ok(choices.into_iter().next().unwrap().0),
            _ => {
                let descr = choices
                    .iter()
                    .map(|(choice, label)| label.as_deref().unwrap_or(choice.get_name()))
                    .collect::<Vec<_>>()
                    .join(",");

                Ok(Self {
                    mode,
                    choices,
                    custom_error: CustomError::build(schema, config, definitions)?,
                    strict: is_strict(schema, config)?,
                    name: format!("{}[{descr}]", Self::EXPECTED_TYPE),
                }
                .into())
            }
        }
    }
}

impl UnionValidator {
    fn validate_smart<'data>(
        &self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        state: &mut ValidationState,
    ) -> ValResult<PyObject> {
        let old_exactness = state.exactness;
        let strict = state.strict_or(self.strict);
        let mut errors = MaybeErrors::new(self.custom_error.as_ref());

        let mut success = None;

        for (choice, label) in &self.choices {
            let state = &mut state.rebind_extra(|extra| {
                if strict {
                    extra.strict = Some(strict);
                }
            });
            state.exactness = Some(Exactness::Exact);
            let result = choice.validate(py, input, state);
            match result {
                Ok(new_success) => match state.exactness {
                    // exact match, return
                    Some(Exactness::Exact) => {
                        return {
                            // exact match, return, restore any previous exactness
                            state.exactness = old_exactness;
                            Ok(new_success)
                        };
                    }
                    _ => {
                        // success should always have an exactness
                        debug_assert_ne!(state.exactness, None);
                        let new_exactness = state.exactness.unwrap_or(Exactness::Lax);
                        // if the new result has higher exactness than the current success, replace it
                        if success
                            .as_ref()
                            .map_or(true, |(_, current_exactness)| *current_exactness < new_exactness)
                        {
                            // TODO: is there a possible optimization here, where once there has
                            // been one success, we turn on strict mode, to avoid unnecessary
                            // coercions for further validation?
                            success = Some((new_success, new_exactness));
                        }
                    }
                },
                Err(ValError::LineErrors(lines)) => {
                    // if we don't yet know this validation will succeed, record the error
                    if success.is_none() {
                        errors.push(choice, label.as_deref(), lines);
                    }
                }
                otherwise => return otherwise,
            }
        }
        state.exactness = old_exactness;

        if let Some((success, exactness)) = success {
            state.floor_exactness(exactness);
            return Ok(success);
        }

        // no matches, build errors
        Err(errors.into_val_error(input))
    }

    fn validate_left_to_right<'data>(
        &self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        state: &mut ValidationState,
    ) -> ValResult<PyObject> {
        let mut errors = MaybeErrors::new(self.custom_error.as_ref());

        let mut rebound_state;
        let state = if state.strict_or(self.strict) {
            rebound_state = state.rebind_extra(|extra| extra.strict = Some(true));
            &mut rebound_state
        } else {
            state
        };

        for (validator, label) in &self.choices {
            match validator.validate(py, input, state) {
                Err(ValError::LineErrors(lines)) => errors.push(validator, label.as_deref(), lines),
                otherwise => return otherwise,
            };
        }

        Err(errors.into_val_error(input))
    }
}

impl PyGcTraverse for UnionValidator {
    fn py_gc_traverse(&self, visit: &PyVisit<'_>) -> Result<(), PyTraverseError> {
        self.choices.iter().try_for_each(|(v, _)| v.py_gc_traverse(visit))?;
        Ok(())
    }
}

impl Validator for UnionValidator {
    fn validate<'data>(
        &self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        state: &mut ValidationState,
    ) -> ValResult<PyObject> {
        match self.mode {
            UnionMode::Smart => self.validate_smart(py, input, state),
            UnionMode::LeftToRight => self.validate_left_to_right(py, input, state),
        }
    }

    fn get_name(&self) -> &str {
        &self.name
    }
}

struct ChoiceLineErrors<'a> {
    choice: &'a CombinedValidator,
    label: Option<&'a str>,
    line_errors: Vec<ValLineError>,
}

enum MaybeErrors<'a> {
    Custom(&'a CustomError),
    Errors(SmallVec<[ChoiceLineErrors<'a>; 4]>),
}

impl<'a> MaybeErrors<'a> {
    fn new(custom_error: Option<&'a CustomError>) -> Self {
        match custom_error {
            Some(custom_error) => Self::Custom(custom_error),
            None => Self::Errors(SmallVec::new()),
        }
    }

    fn push(&mut self, choice: &'a CombinedValidator, label: Option<&'a str>, line_errors: Vec<ValLineError>) {
        match self {
            Self::Custom(_) => {}
            Self::Errors(errors) => errors.push(ChoiceLineErrors {
                choice,
                label,
                line_errors,
            }),
        }
    }

    fn into_val_error<'i>(self, input: &impl Input<'i>) -> ValError {
        match self {
            Self::Custom(custom_error) => custom_error.as_val_error(input),
            Self::Errors(errors) => ValError::LineErrors(
                errors
                    .into_iter()
                    .flat_map(
                        |ChoiceLineErrors {
                             choice,
                             label,
                             line_errors,
                         }| {
                            line_errors.into_iter().map(move |err| {
                                let case_label = label.unwrap_or(choice.get_name());
                                err.with_outer_location(case_label.into())
                            })
                        },
                    )
                    .collect(),
            ),
        }
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

impl PyGcTraverse for Discriminator {
    fn py_gc_traverse(&self, visit: &PyVisit<'_>) -> Result<(), PyTraverseError> {
        match self {
            Self::Function(obj) => visit.call(obj)?,
            Self::LookupKey(_) | Self::SelfSchema => {}
        }
        Ok(())
    }
}

#[derive(Debug)]
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
        for (choice_key, choice_schema) in schema_choices {
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

impl_py_gc_traverse!(TaggedUnionValidator { discriminator, lookup });

impl Validator for TaggedUnionValidator {
    fn validate<'data>(
        &self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
        state: &mut ValidationState,
    ) -> ValResult<PyObject> {
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
                let from_attributes = state.extra().from_attributes.unwrap_or(self.from_attributes);
                let dict = input.validate_model_fields(self.strict, from_attributes)?;
                let tag = match dict {
                    GenericMapping::PyDict(dict) => find_validator!(py_get_dict_item, dict),
                    GenericMapping::PyMapping(mapping) => find_validator!(py_get_mapping_item, mapping),
                    GenericMapping::StringMapping(d) => find_validator!(py_get_dict_item, d),
                    GenericMapping::PyGetAttr(obj, kwargs) => find_validator!(py_get_attr, obj, kwargs),
                    GenericMapping::JsonObject(mapping) => find_validator!(json_get, mapping),
                }?;
                self.find_call_validator(py, tag, input, state)
            }
            Discriminator::Function(ref func) => {
                let tag = func.call1(py, (input.to_object(py),))?;
                if tag.is_none(py) {
                    Err(self.tag_not_found(input))
                } else {
                    self.find_call_validator(py, tag.into_ref(py), input, state)
                }
            }
            Discriminator::SelfSchema => {
                self.find_call_validator(py, self.self_schema_tag(py, input)?.as_ref(), input, state)
            }
        }
    }

    fn get_name(&self) -> &str {
        &self.name
    }
}

impl TaggedUnionValidator {
    fn self_schema_tag<'s, 'data>(
        &'s self,
        py: Python<'data>,
        input: &'data impl Input<'data>,
    ) -> ValResult<&'data PyString> {
        let dict = input.strict_dict()?;
        let either_tag = match dict {
            GenericMapping::PyDict(dict) => match dict.get_item(intern!(py, "type"))? {
                Some(t) => t.validate_str(true, false)?.into_inner(),
                None => return Err(self.tag_not_found(input)),
            },
            _ => unreachable!(),
        };
        let tag_cow = either_tag.as_cow()?;
        let tag = tag_cow.as_ref();
        // custom logic to distinguish between different function and tuple schemas
        if tag == "function" {
            let mode = match dict {
                GenericMapping::PyDict(dict) => match dict.get_item(intern!(py, "mode"))? {
                    Some(m) => Some(m.validate_str(true, false)?.into_inner()),
                    None => None,
                },
                _ => unreachable!(),
            };
            let mode = mode.ok_or_else(|| self.tag_not_found(input))?;
            match mode.as_cow()?.as_ref() {
                "plain" => Ok(intern!(py, "function-plain")),
                "wrap" => Ok(intern!(py, "function-wrap")),
                _ => Ok(intern!(py, "function")),
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
        state: &mut ValidationState,
    ) -> ValResult<PyObject> {
        if let Ok(Some((tag, validator))) = self.lookup.validate(py, tag) {
            return match validator.validate(py, input, state) {
                Ok(res) => Ok(res),
                Err(err) => Err(err.with_outer_location(tag.as_loc_item())),
            };
        }
        match self.custom_error {
            Some(ref custom_error) => Err(custom_error.as_val_error(input)),
            None => Err(ValError::new(
                ErrorType::UnionTagInvalid {
                    discriminator: self.discriminator_repr.clone(),
                    tag: tag.to_string(),
                    expected_tags: self.tags_repr.clone(),
                    context: None,
                },
                input,
            )),
        }
    }

    fn tag_not_found<'s, 'data>(&'s self, input: &'data impl Input<'data>) -> ValError {
        match self.custom_error {
            Some(ref custom_error) => custom_error.as_val_error(input),
            None => ValError::new(
                ErrorType::UnionTagNotFound {
                    discriminator: self.discriminator_repr.clone(),
                    context: None,
                },
                input,
            ),
        }
    }
}
