use std::sync::Arc;

use pyo3::intern;
use pyo3::prelude::*;
use pyo3::pybacked::PyBackedStr;
use pyo3::types::{PyDict, PyList, PyTuple, PyType};

use ahash::AHashSet;

use crate::build_tools::py_schema_err;
use crate::errors::{ErrorType, ErrorTypeDefaults, LocItem, ValError, ValLineError, ValResult, py_err_string};
use crate::input::{
    BorrowInput, ConsumeIterator, Input, ValidatedDict, ValidatedTuple, ValidationMatch, input_as_python_instance,
};
use crate::lookup_key::{LookupPathCollection, LookupType};
use crate::tools::SchemaDict;
use crate::validators::function::convert_err;

use super::validation_state::Exactness;
use super::{BuildValidator, CombinedValidator, DefinitionsBuilder, ValidationState, Validator, build_validator};

#[derive(Debug)]
struct NamedTupleField {
    name: PyBackedStr,
    lookup_path_collection: LookupPathCollection,
    validator: Arc<CombinedValidator>,
}

impl_py_gc_traverse!(NamedTupleField { validator });

#[derive(Debug)]
pub struct NamedTupleValidator {
    class: Py<PyType>,
    fields: Vec<NamedTupleField>,
    loc_by_alias: bool,
    validate_by_alias: Option<bool>,
    validate_by_name: Option<bool>,
    name: String,
}

impl BuildValidator for NamedTupleValidator {
    const EXPECTED_TYPE: &'static str = "named-tuple";

    fn build(
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        definitions: &mut DefinitionsBuilder<Arc<CombinedValidator>>,
    ) -> PyResult<Arc<CombinedValidator>> {
        let py = schema.py();

        let class = schema.get_as_req::<Bound<'_, PyType>>(intern!(py, "cls"))?;
        let name = match schema.get_as::<String>(intern!(py, "cls_name"))? {
            Some(name) => name,
            None => class.getattr(intern!(py, "__name__"))?.extract()?,
        };

        let fields_list: Bound<'_, PyList> = schema.get_as_req(intern!(py, "fields"))?;
        let mut fields: Vec<NamedTupleField> = Vec::with_capacity(fields_list.len());

        for field in fields_list {
            let field = field.cast::<PyDict>()?;

            let field_name: PyBackedStr = field.get_as_req(intern!(py, "name"))?;

            let schema = field.get_as_req(intern!(py, "schema"))?;
            let validator = match build_validator(&schema, config, definitions) {
                Ok(v) => v,
                Err(err) => return py_schema_err!("Field '{field_name}':\n  {err}"),
            };

            if let CombinedValidator::WithDefault(v) = validator.as_ref()
                && v.omit_on_error()
            {
                return py_schema_err!("Field '{field_name}': 'on_error = omit' cannot be set for named tuple fields");
            }

            let validation_alias = field.get_as(intern!(py, "validation_alias"))?;
            let lookup_path_collection = LookupPathCollection::new(validation_alias, field_name.clone())?;

            fields.push(NamedTupleField {
                name: field_name,
                lookup_path_collection,
                validator,
            });
        }

        Ok(CombinedValidator::NamedTuple(Self {
            class: class.into(),
            fields,
            loc_by_alias: config.get_as(intern!(py, "loc_by_alias"))?.unwrap_or(true),
            validate_by_alias: config.get_as(intern!(py, "validate_by_alias"))?,
            validate_by_name: config.get_as(intern!(py, "validate_by_name"))?,
            name,
        })
        .into())
    }
}

impl_py_gc_traverse!(NamedTupleValidator { class, fields });

impl Validator for NamedTupleValidator {
    fn validate<'py>(
        &self,
        py: Python<'py>,
        input: &(impl Input<'py> + ?Sized),
        state: &mut ValidationState<'_, 'py>,
    ) -> ValResult<Py<PyAny>> {
        // this validator does not yet support partial validation, disable it to avoid incorrect results
        state.allow_partial = false.into();

        let class = self.class.bind(py);

        if let Some(py_input) = input_as_python_instance(input, class) {
            // An instance of the named tuple class itself; revalidate the items (using
            // field names in error locations) and reconstruct an instance. Exactness is
            // left untouched, so that the nominal class is preserved in smart unions:
            let collection = py_input.validate_tuple(false)?.unpack(state);
            let items = self.validate_tuple_collection(py, input, state, collection, true)?;
            return self.create_instance(py, input, items);
        }

        // Note: strict mode is currently ignored, as the `'call'` core schema previously
        // used for named tuples had no strict behavior:
        match input.validate_tuple(false) {
            Ok(tuple_match) => {
                // A tuple, list or JSON array; validate positionally, using indices in error locations:
                let collection = tuple_match.unpack(state);
                let items = self.validate_tuple_collection(py, input, state, collection, false)?;
                state.floor_exactness(Exactness::Strict);
                self.create_instance(py, input, items)
            }
            Err(ValError::LineErrors(_)) => match input.validate_dict(false) {
                Ok(dict) => {
                    // A dict, mapping or JSON object; validate by field name:
                    let items = self.validate_dict_input(py, input, state, &dict)?;
                    state.floor_exactness(Exactness::Strict);
                    self.create_instance(py, input, items)
                }
                Err(ValError::LineErrors(_)) => Err(ValError::new(
                    ErrorType::NamedTupleType {
                        class_name: self.name.clone(),
                        context: None,
                    },
                    input,
                )),
                Err(err) => Err(err),
            },
            Err(err) => Err(err),
        }
    }

    fn get_name(&self) -> &str {
        &self.name
    }
}

impl NamedTupleValidator {
    fn validate_tuple_collection<'py, T: ValidatedTuple<'py>>(
        &self,
        py: Python<'py>,
        input: &(impl Input<'py> + ?Sized),
        state: &mut ValidationState<'_, 'py>,
        collection: T,
        name_locs: bool,
    ) -> ValResult<Vec<Py<PyAny>>> {
        let actual_length = collection.len();

        collection.iterate(ValidateItems {
            py,
            input,
            actual_length,
            validator: self,
            state,
            name_locs,
        })?
    }

    fn validate_dict_input<'py>(
        &self,
        py: Python<'py>,
        input: &(impl Input<'py> + ?Sized),
        state: &mut ValidationState<'_, 'py>,
        dict: &impl ValidatedDict<'py>,
    ) -> ValResult<Vec<Py<PyAny>>> {
        let mut output: Vec<Py<PyAny>> = Vec::with_capacity(self.fields.len());
        let mut errors: Vec<ValLineError> = Vec::new();
        let mut used_keys: AHashSet<&str> = AHashSet::with_capacity(self.fields.len());

        let validate_by_alias = state.validate_by_alias_or(self.validate_by_alias);
        let validate_by_name = state.validate_by_name_or(self.validate_by_name);
        let lookup_type = LookupType::from_bools(validate_by_alias, validate_by_name)?;

        for field in &self.fields {
            if let Some((lookup_path, lookup_result)) = field
                .lookup_path_collection
                .lookup_paths(lookup_type)
                .find_map(|path| Some((path, dict.get_item(path).transpose()?)))
            {
                let value = lookup_result?;
                used_keys.insert(lookup_path.first_key());

                let state = &mut state.scoped_set_field_name(Some(field.name.as_py_str().bind(py).clone()));

                match field.validator.validate(py, value.borrow_input(), state) {
                    Ok(value) => output.push(value),
                    Err(ValError::LineErrors(line_errors)) => {
                        errors.extend(
                            line_errors
                                .into_iter()
                                .map(|err| lookup_path.apply_error_loc(err, self.loc_by_alias, &field.name)),
                        );
                    }
                    Err(err) => return Err(err),
                }
                continue;
            }

            match field.validator.default_value(py, Some(field.name.clone()), state) {
                Ok(Some(value)) => output.push(value),
                Ok(None) => {
                    let error_loc = field.lookup_path_collection.error_loc(lookup_type, self.loc_by_alias);
                    errors.push(ValLineError::new_with_full_loc(
                        ErrorTypeDefaults::Missing,
                        input,
                        error_loc,
                    ));
                }
                Err(ValError::LineErrors(line_errors)) => {
                    // Note: this will always use the field name even if there is an alias
                    // However, we don't mind so much because this error can only happen if the
                    // default value fails validation, which is arguably a developer error.
                    errors.extend(line_errors);
                }
                Err(err) => return Err(err),
            }
        }

        dict.iterate(CheckExtras {
            used_keys,
            errors: &mut errors,
        })??;

        if errors.is_empty() {
            Ok(output)
        } else {
            Err(ValError::LineErrors(errors))
        }
    }

    fn create_instance<'py>(
        &self,
        py: Python<'py>,
        input: &(impl Input<'py> + ?Sized),
        items: Vec<Py<PyAny>>,
    ) -> ValResult<Py<PyAny>> {
        let args = PyTuple::new(py, items)?;
        match self.class.bind(py).call1(args) {
            Ok(instance) => Ok(instance.unbind()),
            Err(e) => Err(convert_err(py, e, input)),
        }
    }
}

struct CheckExtras<'a> {
    used_keys: AHashSet<&'a str>,
    errors: &'a mut Vec<ValLineError>,
}

impl<'py, Key, Value> ConsumeIterator<ValResult<(Key, Value)>> for CheckExtras<'_>
where
    Key: BorrowInput<'py> + Clone + Into<LocItem>,
    Value: BorrowInput<'py>,
{
    type Output = ValResult<()>;
    fn consume_iterator(self, iterator: impl Iterator<Item = ValResult<(Key, Value)>>) -> ValResult<()> {
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
            if !self.used_keys.contains(either_str.as_cow()?.as_ref()) {
                // Named tuples cannot hold extra fields, so extra keys are always forbidden:
                self.errors.push(ValLineError::new_with_loc(
                    ErrorTypeDefaults::ExtraForbidden,
                    value.borrow_input(),
                    raw_key.clone(),
                ));
            }
        }
        Ok(())
    }
}

struct ValidateItems<'a, 's, 'py, I: Input<'py> + ?Sized> {
    py: Python<'py>,
    input: &'a I,
    actual_length: Option<usize>,
    validator: &'a NamedTupleValidator,
    state: &'a mut ValidationState<'s, 'py>,
    name_locs: bool,
}

impl<'py, T, I> ConsumeIterator<PyResult<T>> for ValidateItems<'_, '_, 'py, I>
where
    T: BorrowInput<'py>,
    I: Input<'py> + ?Sized,
{
    type Output = ValResult<Vec<Py<PyAny>>>;
    fn consume_iterator(self, mut iterator: impl Iterator<Item = PyResult<T>>) -> ValResult<Vec<Py<PyAny>>> {
        let fields = &self.validator.fields;
        let mut output: Vec<Py<PyAny>> = Vec::with_capacity(fields.len());
        let mut errors: Vec<ValLineError> = Vec::new();

        for (index, field) in fields.iter().enumerate() {
            let loc: LocItem = if self.name_locs {
                field.name.clone().into()
            } else {
                index.into()
            };
            match iterator.next() {
                Some(Ok(item)) => {
                    let state = &mut self
                        .state
                        .scoped_set_field_name(Some(field.name.as_py_str().bind(self.py).clone()));
                    match field.validator.validate(self.py, item.borrow_input(), state) {
                        Ok(value) => output.push(value),
                        Err(ValError::LineErrors(line_errors)) => {
                            errors.extend(line_errors.into_iter().map(|err| err.with_outer_location(loc.clone())));
                        }
                        Err(err) => return Err(err),
                    }
                }
                Some(Err(e)) => {
                    return Err(ValError::new_with_loc(
                        ErrorType::IterationError {
                            error: py_err_string(self.py, e),
                            context: None,
                        },
                        self.input,
                        index,
                    ));
                }
                None => match field.validator.default_value(self.py, Some(loc.clone()), self.state)? {
                    Some(value) => output.push(value),
                    None => {
                        errors.push(ValLineError::new_with_loc(ErrorTypeDefaults::Missing, self.input, loc));
                    }
                },
            }
        }

        // Generate an error if there are any extra items:
        if iterator.next().is_some() {
            return Err(ValError::new(
                ErrorType::TooLong {
                    field_type: "NamedTuple".to_string(),
                    max_length: fields.len(),
                    actual_length: self.actual_length,
                    context: None,
                },
                self.input,
            ));
        }

        if errors.is_empty() {
            Ok(output)
        } else {
            Err(ValError::LineErrors(errors))
        }
    }
}
