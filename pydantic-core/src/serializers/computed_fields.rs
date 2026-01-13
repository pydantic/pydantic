use std::sync::Arc;

use pyo3::prelude::*;
use pyo3::pybacked::PyBackedStr;
use pyo3::types::{PyDict, PyList};
use pyo3::{PyTraverseError, PyVisit, intern};

use crate::build_tools::py_schema_error_type;
use crate::common::missing_sentinel::get_missing_sentinel_object;
use crate::definitions::DefinitionsBuilder;
use crate::py_gc::PyGcTraverse;
use crate::serializers::SerializationState;
use crate::serializers::extra::FieldName;
use crate::serializers::filter::SchemaFilter;
use crate::serializers::shared::{BuildSerializer, CombinedSerializer, SerializeMap};
use crate::tools::{SchemaDict, pybackedstr_to_pystring};

#[derive(Debug)]
pub(super) struct ComputedFields(Vec<ComputedField>);

impl ComputedFields {
    pub fn new(
        schema: &Bound<'_, PyDict>,
        config: Option<&Bound<'_, PyDict>>,
        definitions: &mut DefinitionsBuilder<Arc<CombinedSerializer>>,
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

    pub fn serialize<'py, M: SerializeMap>(
        &self,
        model: &Bound<'py, PyAny>,
        map: &mut M,
        filter: &SchemaFilter<isize>,
        state: &mut SerializationState<'py>,
    ) -> Result<(), M::Error> {
        // In round trip mode, exclude computed fields:
        if state.extra.round_trip || state.extra.exclude_computed_fields {
            return Ok(());
        }

        for computed_field in &self.0 {
            let property_name_py = pybackedstr_to_pystring(model.py(), &computed_field.property_name);
            let Some((next_include, next_exclude)) = filter.key_filter(&property_name_py, state)? else {
                continue;
            };

            let value = model.getattr(&property_name_py)?;
            if state.extra.exclude_none && value.is_none() {
                continue;
            }
            let missing_sentinel = get_missing_sentinel_object(model.py());
            if value.is(missing_sentinel) {
                continue;
            }

            let field_name = FieldName::from(property_name_py);
            let state = &mut state.scoped_set(|s| &mut s.field_name, Some(field_name));
            let state = &mut state.scoped_include_exclude(next_include, next_exclude);
            let key = match state.extra.serialize_by_alias_or(computed_field.serialize_by_alias) {
                true => &computed_field.alias,
                false => &computed_field.property_name,
            };
            map.serialize_entry_string_key(key, &value, &computed_field.serializer, state)?;
        }
        Ok(())
    }
}

#[derive(Debug)]
struct ComputedField {
    property_name: PyBackedStr,
    serializer: Arc<CombinedSerializer>,
    alias: PyBackedStr,
    serialize_by_alias: Option<bool>,
}

impl ComputedField {
    pub fn new(
        schema: &Bound<'_, PyAny>,
        config: Option<&Bound<'_, PyDict>>,
        definitions: &mut DefinitionsBuilder<Arc<CombinedSerializer>>,
    ) -> PyResult<Self> {
        let py = schema.py();
        let schema: &Bound<'_, PyDict> = schema.cast()?;
        let property_name: PyBackedStr = schema.get_as_req(intern!(py, "property_name"))?;
        let return_schema = schema.get_as_req(intern!(py, "return_schema"))?;
        let serializer = CombinedSerializer::build(&return_schema, config, definitions)
            .map_err(|e| py_schema_error_type!("Computed field `{property_name}`:\n  {e}"))?;
        let alias = schema
            .get_as(intern!(py, "alias"))?
            .unwrap_or_else(|| property_name.clone());
        Ok(Self {
            property_name,
            serializer,
            alias,
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
