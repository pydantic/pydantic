use std::borrow::Cow;
use std::str::FromStr;

use crate::build_tools::py_schema_err;
use crate::errors::ErrorType;
use crate::input::EitherBytes;
use crate::serializers::BytesMode;
use crate::tools::SchemaDict;
use base64::engine::general_purpose::GeneralPurpose;
use base64::engine::{DecodePaddingMode, GeneralPurposeConfig};
use base64::{alphabet, DecodeError, Engine};
use pyo3::types::{PyDict, PyString};
use pyo3::{intern, prelude::*};
use speedate::TimestampUnit;

const URL_SAFE_OPTIONAL_PADDING: GeneralPurpose = GeneralPurpose::new(
    &alphabet::URL_SAFE,
    GeneralPurposeConfig::new().with_decode_padding_mode(DecodePaddingMode::Indifferent),
);
const STANDARD_OPTIONAL_PADDING: GeneralPurpose = GeneralPurpose::new(
    &alphabet::STANDARD,
    GeneralPurposeConfig::new().with_decode_padding_mode(DecodePaddingMode::Indifferent),
);

#[derive(Default, Debug, Clone, Copy, PartialEq, Eq)]
pub enum TemporalUnitMode {
    Seconds,
    Milliseconds,
    #[default]
    Infer,
}

impl FromStr for TemporalUnitMode {
    type Err = PyErr;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s {
            "seconds" => Ok(Self::Seconds),
            "milliseconds" => Ok(Self::Milliseconds),
            "infer" => Ok(Self::Infer),

            s => py_schema_err!(
                "Invalid temporal_unit_mode serialization mode: `{}`, expected seconds, milliseconds or infer",
                s
            ),
        }
    }
}

impl TemporalUnitMode {
    pub fn from_config(config: Option<&Bound<'_, PyDict>>) -> PyResult<Self> {
        let Some(config_dict) = config else {
            return Ok(Self::default());
        };
        let raw_mode = config_dict.get_as::<Bound<'_, PyString>>(intern!(config_dict.py(), "val_temporal_unit"))?;
        let temporal_unit = raw_mode.map_or_else(
            || Ok(TemporalUnitMode::default()),
            |raw| TemporalUnitMode::from_str(&raw.to_cow()?),
        )?;
        Ok(temporal_unit)
    }
}

impl From<TemporalUnitMode> for TimestampUnit {
    fn from(value: TemporalUnitMode) -> Self {
        match value {
            TemporalUnitMode::Seconds => TimestampUnit::Second,
            TemporalUnitMode::Milliseconds => TimestampUnit::Millisecond,
            TemporalUnitMode::Infer => TimestampUnit::Infer,
        }
    }
}

#[derive(Default, Debug, Clone, Copy, PartialEq, Eq)]
pub struct ValBytesMode {
    pub ser: BytesMode,
}

impl ValBytesMode {
    pub fn from_config(config: Option<&Bound<'_, PyDict>>) -> PyResult<Self> {
        let Some(config_dict) = config else {
            return Ok(Self::default());
        };
        let raw_mode = config_dict.get_as::<Bound<'_, PyString>>(intern!(config_dict.py(), "val_json_bytes"))?;
        let ser_mode = raw_mode.map_or_else(|| Ok(BytesMode::default()), |raw| BytesMode::from_str(&raw.to_cow()?))?;
        Ok(Self { ser: ser_mode })
    }

    pub fn deserialize_string<'py>(self, s: &str) -> Result<EitherBytes<'_, 'py>, ErrorType> {
        match self.ser {
            BytesMode::Utf8 => Ok(EitherBytes::Cow(Cow::Borrowed(s.as_bytes()))),
            BytesMode::Base64 => URL_SAFE_OPTIONAL_PADDING
                .decode(s)
                .or_else(|err| match err {
                    DecodeError::InvalidByte(_, b'/' | b'+') => STANDARD_OPTIONAL_PADDING.decode(s),
                    _ => Err(err),
                })
                .map(EitherBytes::from)
                .map_err(|err| ErrorType::BytesInvalidEncoding {
                    encoding: "base64".to_string(),
                    encoding_error: err.to_string(),
                    context: None,
                }),
            BytesMode::Hex => match hex::decode(s) {
                Ok(vec) => Ok(EitherBytes::from(vec)),
                Err(err) => Err(ErrorType::BytesInvalidEncoding {
                    encoding: "hex".to_string(),
                    encoding_error: err.to_string(),
                    context: None,
                }),
            },
        }
    }
}
