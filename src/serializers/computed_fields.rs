use pyo3::intern;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyString};
use serde::ser::SerializeMap;
use serde::Serialize;

use crate::build_tools::py_schema_error_type;
use crate::definitions::DefinitionsBuilder;
use crate::serializers::filter::SchemaFilter;
use crate::serializers::shared::{BuildSerializer, CombinedSerializer, PydanticSerializer, TypeSerializer};
use crate::tools::SchemaDict;

use super::errors::py_err_se_err;
use super::Extra;

#[derive(Debug, Clone)]
pub(super) struct ComputedFields(Vec<ComputedField>);

impl ComputedFields {
    pub fn new(
        schema: &PyDict,
        config: Option<&PyDict>,
        definitions: &mut DefinitionsBuilder<CombinedSerializer>,
    ) -> PyResult<Option<Self>> {
        let py = schema.py();
        if let Some(computed_fields) = schema.get_as::<&PyList>(intern!(py, "computed_fields"))? {
            let computed_fields = computed_fields
                .iter()
                .map(|field| ComputedField::new(field, config, definitions))
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
        model: &PyAny,
        output_dict: &PyDict,
        filter: &SchemaFilter<isize>,
        include: Option<&PyAny>,
        exclude: Option<&PyAny>,
        extra: &Extra,
    ) -> PyResult<()> {
        for computed_fields in &self.0 {
            computed_fields.to_python(model, output_dict, filter, include, exclude, extra)?;
        }
        Ok(())
    }

    pub fn serde_serialize<S: serde::ser::Serializer>(
        &self,
        model: &PyAny,
        map: &mut S::SerializeMap,
        filter: &SchemaFilter<isize>,
        include: Option<&PyAny>,
        exclude: Option<&PyAny>,
        extra: &Extra,
    ) -> Result<(), S::Error> {
        for computed_field in &self.0 {
            let property_name_py = computed_field.property_name_py.as_ref(model.py());
            if let Some((next_include, next_exclude)) = filter
                .key_filter(property_name_py, include, exclude)
                .map_err(py_err_se_err)?
            {
                let cfs = ComputedFieldSerializer {
                    model,
                    computed_field,
                    include: next_include,
                    exclude: next_exclude,
                    extra,
                };
                let key = match extra.by_alias {
                    true => computed_field.alias.as_str(),
                    false => computed_field.property_name.as_str(),
                };
                map.serialize_entry(key, &cfs)?;
            }
        }
        Ok(())
    }
}

#[derive(Debug, Clone)]
struct ComputedField {
    property_name: String,
    property_name_py: Py<PyString>,
    serializer: CombinedSerializer,
    alias: String,
    alias_py: Py<PyString>,
}

impl ComputedField {
    pub fn new(
        schema: &PyAny,
        config: Option<&PyDict>,
        definitions: &mut DefinitionsBuilder<CombinedSerializer>,
    ) -> PyResult<Self> {
        let py = schema.py();
        let schema: &PyDict = schema.downcast()?;
        let property_name: &PyString = schema.get_as_req(intern!(py, "property_name"))?;
        let return_schema = schema.get_as_req(intern!(py, "return_schema"))?;
        let serializer = CombinedSerializer::build(return_schema, config, definitions)
            .map_err(|e| py_schema_error_type!("Computed field `{}`:\n  {}", property_name, e))?;
        let alias_py: &PyString = schema.get_as(intern!(py, "alias"))?.unwrap_or(property_name);
        Ok(Self {
            property_name: property_name.extract()?,
            property_name_py: property_name.into_py(py),
            serializer,
            alias: alias_py.extract()?,
            alias_py: alias_py.into_py(py),
        })
    }

    fn to_python(
        &self,
        model: &PyAny,
        output_dict: &PyDict,
        filter: &SchemaFilter<isize>,
        include: Option<&PyAny>,
        exclude: Option<&PyAny>,
        extra: &Extra,
    ) -> PyResult<()> {
        let py = model.py();
        let property_name_py = self.property_name_py.as_ref(py);

        if let Some((next_include, next_exclude)) = filter.key_filter(property_name_py, include, exclude)? {
            let next_value = model.getattr(property_name_py)?;

            let value = self
                .serializer
                .to_python(next_value, next_include, next_exclude, extra)?;
            if extra.exclude_none && value.is_none(py) {
                return Ok(());
            }
            let key = match extra.by_alias {
                true => self.alias_py.as_ref(py),
                false => property_name_py,
            };
            output_dict.set_item(key, value)?;
        }
        Ok(())
    }
}

pub(crate) struct ComputedFieldSerializer<'py> {
    model: &'py PyAny,
    computed_field: &'py ComputedField,
    include: Option<&'py PyAny>,
    exclude: Option<&'py PyAny>,
    extra: &'py Extra<'py>,
}

impl<'py> Serialize for ComputedFieldSerializer<'py> {
    fn serialize<S: serde::ser::Serializer>(&self, serializer: S) -> Result<S::Ok, S::Error> {
        let py = self.model.py();
        let property_name_py = self.computed_field.property_name_py.as_ref(py);
        let next_value = self.model.getattr(property_name_py).map_err(py_err_se_err)?;
        let s = PydanticSerializer::new(
            next_value,
            &self.computed_field.serializer,
            self.include,
            self.exclude,
            self.extra,
        );
        s.serialize(serializer)
    }
}
