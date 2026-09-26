use std::sync::Arc;

use ahash::AHashSet;
use jiter::JsonObject;
use jiter::JsonValue;
use jiter::{Jiter, Peek};
use pyo3::IntoPyObjectExt;
use pyo3::exceptions::PyKeyError;
use pyo3::intern;
use pyo3::prelude::*;
use pyo3::pybacked::PyBackedStr;
use pyo3::types::{PyDict, PyList, PySet, PyString, PyType};
use smallvec::SmallVec;

use crate::build_tools::py_schema_err;
use crate::build_tools::{ExtraBehavior, is_strict, schema_or_config_same};
use crate::errors::LocItem;
use crate::errors::{ErrorType, ErrorTypeDefaults, ValError, ValLineError, ValResult};
use crate::input::ConsumeIterator;
use crate::input::{BorrowInput, Input, ValidatedDict, ValidationMatch};
use crate::lookup_key::LookupPath;
use crate::lookup_key::LookupPathCollection;
use crate::lookup_key::LookupType;
use crate::tools::SchemaDict;
use crate::tools::new_py_string;
use crate::validators::shared::lookup_tree::LookupFieldInfo;
use crate::validators::shared::lookup_tree::LookupFieldPriority;
use crate::validators::shared::lookup_tree::LookupTree;

use super::model::{ModelValidator, create_class, set_model_attrs};
use super::validation_state::Exactness;
use super::{BuildValidator, CombinedValidator, DefinitionsBuilder, ValidationState, Validator, build_validator};

#[derive(Debug)]
struct Field {
    name: PyBackedStr,
    lookup_path_collection: LookupPathCollection,
    validator: Arc<CombinedValidator>,
    frozen: bool,
}

impl_py_gc_traverse!(Field { validator });

#[derive(Debug)]
pub struct ModelFieldsValidator {
    fields: Vec<Field>,
    model_name: String,
    extra_behavior: ExtraBehavior,
    extras_validator: Option<Arc<CombinedValidator>>,
    extras_keys_validator: Option<Arc<CombinedValidator>>,
    strict: bool,
    from_attributes: bool,
    loc_by_alias: bool,
    lookup: LookupTree,
    validate_by_alias: Option<bool>,
    validate_by_name: Option<bool>,
}

impl BuildValidator for ModelFieldsValidator {
    const EXPECTED_TYPE: &'static str = "model-fields";

    fn build(
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        definitions: &mut DefinitionsBuilder<Arc<CombinedValidator>>,
    ) -> PyResult<Arc<CombinedValidator>> {
        let py = schema.py();

        let strict = is_strict(schema, config)?;

        let from_attributes = schema_or_config_same(schema, config, intern!(py, "from_attributes"))?.unwrap_or(false);

        let extra_behavior = ExtraBehavior::from_schema_or_config(py, schema, config, ExtraBehavior::Ignore)?;

        let extras_validator = match (schema.get_item(intern!(py, "extras_schema"))?, &extra_behavior) {
            (Some(v), ExtraBehavior::Allow) => Some(build_validator(&v, config, definitions)?),
            (Some(_), _) => return py_schema_err!("extras_schema can only be used if extra_behavior=allow"),
            (_, _) => None,
        };
        let extras_keys_validator = match (schema.get_item(intern!(py, "extras_keys_schema"))?, &extra_behavior) {
            (Some(v), ExtraBehavior::Allow) => Some(build_validator(&v, config, definitions)?),
            (Some(_), _) => return py_schema_err!("extras_keys_schema can only be used if extra_behavior=allow"),
            (_, _) => None,
        };
        let model_name: String = schema
            .get_as(intern!(py, "model_name"))?
            .unwrap_or_else(|| "Model".to_string());

        let fields_dict: Bound<'_, PyDict> = schema.get_as_req(intern!(py, "fields"))?;
        let mut fields: Vec<Field> = Vec::with_capacity(fields_dict.len());

        for (key, value) in fields_dict {
            let field_info = value.cast::<PyDict>()?;
            let name: PyBackedStr = key.extract()?;

            let schema = field_info.get_as_req(intern!(py, "schema"))?;

            let validator = match build_validator(&schema, config, definitions) {
                Ok(v) => v,
                Err(err) => return py_schema_err!("Field \"{name}\":\n  {err}"),
            };

            let validation_alias = field_info.get_as(intern!(py, "validation_alias"))?;
            let lookup_path_collection = LookupPathCollection::new(validation_alias, name.clone())?;

            fields.push(Field {
                name,
                lookup_path_collection,
                validator,
                frozen: field_info.get_as::<bool>(intern!(py, "frozen"))?.unwrap_or(false),
            });
        }

        let lookup = LookupTree::from_fields(&fields, |field| &field.lookup_path_collection);

        Ok(CombinedValidator::ModelFields(Self {
            fields,
            model_name,
            extra_behavior,
            extras_validator,
            extras_keys_validator,
            strict,
            from_attributes,
            loc_by_alias: config.get_as(intern!(py, "loc_by_alias"))?.unwrap_or(true),
            lookup,
            validate_by_alias: config.get_as(intern!(py, "validate_by_alias"))?,
            validate_by_name: config.get_as(intern!(py, "validate_by_name"))?,
        })
        .into())
    }
}

impl_py_gc_traverse!(ModelFieldsValidator {
    fields,
    extras_validator
});

impl Validator for ModelFieldsValidator {
    fn validate<'py>(
        &self,
        py: Python<'py>,
        input: &(impl Input<'py> + ?Sized),
        state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<Py<PyAny>> {
        // this validator does not yet support partial validation, disable it to avoid incorrect results
        state.allow_partial = false.into();

        let strict = state.strict_or(self.strict);
        let extra_behavior = state.extra_behavior_or(self.extra_behavior);
        let from_attributes = state.extra().from_attributes.unwrap_or(self.from_attributes);

        let (model_dict, mut model_extra_dict_op, fields_set) = if let Some(json_input) = input.as_json() {
            let JsonValue::Object(json_object) = json_input else {
                return Err(ValError::new(
                    ErrorType::ModelType {
                        context: None,
                        class_name: self.model_name.clone(),
                    },
                    input,
                ));
            };
            self.validate_json_by_iteration(py, json_input, json_object, state)?
        } else {
            // we convert the DictType error to a ModelType error
            let dict = match input.validate_model_fields(strict, from_attributes) {
                Ok(d) => d,
                Err(ValError::LineErrors(errors)) => {
                    let errors: Vec<ValLineError> = errors
                        .into_iter()
                        .map(|e| match e.error_type {
                            ErrorType::DictType { .. } => {
                                let mut e = e;
                                e.error_type = ErrorType::ModelType {
                                    class_name: self.model_name.clone(),
                                    context: None,
                                };
                                e
                            }
                            _ => e,
                        })
                        .collect();
                    return Err(ValError::LineErrors(errors));
                }
                Err(err) => return Err(err),
            };
            self.validate_by_get_item(py, input, dict, state)?
        };

        // if we have extra=allow, but we didn't create a dict because we were validating
        // from attributes, set it now so __pydantic_extra__ is always a dict if extra=allow
        if matches!(extra_behavior, ExtraBehavior::Allow) && model_extra_dict_op.is_none() {
            model_extra_dict_op = Some(PyDict::new(py));
        }

        Ok((model_dict, model_extra_dict_op, fields_set).into_py_any(py)?)
    }

    fn validate_assignment<'py>(
        &self,
        py: Python<'py>,
        obj: &Bound<'py, PyAny>,
        field_name: &PyBackedStr,
        field_value: &Bound<'py, PyAny>,
        state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<Py<PyAny>> {
        let dict = obj.cast::<PyDict>()?;
        let extra_behavior = state.extra_behavior_or(self.extra_behavior);

        let get_updated_dict = |output: &Bound<'py, PyAny>| {
            dict.set_item(field_name, output)?;
            Ok(dict)
        };

        let prepare_result = |result: ValResult<Py<PyAny>>| match result {
            Ok(output) => get_updated_dict(&output.into_bound(py)),
            Err(ValError::LineErrors(line_errors)) => {
                let errors = line_errors
                    .into_iter()
                    .map(|e| e.with_outer_location(field_name.clone()))
                    .collect();
                Err(ValError::LineErrors(errors))
            }
            Err(err) => Err(err),
        };

        // by using dict but removing the field in question, we match V1 behaviour
        let data_dict = dict.copy()?;
        if let Err(err) = data_dict.del_item(field_name) {
            // KeyError is fine here as the field might not be in the dict
            if !err.get_type(py).is(PyType::new::<PyKeyError>(py)) {
                return Err(err.into());
            }
        }

        let new_data = {
            let state = &mut state.scoped_set_data(Some(data_dict));

            if let Some(field) = self.fields.iter().find(|f| &*f.name == field_name) {
                if field.frozen {
                    return Err(ValError::new_with_loc(
                        ErrorTypeDefaults::FrozenField,
                        field_value,
                        &*field.name,
                    ));
                }

                let state = &mut state.scoped_set_field_name(Some(field.name.as_py_str().bind(py).clone()));

                prepare_result(field.validator.validate(py, field_value, state))?
            } else {
                // Handle extra (unknown) field
                // We partially use the extra_behavior for initialization / validation
                // to determine how to handle assignment
                // For models / typed dicts we forbid assigning extra attributes
                // unless the user explicitly set extra_behavior to 'allow'
                match extra_behavior {
                    ExtraBehavior::Allow => match self.extras_validator {
                        Some(ref validator) => prepare_result(validator.validate(py, field_value, state))?,
                        None => get_updated_dict(field_value)?,
                    },
                    ExtraBehavior::Forbid | ExtraBehavior::Ignore => {
                        return Err(ValError::new_with_loc(
                            ErrorType::NoSuchAttribute {
                                attribute: field_name.to_string(),
                                context: None,
                            },
                            field_value,
                            field_name.to_string(),
                        ));
                    }
                }
            }
        };

        let new_extra = match &extra_behavior {
            ExtraBehavior::Allow => {
                let non_extra_data = PyDict::new(py);
                self.fields.iter().try_for_each(|f| -> PyResult<()> {
                    let Some(popped_value) = new_data.get_item(&f.name)? else {
                        // field not present in __dict__ for some reason; let the rest of the
                        // validation pipeline handle it later
                        return Ok(());
                    };
                    new_data.del_item(&f.name)?;
                    non_extra_data.set_item(&f.name, popped_value)?;
                    Ok(())
                })?;
                let new_extra = new_data.copy()?;
                new_data.clear();
                new_data.update(non_extra_data.as_mapping())?;
                new_extra.into()
            }
            _ => py.None(),
        };

        let fields_set = PySet::new(py, &[field_name.to_string()])?;
        Ok((new_data, new_extra, fields_set).into_py_any(py)?)
    }

    fn get_name(&self) -> &str {
        Self::EXPECTED_TYPE
    }
}

/// Why the fast path stopped: the cursor hit something it will not handle, in which case the
/// caller falls back, or python raised, which the caller passes on.
pub(crate) enum StreamStop {
    Cursor,
    Py(PyErr),
}

impl From<jiter::JiterError> for StreamStop {
    fn from(_: jiter::JiterError) -> Self {
        Self::Cursor
    }
}

impl From<PyErr> for StreamStop {
    fn from(err: PyErr) -> Self {
        Self::Py(err)
    }
}

impl From<std::convert::Infallible> for StreamStop {
    fn from(err: std::convert::Infallible) -> Self {
        match err {}
    }
}

/// A field whose value can be taken straight off the cursor when the json type matches it exactly.
/// In that case strict and lax agree and no validator has to run.
pub(crate) enum Fast<'v> {
    Str,
    Bool,
    Int,
    Float,
    /// a nested model, whose own fields come off the same cursor
    Model(Box<NestedModel<'v>>),
    /// an array whose elements all come off the cursor the same way, to any depth
    List(Box<ContainerPlan<'v>>),
    /// an object with string keys whose values all come off the cursor the same way
    Dict(Box<ContainerPlan<'v>>),
    No,
}

/// One field's plan: how to take its value, and whether null is also an answer for it.
pub(crate) struct FieldPlan<'v> {
    fast: Fast<'v>,
    nullable: bool,
}

/// A container's plan: how to take each element, and the length the result has to have.
pub(crate) struct ContainerPlan<'v> {
    element: FieldPlan<'v>,
    min_length: Option<usize>,
    max_length: Option<usize>,
}

impl ContainerPlan<'_> {
    /// Whether a container of this length is one the caller can keep.
    fn length_ok(&self, len: usize) -> bool {
        self.min_length.is_none_or(|min| len >= min) && self.max_length.is_none_or(|max| len <= max)
    }
}

/// How many fields a model can have before its slots go to the heap. A model is read once per
/// object, so the allocation is per object, not per document; the array sits in a stack frame
/// that recurses only as deep as the plan allows.
const SLOTS_ON_STACK: usize = 16;

/// One model's plan.
pub(crate) struct ModelPlan<'v> {
    fields: Vec<FieldPlan<'v>>,
    /// no field has an alias, so every key belongs to at most one field and the alias priority
    /// rule cannot come into it
    names_only: bool,
    /// an unknown key is an error the ordinary path has to report, so the object goes back to it
    forbid_extra: bool,
}

/// What it takes to build one nested model without leaving the cursor.
pub(crate) struct NestedModel<'v> {
    class: &'v Py<PyType>,
    fields: &'v ModelFieldsValidator,
    plan: ModelPlan<'v>,
}

/// How far down the plan follows nested models. A self-referential schema would otherwise plan
/// forever, and each level down accounts for less of the document than the one above it.
const MAX_PLAN_DEPTH: u8 = 4;

/// A validator that a model class already had built is reused through a `Prebuilt` wrapper
/// which only delegates, and real pydantic schemas are made almost entirely of them.
pub(crate) fn unwrap_prebuilt(validator: &CombinedValidator) -> &CombinedValidator {
    let mut current = validator;
    while let CombinedValidator::Prebuilt(prebuilt) = current {
        current = prebuilt.stream_inner();
    }
    current
}

fn classify(validator: &CombinedValidator, depth: u8) -> FieldPlan<'_> {
    match unwrap_prebuilt(validator) {
        // null is an answer for the field however the rest of it is validated
        CombinedValidator::Nullable(nullable) => FieldPlan {
            nullable: true,
            ..classify(nullable.stream_inner(), depth)
        },
        // a field that is present is validated by the inner validator alone
        CombinedValidator::WithDefault(with_default) => classify(with_default.stream_inner(), depth),
        _ => FieldPlan {
            fast: classify_fast(validator, depth),
            nullable: false,
        },
    }
}

fn classify_fast(validator: &CombinedValidator, depth: u8) -> Fast<'_> {
    match unwrap_prebuilt(validator) {
        CombinedValidator::Str(_) => Fast::Str,
        CombinedValidator::Bool(_) => Fast::Bool,
        CombinedValidator::Int(_) => Fast::Int,
        CombinedValidator::Float(_) => Fast::Float,
        // a container's element plan does not raise the depth: only a model can recurse, and
        // `list[list[list[float]]]` is a real shape that a depth cap would refuse for no reason
        CombinedValidator::List(list) => match list.stream_list() {
            // `fail_fast` only decides how errors are collected, and a streamed list that
            // produces any error is handed back whole, so it makes no difference here
            Some(list) => match container_plan(list.items, list.min_length, list.max_length, depth) {
                Some(plan) => Fast::List(Box::new(plan)),
                None => Fast::No,
            },
            None => Fast::No,
        },
        CombinedValidator::Dict(dict) => match dict.stream_str_values() {
            Some((values, min, max)) => match container_plan(values, min, max, depth) {
                Some(plan) => Fast::Dict(Box::new(plan)),
                None => Fast::No,
            },
            None => Fast::No,
        },
        CombinedValidator::Model(model) if depth < MAX_PLAN_DEPTH => match nested_model(model, depth) {
            Some(nested) => Fast::Model(Box::new(nested)),
            None => Fast::No,
        },
        _ => Fast::No,
    }
}

fn container_plan(
    element: &CombinedValidator,
    min_length: Option<usize>,
    max_length: Option<usize>,
    depth: u8,
) -> Option<ContainerPlan<'_>> {
    let element = classify(element, depth);
    if matches!(element.fast, Fast::No) {
        return None;
    }
    Some(ContainerPlan {
        element,
        min_length,
        max_length,
    })
}

fn nested_model(model: &ModelValidator, depth: u8) -> Option<NestedModel<'_>> {
    let (class, inner) = model.stream_parts()?;
    let CombinedValidator::ModelFields(fields) = &**inner else {
        return None;
    };
    Some(NestedModel {
        class,
        fields,
        plan: fields.stream_plan_at(depth + 1)?,
    })
}

/// What came off the cursor for one field.
enum Taken<'j, 'py> {
    /// the json type matched the field exactly, so this is already the answer
    Ready(Bound<'py, PyAny>),
    /// not an exact match, so the field's own validator has to see it
    Raw(JsonValue<'j>),
}

/// One model instance from the cursor, or `None` if its object could not be finished. Either way
/// the object has been consumed.
fn build_model<'py>(
    py: Python<'py>,
    nested: &NestedModel<'_>,
    jiter: &mut Jiter<'_>,
    state: &mut ValidationState<'_, 'py>,
) -> Result<Option<Bound<'py, PyAny>>, StreamStop> {
    // constructing a model is never an exact match, exactly as the ordinary path has it
    state.floor_exactness(Exactness::Strict);
    let Some((model_dict, _extra, fields_set)) =
        nested.fields.validate_json_streaming(py, jiter, &nested.plan, state)?
    else {
        return Ok(None);
    };
    let instance = create_class(nested.class.bind(py))?;
    let none = py.None();
    set_model_attrs(&instance, &model_dict, none.bind(py), &fields_set)?;
    Ok(Some(instance))
}

/// A plan for a whole document, for a root the model shapes do not cover.
pub(crate) fn root_plan(validator: &CombinedValidator) -> Option<FieldPlan<'_>> {
    let plan = classify(validator, 0);
    (!matches!(plan.fast, Fast::No)).then_some(plan)
}

/// One whole document off the cursor, or `None` if the cursor could not finish it.
pub(crate) fn take_root<'py>(
    py: Python<'py>,
    jiter: &mut Jiter<'_>,
    plan: &FieldPlan<'_>,
    state: &mut ValidationState<'_, 'py>,
) -> Result<Option<Bound<'py, PyAny>>, StreamStop> {
    match take_fast(py, jiter, plan, state)? {
        Taken::Ready(value) => Ok(Some(value)),
        Taken::Raw(_) => Ok(None),
    }
}

/// An array, every element taken the same way. If any element is not something the cursor can
/// finish, the array is handed back whole: by then part of it is already python objects, so it
/// cannot be assembled from both halves.
#[inline(never)]
fn take_list<'j, 'py>(
    py: Python<'py>,
    jiter: &mut Jiter<'j>,
    plan: &ContainerPlan<'_>,
    state: &mut ValidationState<'_, 'py>,
) -> Result<Taken<'j, 'py>, StreamStop> {
    let element = &plan.element;
    let start = jiter.current_index();
    // collected first so the list is allocated once at its final size: appending into an empty
    // list over-allocates and then reallocates, which is most of what a short list costs
    let mut items: SmallVec<[Bound<'py, PyAny>; 8]> = SmallVec::new();
    let mut all_ready = true;
    let mut next = jiter.known_array()?;
    while let Some(peek) = next {
        if all_ready {
            match take_peeked(py, jiter, element, peek, state)? {
                Taken::Ready(value) => items.push(value),
                Taken::Raw(_) => all_ready = false,
            }
        } else {
            // consume the rest so the object around it can carry on
            jiter.known_skip(peek)?;
        }
        next = jiter.array_step()?;
    }
    if all_ready && plan.length_ok(items.len()) {
        Ok(Taken::Ready(PyList::new(py, items)?.into_any()))
    } else {
        Ok(Taken::Raw(reread(jiter, start)?))
    }
}

/// An object with string keys, every value taken the same way. Json keys are always strings, so
/// the key validator has nothing to check.
#[inline(never)]
fn take_dict<'j, 'py>(
    py: Python<'py>,
    jiter: &mut Jiter<'j>,
    plan: &ContainerPlan<'_>,
    state: &mut ValidationState<'_, 'py>,
) -> Result<Taken<'j, 'py>, StreamStop> {
    let value_plan = &plan.element;
    let start = jiter.current_index();
    let dict = PyDict::new(py);
    let mut all_ready = true;
    let mut key = jiter.known_object()?;
    while let Some(k) = key {
        if all_ready {
            // the key borrows the cursor, so it has to become a python string before the value
            // is read
            let k = new_py_string(py, k, state.cache_str());
            match take_fast(py, jiter, value_plan, state)? {
                Taken::Ready(value) => dict.set_item(k, value)?,
                Taken::Raw(_) => all_ready = false,
            }
        } else {
            jiter.next_skip()?;
        }
        key = jiter.next_key()?;
    }
    // a json object can repeat a key, so the dict may be shorter than the members read
    if all_ready && plan.length_ok(dict.len()) {
        Ok(Taken::Ready(dict.into_any()))
    } else {
        Ok(Taken::Raw(reread(jiter, start)?))
    }
}

/// The value just consumed, read again from its own bytes, so that the field's own validator
/// sees exactly what the ordinary path would have seen.
fn reread<'j>(jiter: &Jiter<'j>, start: usize) -> Result<JsonValue<'j>, StreamStop> {
    JsonValue::parse(jiter.slice_to_current(start), true).map_err(|_| StreamStop::Cursor)
}

/// Take one value off the cursor, as a python object where the json type matches the field
/// exactly and as json otherwise. The value is always consumed, so the caller carries on reading
/// keys either way.
fn take_fast<'j, 'py>(
    py: Python<'py>,
    jiter: &mut Jiter<'j>,
    field: &FieldPlan<'_>,
    state: &mut ValidationState<'_, 'py>,
) -> Result<Taken<'j, 'py>, StreamStop> {
    let peek = jiter.peek()?;
    take_peeked(py, jiter, field, peek, state)
}

/// The same, for a value whose peek the caller already has: an element of an array, or the value
/// of an object member.
fn take_peeked<'j, 'py>(
    py: Python<'py>,
    jiter: &mut Jiter<'j>,
    field: &FieldPlan<'_>,
    peek: Peek,
    state: &mut ValidationState<'_, 'py>,
) -> Result<Taken<'j, 'py>, StreamStop> {
    if field.nullable && matches!(peek, Peek::Null) {
        jiter.known_null()?;
        return Ok(Taken::Ready(py.None().into_bound(py)));
    }
    let fast = &field.fast;
    let scalar = !matches!(
        peek,
        Peek::String | Peek::Array | Peek::Object | Peek::Null | Peek::True | Peek::False
    );
    let value = match (fast, peek) {
        (Fast::Str, Peek::String) => {
            let s = jiter.known_str()?;
            Taken::Ready(new_py_string(py, s, state.cache_str()).into_any())
        }
        (Fast::Bool, Peek::True | Peek::False) => {
            let b = jiter.known_bool(peek)?;
            Taken::Ready(pyo3::types::PyBool::new(py, b).to_owned().into_any())
        }
        (Fast::Int | Fast::Float, _) if scalar => {
            let number = jiter.known_number(peek)?;
            match (fast, number) {
                (Fast::Int, jiter::NumberAny::Int(jiter::NumberInt::Int(i))) => {
                    Taken::Ready(i.into_pyobject(py)?.into_any())
                }
                (Fast::Float, jiter::NumberAny::Float(f)) if f.is_finite() => {
                    Taken::Ready(f.into_pyobject(py)?.into_any())
                }
                // a json int is a valid float under both strict and lax, and the conversion is the
                // one the float validator would do; without this a single `-128` among the decimals
                // hands back the whole array it sits in
                (Fast::Float, jiter::NumberAny::Int(jiter::NumberInt::Int(i))) => {
                    Taken::Ready((i as f64).into_pyobject(py)?.into_any())
                }
                // a float or bigint for an int field, or a non-finite float
                (_, jiter::NumberAny::Int(jiter::NumberInt::Int(i))) => Taken::Raw(JsonValue::Int(i)),
                (_, jiter::NumberAny::Float(f)) => Taken::Raw(JsonValue::Float(f)),
                (_, jiter::NumberAny::Int(jiter::NumberInt::BigInt(b))) => Taken::Raw(JsonValue::BigInt(b)),
            }
        }
        (Fast::List(plan), Peek::Array) => take_list(py, jiter, plan, state)?,
        (Fast::Dict(plan), Peek::Object) => take_dict(py, jiter, plan, state)?,
        (Fast::Model(nested), Peek::Object) => {
            let start = jiter.current_index();
            match build_model(py, nested, jiter, state)? {
                Some(instance) => Taken::Ready(instance),
                None => Taken::Raw(reread(jiter, start)?),
            }
        }
        // a field this path does not specialise, or a json type that does not match it: hand the
        // value to the field's own validator rather than giving up on the whole object
        _ => Taken::Raw(jiter.next_value()?),
    };
    Ok(value)
}

type ValidatedModelFields<'py> = (Bound<'py, PyDict>, Option<Bound<'py, PyDict>>, Bound<'py, PySet>);

impl ModelFieldsValidator {
    fn validate_by_get_item<'py>(
        &self,
        py: Python<'py>,
        input: &(impl Input<'py> + ?Sized),
        dict: impl ValidatedDict<'py>,
        state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<ValidatedModelFields<'py>> {
        let extra_behavior = state.extra_behavior_or(self.extra_behavior);
        let model_dict = PyDict::new(py);
        let mut model_extra_dict_op: Option<Bound<PyDict>> = None;
        let mut errors: Vec<ValLineError> = Vec::with_capacity(self.fields.len());
        let mut fields_set_vec = Vec::with_capacity(self.fields.len());
        let mut fields_set_count: usize = 0;

        let validate_by_alias = state.validate_by_alias_or(self.validate_by_alias);
        let validate_by_name = state.validate_by_name_or(self.validate_by_name);
        let lookup_type = LookupType::from_bools(validate_by_alias, validate_by_name)?;

        // we only care about which keys have been used if we're iterating over the object for extra after
        // the first pass
        let mut used_keys: Option<AHashSet<&str>> = if extra_behavior == ExtraBehavior::Ignore || dict.is_py_get_attr()
        {
            None
        } else {
            Some(AHashSet::with_capacity(self.fields.len()))
        };

        {
            let state = &mut state.scoped_set_data(Some(model_dict.clone()));
            let state = &mut state.scoped_clear_field_error();

            for field in &self.fields {
                let state = &mut state.scoped_set_field_name(Some(field.name.as_py_str().bind(py).clone()));

                if let Some((lookup_path, lookup_result)) = field
                    .lookup_path_collection
                    .lookup_paths(lookup_type)
                    .find_map(|path| Some((path, dict.get_item(path).transpose()?)))
                {
                    let value = match lookup_result {
                        Ok(value) => value,
                        Err(ValError::LineErrors(line_errors)) => {
                            for err in line_errors {
                                errors.push(err.with_outer_location(field.name.clone()));
                            }
                            continue;
                        }
                        Err(e) => {
                            return Err(e);
                        }
                    };

                    if let Some(ref mut used_keys) = used_keys {
                        // key is "used" whether or not validation passes, since we want to skip this key in
                        // extra logic either way
                        used_keys.insert(lookup_path.first_key());
                    }

                    match field.validator.validate(py, value.borrow_input(), state) {
                        Ok(value) => {
                            model_dict.set_item(&field.name, value)?;
                            fields_set_vec.push(field.name.clone());
                            fields_set_count += 1;
                        }
                        Err(e) => {
                            state.has_field_error = true;
                            match e {
                                ValError::Omit => continue,
                                ValError::LineErrors(line_errors) => {
                                    for err in line_errors {
                                        errors.push(lookup_path.apply_error_loc(err, self.loc_by_alias, &field.name));
                                    }
                                }
                                err => return Err(err),
                            }
                        }
                    }
                    continue;
                }

                match field.validator.default_value(py, Some(field.name.clone()), state) {
                    Ok(Some(value)) => {
                        // Default value exists, and passed validation if required
                        model_dict.set_item(&field.name, value)?;
                    }
                    Ok(None) => {
                        // There was no default value
                        state.has_field_error = true;
                        let error_type = ErrorTypeDefaults::Missing;
                        let error_loc = field.lookup_path_collection.error_loc(lookup_type, self.loc_by_alias);
                        errors.push(ValLineError::new_with_full_loc(error_type, input, error_loc));
                    }
                    Err(ValError::Omit) => {}
                    Err(ValError::LineErrors(line_errors)) => {
                        state.has_field_error = true;
                        for err in line_errors {
                            // Note: this will always use the field name even if there is an alias
                            // However, we don't mind so much because this error can only happen if the
                            // default value fails validation, which is arguably a developer error.
                            // We could try to "fix" this in the future if desired.
                            errors.push(err);
                        }
                    }
                    Err(err) => return Err(err),
                }
            }
        }

        if let Some(used_keys) = used_keys {
            struct ValidateToModelExtra<'a, 's, 'py> {
                py: Python<'py>,
                used_keys: AHashSet<&'a str>,
                errors: &'a mut Vec<ValLineError>,
                fields_set_vec: &'a mut Vec<PyBackedStr>,
                extra_behavior: ExtraBehavior,
                extras_validator: Option<&'a CombinedValidator>,
                extras_keys_validator: Option<&'a CombinedValidator>,
                state: &'a mut ValidationState<'s, 'py>,
            }

            impl<'py, Key, Value> ConsumeIterator<ValResult<(Key, Value)>> for ValidateToModelExtra<'_, '_, 'py>
            where
                Key: BorrowInput<'py> + Clone + Into<LocItem>,
                Value: BorrowInput<'py>,
            {
                type Output = ValResult<Bound<'py, PyDict>>;
                fn consume_iterator(
                    self,
                    iterator: impl Iterator<Item = ValResult<(Key, Value)>>,
                ) -> ValResult<Bound<'py, PyDict>> {
                    let model_extra_dict = PyDict::new(self.py);
                    for item_result in iterator {
                        let (raw_key, value) = item_result?;
                        let either_str = match raw_key
                            .borrow_input()
                            .validate_str(true, false)
                            .map(ValidationMatch::into_inner)
                        {
                            Ok(k) => k,
                            Err(ValError::LineErrors(line_errors)) => {
                                for err in line_errors {
                                    self.errors.push(
                                        err.with_outer_location(raw_key.clone())
                                            .with_type(ErrorTypeDefaults::InvalidKey),
                                    );
                                }
                                continue;
                            }
                            Err(err) => return Err(err),
                        };
                        let cow = either_str.as_cow()?;
                        if self.used_keys.contains(cow.as_ref()) {
                            continue;
                        }

                        let value = value.borrow_input();
                        // Unknown / extra field
                        match self.extra_behavior {
                            ExtraBehavior::Forbid => {
                                self.errors.push(ValLineError::new_with_loc(
                                    ErrorTypeDefaults::ExtraForbidden,
                                    value,
                                    raw_key.clone(),
                                ));
                            }
                            ExtraBehavior::Ignore => {}
                            ExtraBehavior::Allow => {
                                let py_key = match self.extras_keys_validator {
                                    Some(validator) => {
                                        match validator.validate(self.py, raw_key.borrow_input(), self.state) {
                                            Ok(value) => value.cast_bound::<PyString>(self.py)?.clone(),
                                            Err(ValError::LineErrors(line_errors)) => {
                                                for err in line_errors {
                                                    self.errors.push(err.with_outer_location(raw_key.clone()));
                                                }
                                                continue;
                                            }
                                            Err(err) => return Err(err),
                                        }
                                    }
                                    None => either_str.as_py_string(self.py, self.state.cache_str()),
                                };

                                if let Some(validator) = self.extras_validator {
                                    match validator.validate(self.py, value, self.state) {
                                        Ok(value) => {
                                            model_extra_dict.set_item(&py_key, value)?;
                                            self.fields_set_vec.push(py_key.try_into()?);
                                        }
                                        Err(ValError::LineErrors(line_errors)) => {
                                            for err in line_errors {
                                                self.errors.push(err.with_outer_location(raw_key.clone()));
                                            }
                                        }
                                        Err(err) => return Err(err),
                                    }
                                } else {
                                    model_extra_dict.set_item(&py_key, value.to_object(self.py)?)?;
                                    self.fields_set_vec.push(py_key.try_into()?);
                                }
                            }
                        }
                    }
                    Ok(model_extra_dict)
                }
            }

            let model_extra_dict = dict.iterate(ValidateToModelExtra {
                py,
                used_keys,
                errors: &mut errors,
                fields_set_vec: &mut fields_set_vec,
                extra_behavior,
                extras_validator: self.extras_validator.as_deref(),
                extras_keys_validator: self.extras_keys_validator.as_deref(),
                state,
            })??;

            if matches!(extra_behavior, ExtraBehavior::Allow) {
                model_extra_dict_op = Some(model_extra_dict);
            }
        }

        if !errors.is_empty() {
            Err(ValError::LineErrors(errors))
        } else {
            let fields_set = PySet::new(py, &fields_set_vec)?;
            state.add_fields_set(fields_set_count);

            // if we have extra=allow, but we didn't create a dict because we were validating
            // from attributes, set it now so __pydantic_extra__ is always a dict if extra=allow
            if matches!(extra_behavior, ExtraBehavior::Allow) && model_extra_dict_op.is_none() {
                model_extra_dict_op = Some(PyDict::new(py));
            }

            Ok((model_dict, model_extra_dict_op, fields_set))
        }
    }

    /// Build one model's fields straight off a json cursor, with no `JsonValue` tree.
    ///
    /// `None` means this object is not one the fast path can finish: a value was not the exact type
    /// its field wants, or a field is missing without a default. The whole object has still been
    /// consumed, so the caller can re-read its bytes and validate it the ordinary way, which is how
    /// errors stay identical to the tree path's.
    /// How each field's value can be taken, or `None` if this schema cannot be streamed at all.
    ///
    /// Worked out once per document rather than once per record: with no aliases anywhere the name
    /// path is the only one that can match, whatever the caller configures, so there is no alias
    /// priority to resolve and a key can be handled the moment it is read.
    pub(crate) fn stream_plan(&self) -> Option<ModelPlan<'_>> {
        self.stream_plan_at(0)
    }

    fn stream_plan_at(&self, depth: u8) -> Option<ModelPlan<'_>> {
        let streamable = matches!(self.extra_behavior, ExtraBehavior::Ignore | ExtraBehavior::Forbid)
            && self.extras_validator.is_none()
            && self.fields.iter().all(|field| {
                field
                    .lookup_path_collection
                    .by_alias
                    .iter()
                    .all(LookupPath::is_single_key)
            });
        streamable.then(|| ModelPlan {
            fields: self
                .fields
                .iter()
                .map(|field| classify(&field.validator, depth))
                .collect(),
            names_only: self
                .fields
                .iter()
                .all(|field| field.lookup_path_collection.by_alias.is_empty()),
            forbid_extra: matches!(self.extra_behavior, ExtraBehavior::Forbid),
        })
    }

    pub(crate) fn validate_json_streaming<'j, 'py>(
        &self,
        py: Python<'py>,
        jiter: &mut Jiter<'j>,
        plan: &ModelPlan<'_>,
        state: &mut ValidationState<'_, 'py>,
    ) -> Result<Option<ValidatedModelFields<'py>>, StreamStop> {
        let validate_by_alias = state.validate_by_alias_or(self.validate_by_alias);
        let validate_by_name = state.validate_by_name_or(self.validate_by_name);
        let lookup_type = LookupType::from_bools(validate_by_alias, validate_by_name)?;
        // on the stack for all but the widest models: this is allocated once per object read,
        // and it was half of everything the streaming path allocated
        let mut slots: SmallVec<[Option<Taken<'j, 'py>>; SLOTS_ON_STACK]> =
            (0..self.fields.len()).map(|_| None).collect();

        if plan.names_only {
            let mut key = jiter.known_object()?;
            while let Some(k) = key {
                // the key borrows the cursor, so resolve the field before taking the value
                let found = self
                    .lookup
                    .iter_matches(k, &JsonValue::Null)
                    .find(|(info, _)| info.matches_lookup(lookup_type))
                    .map(|(info, _)| info.field_index);
                match found {
                    Some(index) => slots[index] = Some(take_fast(py, jiter, &plan.fields[index], state)?),
                    None if plan.forbid_extra => return Ok(None),
                    None => jiter.next_skip()?,
                }
                key = jiter.next_key()?;
            }
        } else if !self.scan_aliased(py, jiter, plan, lookup_type, &mut slots, state)? {
            return Ok(None);
        }

        let model_dict = PyDict::new(py);
        let fields_set = PySet::empty(py)?;
        let mut fields_set_count: usize = 0;
        let state = &mut state.scoped_set_data(Some(model_dict.clone()));
        for (field, slot) in std::iter::zip(&self.fields, slots) {
            let value = match slot {
                Some(Taken::Ready(value)) => {
                    fields_set.add(&field.name)?;
                    fields_set_count += 1;
                    value.unbind()
                }
                Some(Taken::Raw(json_value)) => {
                    let state = &mut state.scoped_set_field_name(Some(field.name.as_py_str().bind(py).clone()));
                    match field.validator.validate(py, &json_value, state) {
                        Ok(value) => {
                            fields_set.add(&field.name)?;
                            fields_set_count += 1;
                            value
                        }
                        // any error at all: the ordinary path reports it, with its own locations
                        Err(_) => return Ok(None),
                    }
                }
                None => match field.validator.default_value(py, Some(&*field.name), state) {
                    Ok(Some(default)) => default,
                    // required and absent, or a default that does not simply produce a value
                    _ => return Ok(None),
                },
            };
            model_dict.set_item(&field.name, value)?;
        }
        state.add_fields_set(fields_set_count);
        Ok(Some((model_dict, None, fields_set)))
    }

    /// The same scan for a model that has aliases: a key can reach a field by more than one
    /// route, so each slot remembers which one filled it. Kept out of line so that the common
    /// scan above stays the size it was.
    #[inline(never)]
    fn scan_aliased<'j, 'py>(
        &self,
        py: Python<'py>,
        jiter: &mut Jiter<'j>,
        plan: &ModelPlan<'_>,
        lookup_type: LookupType,
        slots: &mut [Option<Taken<'j, 'py>>],
        state: &mut ValidationState<'_, 'py>,
    ) -> Result<bool, StreamStop> {
        // which lookup filled each slot, so that an alias can outrank a name that came later
        let mut held: SmallVec<[Option<LookupFieldPriority>; SLOTS_ON_STACK]> =
            smallvec::smallvec![None; self.fields.len()];
        let mut key = jiter.known_object()?;
        while let Some(k) = key {
            // a single key can only feed one field here: the value is read once and cannot be
            // handed to a second, so a schema that does that goes the ordinary way
            let mut found: Option<LookupFieldInfo> = None;
            let mut ambiguous = false;
            for (info, _) in self.lookup.iter_matches(k, &JsonValue::Null) {
                if !info.matches_lookup(lookup_type) {
                    continue;
                }
                if found.is_some() {
                    ambiguous = true;
                    break;
                }
                found = Some(*info);
            }
            if ambiguous {
                return Ok(false);
            }
            match found {
                Some(info) => {
                    let index = info.field_index;
                    if info.lookup_priority.replaces(held[index]) {
                        held[index] = Some(info.lookup_priority);
                        slots[index] = Some(take_fast(py, jiter, &plan.fields[index], state)?);
                    } else {
                        jiter.next_skip()?;
                    }
                }
                None if plan.forbid_extra => return Ok(false),
                None => jiter.next_skip()?,
            }
            key = jiter.next_key()?;
        }
        Ok(true)
    }

    fn validate_json_by_iteration<'py>(
        &self,
        py: Python<'py>,
        json_input: &JsonValue<'_>,
        json_object: &JsonObject<'_>,
        state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<ValidatedModelFields<'py>> {
        // expect json_input and json_object to be the same thing, just projected
        debug_assert!(matches!(&json_input, JsonValue::Object(j) if Arc::ptr_eq(j, json_object)));

        let extra_behavior = state.extra_behavior_or(self.extra_behavior);
        let validate_by_alias = state.validate_by_alias_or(self.validate_by_alias);
        let validate_by_name = state.validate_by_name_or(self.validate_by_name);
        let lookup_type = LookupType::from_bools(validate_by_alias, validate_by_name)?;

        let model_dict = PyDict::new(py);
        let mut model_extra_dict_op: Option<Bound<PyDict>> = None;
        let mut field_results: Vec<Option<(LookupFieldInfo, &JsonValue)>> =
            (0..self.fields.len()).map(|_| None).collect();
        let mut errors: Vec<ValLineError> = Vec::new();
        let fields_set = PySet::empty(py)?;
        let mut fields_set_count: usize = 0;

        let state = &mut state.scoped_set_data(Some(model_dict.clone()));
        let state = &mut state.scoped_clear_field_error();

        let model_extra_dict = PyDict::new(py);
        for (key, value) in &**json_object {
            let mut handled = false;
            let key = key.as_ref();
            for (field_info, field_value) in self.lookup.iter_matches(key, value) {
                handled = true;

                if !field_info.matches_lookup(lookup_type) {
                    continue;
                }

                let field_result = &mut field_results[field_info.field_index];

                if !field_info
                    .lookup_priority
                    .replaces(field_result.as_ref().map(|(info, _)| info.lookup_priority))
                {
                    continue;
                }

                *field_result = Some((*field_info, field_value));
            }

            if handled {
                continue;
            }

            // Unknown / extra field - we currently only care about these at the top level
            match extra_behavior {
                ExtraBehavior::Forbid => {
                    errors.push(ValLineError::new_with_loc(
                        ErrorTypeDefaults::ExtraForbidden,
                        value,
                        key,
                    ));
                }
                ExtraBehavior::Ignore => {}
                ExtraBehavior::Allow => {
                    let py_key: Bound<'_, PyString> = new_py_string(py, key, state.cache_str());
                    if let Some(validator) = &self.extras_validator {
                        match validator.validate(py, value, state) {
                            Ok(value) => {
                                model_extra_dict.set_item(&py_key, value)?;
                                fields_set.add(py_key)?;
                            }
                            Err(ValError::LineErrors(line_errors)) => {
                                for err in line_errors {
                                    errors.push(err.with_outer_location(key));
                                }
                            }
                            Err(err) => return Err(err),
                        }
                    } else {
                        model_extra_dict.set_item(&py_key, value)?;
                        fields_set.add(py_key)?;
                    }
                }
            }
        }

        // now that we've iterated over all the keys, we can set the values in the model
        // dict, and try to set defaults for any missing fields

        for (field, field_result) in std::iter::zip(&self.fields, field_results) {
            let state = &mut state.scoped_set_field_name(Some(field.name.as_py_str().bind(py).clone()));

            let field_value = if let Some((field_info, field_json_value)) = field_result {
                match field.validator.validate(py, field_json_value, state) {
                    Ok(value) => {
                        fields_set.add(&field.name)?;
                        fields_set_count += 1;
                        value
                    }
                    Err(ValError::Omit) => continue,
                    Err(ValError::LineErrors(line_errors)) => {
                        state.has_field_error = true;
                        // for line errors, apply the actual lookup path used
                        errors.extend(line_errors.into_iter().map(|mut err| {
                            if self.loc_by_alias
                                && let Some(alias_index) = field_info.alias_index()
                            {
                                err = field.lookup_path_collection.by_alias[alias_index].apply_error_loc(
                                    err,
                                    self.loc_by_alias,
                                    &field.name,
                                );
                            } else {
                                err = err.with_outer_location(field.name.clone());
                            }
                            err
                        }));
                        continue;
                    }
                    Err(err) => return Err(err),
                }
            } else {
                match field.validator.default_value(py, Some(&*field.name), state) {
                    Ok(Some(default_value)) => default_value,
                    Ok(None) => {
                        // There was no default value
                        let error_type = ErrorTypeDefaults::Missing;
                        let error_loc = field.lookup_path_collection.error_loc(lookup_type, self.loc_by_alias);
                        errors.push(ValLineError::new_with_full_loc(error_type, json_input, error_loc));
                        continue;
                    }
                    Err(ValError::Omit) => continue,
                    Err(ValError::LineErrors(line_errors)) => {
                        state.has_field_error = true;
                        for err in line_errors {
                            // Note: this will always use the field name even if there is an alias
                            // However, we don't mind so much because this error can only happen if the
                            // default value fails validation, which is arguably a developer error.
                            // We could try to "fix" this in the future if desired.
                            errors.push(err);
                        }
                        continue;
                    }
                    Err(err) => return Err(err),
                }
            };

            model_dict.set_item(&field.name, field_value)?;
        }

        if matches!(extra_behavior, ExtraBehavior::Allow) {
            model_extra_dict_op = Some(model_extra_dict);
        }

        if !errors.is_empty() {
            return Err(ValError::LineErrors(errors));
        }

        state.add_fields_set(fields_set_count);
        Ok((model_dict, model_extra_dict_op, fields_set))
    }
}

#[cfg(test)]
mod plan_tests {
    use super::*;

    fn bounded(min: Option<usize>, max: Option<usize>) -> ContainerPlan<'static> {
        ContainerPlan {
            element: FieldPlan {
                fast: Fast::Str,
                nullable: false,
            },
            min_length: min,
            max_length: max,
        }
    }

    /// Both bounds are inclusive, matching `length_check!`, which is what the ordinary path
    /// applies to the same container.
    #[test]
    fn length_bounds_are_inclusive() {
        let none = bounded(None, None);
        assert!(none.length_ok(0));
        assert!(none.length_ok(9999));

        let at_least_two = bounded(Some(2), None);
        assert!(!at_least_two.length_ok(1));
        assert!(at_least_two.length_ok(2));
        assert!(at_least_two.length_ok(3));

        let at_most_two = bounded(None, Some(2));
        assert!(at_most_two.length_ok(2));
        assert!(!at_most_two.length_ok(3));

        let exactly_two = bounded(Some(2), Some(2));
        assert!(!exactly_two.length_ok(1));
        assert!(exactly_two.length_ok(2));
        assert!(!exactly_two.length_ok(3));
    }

    /// A field's plan sits in a `Vec` per model and is rebuilt per document, so a fat variant
    /// costs every field of every model. Box a new variant rather than raising this.
    #[test]
    fn field_plan_stays_small() {
        assert!(
            std::mem::size_of::<FieldPlan<'_>>() <= 24,
            "FieldPlan grew to {} bytes",
            std::mem::size_of::<FieldPlan<'_>>()
        );
    }
}
