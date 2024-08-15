use std::fmt::Write;
use std::str::FromStr;

use crate::py_gc::PyGcTraverse;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyString, PyTuple};
use pyo3::{intern, PyTraverseError, PyVisit};
use smallvec::SmallVec;

use crate::build_tools::py_schema_err;
use crate::build_tools::{is_strict, schema_or_config};
use crate::common::union::{Discriminator, SMALL_UNION_THRESHOLD};
use crate::errors::{ErrorType, ToErrorValue, ValError, ValLineError, ValResult};
use crate::input::{BorrowInput, Input, ValidatedDict};
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
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let py = schema.py();
        let choices: Vec<(CombinedValidator, Option<String>)> = schema
            .get_as_req::<Bound<'_, PyList>>(intern!(py, "choices"))?
            .iter()
            .map(|choice| {
                let mut label: Option<String> = None;
                let choice = match choice.downcast::<PyTuple>() {
                    Ok(py_tuple) => {
                        let choice = py_tuple.get_item(0)?;
                        label = Some(py_tuple.get_item(1)?.to_string());
                        choice
                    }
                    Err(_) => choice,
                };
                Ok((build_validator(&choice, config, definitions)?, label))
            })
            .collect::<PyResult<Vec<(CombinedValidator, Option<String>)>>>()?;

        let auto_collapse = || schema.get_as_req(intern!(py, "auto_collapse")).unwrap_or(true);
        let mode = schema
            .get_as::<Bound<'_, PyString>>(intern!(py, "mode"))?
            .map_or(Ok(UnionMode::Smart), |mode| mode.to_str().and_then(UnionMode::from_str))?;
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
    fn validate_smart<'py>(
        &self,
        py: Python<'py>,
        input: &(impl Input<'py> + ?Sized),
        state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<PyObject> {
        let old_exactness = state.exactness;
        let old_fields_set_count = state.fields_set_count;

        let strict = state.strict_or(self.strict);
        let mut errors = MaybeErrors::new(self.custom_error.as_ref());

        let mut best_match: Option<(Py<PyAny>, Exactness, Option<usize>)> = None;

        for (choice, label) in &self.choices {
            let state = &mut state.rebind_extra(|extra| {
                if strict {
                    extra.strict = Some(strict);
                }
            });
            state.exactness = Some(Exactness::Exact);
            state.fields_set_count = None;
            let result = choice.validate(py, input, state);
            match result {
                Ok(new_success) => match (state.exactness, state.fields_set_count) {
                    (Some(Exactness::Exact), None) => {
                        // exact match with no fields set data, return immediately
                        return {
                            // exact match, return, restore any previous exactness
                            state.exactness = old_exactness;
                            state.fields_set_count = old_fields_set_count;
                            Ok(new_success)
                        };
                    }
                    _ => {
                        // success should always have an exactness
                        debug_assert_ne!(state.exactness, None);

                        let new_exactness = state.exactness.unwrap_or(Exactness::Lax);
                        let new_fields_set_count = state.fields_set_count;

                        // we use both the exactness and the fields_set_count to determine the best union member match
                        // if fields_set_count is available for the current best match and the new candidate, we use this
                        // as the primary metric. If the new fields_set_count is greater, the new candidate is better.
                        // if the fields_set_count is the same, we use the exactness as a tie breaker to determine the best match.
                        // if the fields_set_count is not available for either the current best match or the new candidate,
                        // we use the exactness to determine the best match.
                        let new_success_is_best_match: bool =
                            best_match
                                .as_ref()
                                .map_or(true, |(_, cur_exactness, cur_fields_set_count)| {
                                    match (*cur_fields_set_count, new_fields_set_count) {
                                        (Some(cur), Some(new)) if cur != new => cur < new,
                                        _ => *cur_exactness < new_exactness,
                                    }
                                });

                        if new_success_is_best_match {
                            best_match = Some((new_success, new_exactness, new_fields_set_count));
                        }
                    }
                },
                Err(ValError::LineErrors(lines)) => {
                    // if we don't yet know this validation will succeed, record the error
                    if best_match.is_none() {
                        errors.push(choice, label.as_deref(), lines);
                    }
                }
                otherwise => return otherwise,
            }
        }

        // restore previous validation state to prepare for any future validations
        state.exactness = old_exactness;
        state.fields_set_count = old_fields_set_count;

        if let Some((best_match, exactness, fields_set_count)) = best_match {
            state.floor_exactness(exactness);
            if let Some(count) = fields_set_count {
                state.add_fields_set(count);
            }
            return Ok(best_match);
        }

        // no matches, build errors
        Err(errors.into_val_error(input))
    }

    fn validate_left_to_right<'py>(
        &self,
        py: Python<'py>,
        input: &(impl Input<'py> + ?Sized),
        state: &mut ValidationState<'_, 'py>,
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
    fn validate<'py>(
        &self,
        py: Python<'py>,
        input: &(impl Input<'py> + ?Sized),
        state: &mut ValidationState<'_, 'py>,
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
    Errors(SmallVec<[ChoiceLineErrors<'a>; SMALL_UNION_THRESHOLD]>),
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

    fn into_val_error(self, input: impl ToErrorValue) -> ValError {
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
                                err.with_outer_location(case_label)
                            })
                        },
                    )
                    .collect(),
            ),
        }
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
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        definitions: &mut DefinitionsBuilder<CombinedValidator>,
    ) -> PyResult<CombinedValidator> {
        let py = schema.py();
        let discriminator = Discriminator::new(py, &schema.get_as_req(intern!(py, "discriminator"))?)?;
        let discriminator_repr = discriminator.to_string_py(py)?;

        let choices = PyDict::new_bound(py);
        let mut tags_repr = String::with_capacity(50);
        let mut descr = String::with_capacity(50);
        let mut first = true;
        let schema_choices: Bound<PyDict> = schema.get_as_req(intern!(py, "choices"))?;
        let mut lookup_map = Vec::with_capacity(choices.len());
        for (choice_key, choice_schema) in schema_choices {
            let validator = build_validator(&choice_schema, config, definitions)?;
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
    fn validate<'py>(
        &self,
        py: Python<'py>,
        input: &(impl Input<'py> + ?Sized),
        state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<PyObject> {
        match &self.discriminator {
            Discriminator::LookupKey(lookup_key) => {
                let from_attributes = state.extra().from_attributes.unwrap_or(self.from_attributes);
                let dict = input.validate_model_fields(self.strict, from_attributes)?;
                // note this methods returns PyResult<Option<(data, data)>>, the outer Err is just for
                // errors when getting attributes which should be "raised"
                let tag = match dict.get_item(lookup_key)? {
                    Some((_, value)) => value,
                    None => return Err(self.tag_not_found(input)),
                };
                self.find_call_validator(py, tag.borrow_input().to_object(py).bind(py), input, state)
            }
            Discriminator::Function(func) => {
                let tag: Py<PyAny> = func.call1(py, (input.to_object(py),))?;
                if tag.is_none(py) {
                    Err(self.tag_not_found(input))
                } else {
                    self.find_call_validator(py, tag.bind(py), input, state)
                }
            }
        }
    }

    fn get_name(&self) -> &str {
        &self.name
    }
}

impl TaggedUnionValidator {
    fn find_call_validator<'py>(
        &self,
        py: Python<'py>,
        tag: &Bound<'py, PyAny>,
        input: &(impl Input<'py> + ?Sized),
        state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<PyObject> {
        if let Ok(Some((tag, validator))) = self.lookup.validate(py, tag) {
            return match validator.validate(py, input, state) {
                Ok(res) => Ok(res),
                Err(err) => Err(err.with_outer_location(tag)),
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

    fn tag_not_found<'py>(&self, input: &(impl Input<'py> + ?Sized)) -> ValError {
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
