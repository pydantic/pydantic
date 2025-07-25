use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyString};
use pyo3::{intern, PyTraverseError, PyVisit};
use serde::ser::SerializeMap;

use crate::build_tools::py_schema_error_type;
use crate::common::missing_sentinel::get_missing_sentinel_object;
use crate::definitions::DefinitionsBuilder;
use crate::py_gc::PyGcTraverse;
use crate::serializers::filter::SchemaFilter;
use crate::serializers::shared::{BuildSerializer, CombinedSerializer, PydanticSerializer};
use crate::tools::SchemaDict;

use super::errors::py_err_se_err;
use super::Extra;

#[derive(Debug)]
pub(super) struct ComputedFields(Vec<ComputedField>);

impl ComputedFields {
    pub fn new(
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        definitions: &mut DefinitionsBuilder<CombinedSerializer>,
    ) -> PyResult<Option<Self>> {
        let py = schema.py();
        if let Some(computed_fields) = schema.get_as::<Bound<'_, PyList>>(intern!(py, "computed_fields"))? {
            let computed_fields = computed_fields
                .iter()
                .map(|field| ComputedField::new(&field, config, definitions))
                .collect::<PyResult<Vec<_>>>()?;
            Ok(Some(Self(computed_fields)))
        } else {
            Ok(None)
        }
    }

    pub fn len(&self) -> usize {
        self.0.len()
    }

    pub fn to_python(
        &self,
        model: &Bound<'_, PyAny>,
        output_dict: &Bound<'_, PyDict>,
        filter: &SchemaFilter<isize>,
        include: Option<&Bound<'_, PyAny>>,
        exclude: Option<&Bound<'_, PyAny>>,
        extra: &Extra,
    ) -> PyResult<()> {
        self.serialize_fields(
            model,
            filter,
            include,
            exclude,
            extra,
            |e| e,
            |ComputedFieldToSerialize {
                 computed_field,
                 value,
                 include,
                 exclude,
                 field_extra,
             }| {
                let key = match field_extra.serialize_by_alias_or(computed_field.serialize_by_alias) {
                    true => computed_field.alias_py.bind(model.py()),
                    false => computed_field.property_name_py.bind(model.py()),
                };
                let value =
                    computed_field
                        .serializer
                        .to_python(&value, include.as_ref(), exclude.as_ref(), &field_extra)?;
                output_dict.set_item(key, value)
            },
        )
    }

    pub fn serde_serialize<S: serde::ser::Serializer>(
        &self,
        model: &Bound<'_, PyAny>,
        map: &mut S::SerializeMap,
        filter: &SchemaFilter<isize>,
        include: Option<&Bound<'_, PyAny>>,
        exclude: Option<&Bound<'_, PyAny>>,
        extra: &Extra,
    ) -> Result<(), S::Error> {
        self.serialize_fields(
            model,
            filter,
            include,
            exclude,
            extra,
            py_err_se_err,
            |ComputedFieldToSerialize {
                 computed_field,
                 value,
                 include,
                 exclude,
                 field_extra,
             }| {
                let key = match field_extra.serialize_by_alias_or(computed_field.serialize_by_alias) {
                    true => &computed_field.alias,
                    false => &computed_field.property_name,
                };
                let s = PydanticSerializer::new(
                    &value,
                    &computed_field.serializer,
                    include.as_ref(),
                    exclude.as_ref(),
                    &field_extra,
                );
                map.serialize_entry(key, &s)
            },
        )
    }

    /// Iterate each field for serialization, filtering on
    /// `include` and `exclude` if provided.
    #[allow(clippy::too_many_arguments)]
    fn serialize_fields<'a, 'py, E>(
        &'a self,
        model: &'a Bound<'py, PyAny>,
        filter: &'a SchemaFilter<isize>,
        include: Option<&'a Bound<'py, PyAny>>,
        exclude: Option<&'a Bound<'py, PyAny>>,
        extra: &'a Extra,
        convert_error: impl FnOnce(PyErr) -> E,
        mut serialize: impl FnMut(ComputedFieldToSerialize<'a, 'py>) -> Result<(), E>,
    ) -> Result<(), E> {
        if extra.round_trip {
            // Do not serialize computed fields
            return Ok(());
        }

        for computed_field in &self.0 {
            let property_name_py = computed_field.property_name_py.bind(model.py());
            let (next_include, next_exclude) = match filter.key_filter(property_name_py, include, exclude) {
                Ok(Some((next_include, next_exclude))) => (next_include, next_exclude),
                Ok(None) => continue,
                Err(e) => return Err(convert_error(e)),
            };

            let value = match model.getattr(property_name_py) {
                Ok(field_value) => field_value,
                Err(e) => {
                    return Err(convert_error(e));
                }
            };
            if extra.exclude_none && value.is_none() {
                continue;
            }
            let missing_sentinel = get_missing_sentinel_object(model.py());
            if value.is(missing_sentinel) {
                continue;
            }

            let field_extra = Extra {
                field_name: Some(&computed_field.property_name),
                ..*extra
            };
            serialize(ComputedFieldToSerialize {
                computed_field,
                value,
                include: next_include,
                exclude: next_exclude,
                field_extra,
            })?;
        }
        Ok(())
    }
}

struct ComputedFieldToSerialize<'a, 'py> {
    computed_field: &'a ComputedField,
    value: Bound<'py, PyAny>,
    include: Option<Bound<'py, PyAny>>,
    exclude: Option<Bound<'py, PyAny>>,
    field_extra: Extra<'a>,
}

#[derive(Debug)]
struct ComputedField {
    property_name: String,
    property_name_py: Py<PyString>,
    serializer: CombinedSerializer,
    alias: String,
    alias_py: Py<PyString>,
    serialize_by_alias: Option<bool>,
}

impl ComputedField {
    pub fn new(
        schema: &Bound<'_, PyAny>,
        config: Option<&Bound<'_, PyDict>>,
        definitions: &mut DefinitionsBuilder<CombinedSerializer>,
    ) -> PyResult<Self> {
        let py = schema.py();
        let schema: &Bound<'_, PyDict> = schema.downcast()?;
        let property_name: Bound<'_, PyString> = schema.get_as_req(intern!(py, "property_name"))?;
        let return_schema = schema.get_as_req(intern!(py, "return_schema"))?;
        let serializer = CombinedSerializer::build(&return_schema, config, definitions)
            .map_err(|e| py_schema_error_type!("Computed field `{}`:\n  {}", property_name, e))?;
        let alias_py = schema
            .get_as(intern!(py, "alias"))?
            .unwrap_or_else(|| property_name.clone());
        Ok(Self {
            property_name: property_name.extract()?,
            property_name_py: property_name.into(),
            serializer,
            alias: alias_py.extract()?,
            alias_py: alias_py.into(),
            serialize_by_alias: config.get_as(intern!(py, "serialize_by_alias"))?,
        })
    }
}

impl_py_gc_traverse!(ComputedField { serializer });

impl PyGcTraverse for ComputedFields {
    fn py_gc_traverse(&self, visit: &PyVisit<'_>) -> Result<(), PyTraverseError> {
        self.0.py_gc_traverse(visit)
    }
}
