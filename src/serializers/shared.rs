use std::borrow::Cow;
use std::fmt::Debug;

use pyo3::exceptions::PyTypeError;
use pyo3::once_cell::GILOnceCell;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyString};
use pyo3::{intern, PyTraverseError, PyVisit};

use enum_dispatch::enum_dispatch;
use serde::Serialize;
use serde_json::ser::PrettyFormatter;

use crate::build_tools::py_schema_err;
use crate::build_tools::py_schema_error_type;
use crate::definitions::DefinitionsBuilder;
use crate::tools::{py_err, SchemaDict};

use super::errors::se_err_py_err;
use super::extra::Extra;
use super::infer::infer_json_key;
use super::ob_type::{IsType, ObType};
use super::type_serializers::definitions::DefinitionRefSerializer;

pub(crate) trait BuildSerializer: Sized {
    const EXPECTED_TYPE: &'static str;

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        definitions: &mut DefinitionsBuilder<CombinedSerializer>,
    ) -> PyResult<CombinedSerializer>;
}

/// Build the `CombinedSerializer` enum and implement a `find_serializer` method for it.
macro_rules! combined_serializer {
    (
        enum_only: {$($e_key:ident: $e_serializer:path;)*}
        find_only: {$($builder:path;)*}
        both: {$($b_key:ident: $b_serializer:path;)*}
    ) => {
        #[derive(Debug, Clone)]
        #[enum_dispatch]
        pub enum CombinedSerializer {
            $($e_key($e_serializer),)*
            $($b_key($b_serializer),)*
        }

        impl CombinedSerializer {
            fn find_serializer(
                lookup_type: &str,
                schema: &PyDict,
                config: Option<&PyDict>,
                definitions: &mut DefinitionsBuilder<CombinedSerializer>
            ) -> PyResult<CombinedSerializer> {
                match lookup_type {
                    $(
                        <$b_serializer>::EXPECTED_TYPE => match <$b_serializer>::build(schema, config, definitions) {
                            Ok(serializer) => Ok(serializer),
                            Err(err) => py_schema_err!("Error building `{}` serializer:\n  {}", lookup_type, err),
                        },
                    )*
                    $(
                        <$builder>::EXPECTED_TYPE => match <$builder>::build(schema, config, definitions) {
                            Ok(serializer) => Ok(serializer),
                            Err(err) => py_schema_err!("Error building `{}` serializer:\n  {}", lookup_type, err),
                        },
                    )*
                    _ => py_schema_err!("Unknown serialization schema type: `{}`", lookup_type),
                }
            }
        }

    };
}

combined_serializer! {
    // `enum_only` is for type_serializers which are not built directly via the `type` key and `find_serializer`
    // but are included in the `CombinedSerializer` enum
    enum_only: {
        // function type_serializers cannot be defined by type lookup, but must be members of `CombinedSerializer`,
        // hence they're here.
        Function: super::type_serializers::function::FunctionPlainSerializer;
        FunctionWrap: super::type_serializers::function::FunctionWrapSerializer;
        Fields: super::fields::GeneralFieldsSerializer;
    }
    // `find_only` is for type_serializers which are built directly via the `type` key and `find_serializer`
    // but aren't actually used for serialization, e.g. their `build` method must return another serializer
    find_only: {
        super::type_serializers::union::TaggedUnionBuilder;
        super::type_serializers::other::ChainBuilder;
        super::type_serializers::other::CustomErrorBuilder;
        super::type_serializers::other::CallBuilder;
        super::type_serializers::other::LaxOrStrictBuilder;
        super::type_serializers::other::ArgumentsBuilder;
        super::type_serializers::other::IsInstanceBuilder;
        super::type_serializers::other::IsSubclassBuilder;
        super::type_serializers::other::CallableBuilder;
        super::type_serializers::definitions::DefinitionsSerializerBuilder;
        super::type_serializers::dataclass::DataclassArgsBuilder;
        super::type_serializers::function::FunctionBeforeSerializerBuilder;
        super::type_serializers::function::FunctionAfterSerializerBuilder;
        super::type_serializers::function::FunctionPlainSerializerBuilder;
        super::type_serializers::function::FunctionWrapSerializerBuilder;
        super::type_serializers::model::ModelFieldsBuilder;
        super::type_serializers::typed_dict::TypedDictBuilder;
    }
    // `both` means the struct is added to both the `CombinedSerializer` enum and the match statement in
    // `find_serializer` so they can be used via a `type` str.
    both: {
        None: super::type_serializers::simple::NoneSerializer;
        Nullable: super::type_serializers::nullable::NullableSerializer;
        Int: super::type_serializers::simple::IntSerializer;
        Bool: super::type_serializers::simple::BoolSerializer;
        Float: super::type_serializers::simple::FloatSerializer;
        Str: super::type_serializers::string::StrSerializer;
        Bytes: super::type_serializers::bytes::BytesSerializer;
        Datetime: super::type_serializers::datetime_etc::DatetimeSerializer;
        TimeDelta: super::type_serializers::timedelta::TimeDeltaSerializer;
        Date: super::type_serializers::datetime_etc::DateSerializer;
        Time: super::type_serializers::datetime_etc::TimeSerializer;
        List: super::type_serializers::list::ListSerializer;
        Set: super::type_serializers::set_frozenset::SetSerializer;
        FrozenSet: super::type_serializers::set_frozenset::FrozenSetSerializer;
        Generator: super::type_serializers::generator::GeneratorSerializer;
        Dict: super::type_serializers::dict::DictSerializer;
        Model: super::type_serializers::model::ModelSerializer;
        Dataclass: super::type_serializers::dataclass::DataclassSerializer;
        Url: super::type_serializers::url::UrlSerializer;
        MultiHostUrl: super::type_serializers::url::MultiHostUrlSerializer;
        Any: super::type_serializers::any::AnySerializer;
        Format: super::type_serializers::format::FormatSerializer;
        ToString: super::type_serializers::format::ToStringSerializer;
        WithDefault: super::type_serializers::with_default::WithDefaultSerializer;
        Json: super::type_serializers::json::JsonSerializer;
        JsonOrPython: super::type_serializers::json_or_python::JsonOrPythonSerializer;
        Union: super::type_serializers::union::UnionSerializer;
        Literal: super::type_serializers::literal::LiteralSerializer;
        Recursive: super::type_serializers::definitions::DefinitionRefSerializer;
        TuplePositional: super::type_serializers::tuple::TuplePositionalSerializer;
        TupleVariable: super::type_serializers::tuple::TupleVariableSerializer;
    }
}

impl CombinedSerializer {
    fn _build(
        schema: &PyDict,
        config: Option<&PyDict>,
        definitions: &mut DefinitionsBuilder<CombinedSerializer>,
    ) -> PyResult<CombinedSerializer> {
        let py = schema.py();
        let type_key = intern!(py, "type");

        if let Some(ser_schema) = schema.get_as::<&PyDict>(intern!(py, "serialization"))? {
            let op_ser_type: Option<&str> = ser_schema.get_as(type_key)?;
            match op_ser_type {
                Some("function-plain") => {
                    // `function-plain` is a special case, not included in `find_serializer` since it means
                    // something different in `schema.type`
                    // NOTE! we use the `schema` here, not `ser_schema`
                    return super::type_serializers::function::FunctionPlainSerializer::build(
                        schema,
                        config,
                        definitions,
                    )
                    .map_err(|err| py_schema_error_type!("Error building `function-plain` serializer:\n  {}", err));
                }
                Some("function-wrap") => {
                    // `function-wrap` is also a special case, not included in `find_serializer` since it mean
                    // something different in `schema.type`
                    // NOTE! we use the `schema` here, not `ser_schema`
                    return super::type_serializers::function::FunctionWrapSerializer::build(
                        schema,
                        config,
                        definitions,
                    )
                    .map_err(|err| py_schema_error_type!("Error building `function-wrap` serializer:\n  {}", err));
                }
                // applies to lists tuples and dicts, does not override the main schema `type`
                Some("include-exclude-sequence" | "include-exclude-dict") => (),
                // applies specifically to bytes, does not override the main schema `type`
                Some("base64") => (),
                Some(ser_type) => {
                    // otherwise if `schema.serialization.type` is defined, use that with `find_serializer`
                    // instead of `schema.type`. In this case it's an error if a serializer isn't found.
                    return Self::find_serializer(ser_type, ser_schema, config, definitions);
                }
                // if `schema.serialization.type` is None, fall back to `schema.type`
                None => (),
            };
        }

        let type_: &str = schema.get_as_req(type_key)?;
        Self::find_serializer(type_, schema, config, definitions)
    }
}

impl BuildSerializer for CombinedSerializer {
    // this value is never used, it's just here to satisfy the trait
    const EXPECTED_TYPE: &'static str = "";

    fn build(
        schema: &PyDict,
        config: Option<&PyDict>,
        definitions: &mut DefinitionsBuilder<CombinedSerializer>,
    ) -> PyResult<CombinedSerializer> {
        let py: Python = schema.py();
        if let Some(schema_ref) = schema.get_as::<String>(intern!(py, "ref"))? {
            let inner_ser = Self::_build(schema, config, definitions)?;
            let ser_id = definitions.add_definition(schema_ref, inner_ser)?;
            return Ok(DefinitionRefSerializer::from_id(ser_id));
        }

        Self::_build(schema, config, definitions)
    }
}

#[enum_dispatch(CombinedSerializer)]
pub(crate) trait TypeSerializer: Send + Sync + Clone + Debug {
    fn py_gc_traverse(&self, _visit: &PyVisit<'_>) -> Result<(), PyTraverseError> {
        Ok(())
    }
    fn py_gc_clear(&mut self) {}
    fn to_python(
        &self,
        value: &PyAny,
        include: Option<&PyAny>,
        exclude: Option<&PyAny>,
        extra: &Extra,
    ) -> PyResult<PyObject>;

    fn json_key<'py>(&self, key: &'py PyAny, extra: &Extra) -> PyResult<Cow<'py, str>>;

    fn _invalid_as_json_key<'py>(
        &self,
        key: &'py PyAny,
        extra: &Extra,
        expected_type: &'static str,
    ) -> PyResult<Cow<'py, str>> {
        match extra.ob_type_lookup.is_type(key, ObType::None) {
            IsType::Exact | IsType::Subclass => py_err!(PyTypeError; "`{}` not valid as object key", expected_type),
            IsType::False => {
                extra.warnings.on_fallback_py(self.get_name(), key, extra)?;
                infer_json_key(key, extra)
            }
        }
    }

    fn serde_serialize<S: serde::ser::Serializer>(
        &self,
        value: &PyAny,
        serializer: S,
        include: Option<&PyAny>,
        exclude: Option<&PyAny>,
        extra: &Extra,
    ) -> Result<S::Ok, S::Error>;

    fn get_name(&self) -> &str;

    /// Used by union serializers to decide if it's worth trying again while allowing subclasses
    fn retry_with_lax_check(&self) -> bool {
        false
    }

    fn get_default(&self, _py: Python) -> PyResult<Option<PyObject>> {
        Ok(None)
    }
}

pub(crate) struct PydanticSerializer<'py> {
    value: &'py PyAny,
    serializer: &'py CombinedSerializer,
    include: Option<&'py PyAny>,
    exclude: Option<&'py PyAny>,
    extra: &'py Extra<'py>,
}

impl<'py> PydanticSerializer<'py> {
    pub(crate) fn new(
        value: &'py PyAny,
        serializer: &'py CombinedSerializer,
        include: Option<&'py PyAny>,
        exclude: Option<&'py PyAny>,
        extra: &'py Extra<'py>,
    ) -> Self {
        Self {
            value,
            serializer,
            include,
            exclude,
            extra,
        }
    }
}

impl<'py> Serialize for PydanticSerializer<'py> {
    fn serialize<S: serde::ser::Serializer>(&self, serializer: S) -> Result<S::Ok, S::Error> {
        self.serializer
            .serde_serialize(self.value, serializer, self.include, self.exclude, self.extra)
    }
}

#[allow(clippy::too_many_arguments)]
pub(crate) fn to_json_bytes(
    value: &PyAny,
    serializer: &CombinedSerializer,
    include: Option<&PyAny>,
    exclude: Option<&PyAny>,
    extra: &Extra,
    indent: Option<usize>,
    expected_json_size: usize,
) -> PyResult<Vec<u8>> {
    let serializer = PydanticSerializer::new(value, serializer, include, exclude, extra);

    let writer: Vec<u8> = Vec::with_capacity(expected_json_size);
    let bytes = match indent {
        Some(indent) => {
            let indent = vec![b' '; indent];
            let formatter = PrettyFormatter::with_indent(&indent);
            let mut ser = serde_json::Serializer::with_formatter(writer, formatter);
            serializer.serialize(&mut ser).map_err(se_err_py_err)?;
            ser.into_inner()
        }
        None => {
            let mut ser = serde_json::Serializer::new(writer);
            serializer.serialize(&mut ser).map_err(se_err_py_err)?;
            ser.into_inner()
        }
    };
    Ok(bytes)
}

static DC_FIELD_MARKER: GILOnceCell<PyObject> = GILOnceCell::new();

/// needed to match the logic from dataclasses.fields `tuple(f for f in fields.values() if f._field_type is _FIELD)`
pub(super) fn get_field_marker(py: Python<'_>) -> PyResult<&PyAny> {
    let field_type_marker_obj = DC_FIELD_MARKER.get_or_try_init(py, || {
        let field_ = py.import("dataclasses")?.getattr("_FIELD")?;
        Ok::<PyObject, PyErr>(field_.into_py(py))
    })?;
    Ok(field_type_marker_obj.as_ref(py))
}

pub(super) fn dataclass_to_dict(dc: &PyAny) -> PyResult<&PyDict> {
    let py = dc.py();
    let dc_fields: &PyDict = dc.getattr(intern!(py, "__dataclass_fields__"))?.downcast()?;
    let dict = PyDict::new(py);

    let field_type_marker = get_field_marker(py)?;
    for (field_name, field) in dc_fields.iter() {
        let field_type = field.getattr(intern!(py, "_field_type"))?;
        if field_type.is(field_type_marker) {
            let field_name: &PyString = field_name.downcast()?;
            dict.set_item(field_name, dc.getattr(field_name)?)?;
        }
    }
    Ok(dict)
}
