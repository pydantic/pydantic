use std::{io, num::FpCategory};

use serde::{ser::Impossible, serde_if_integer128, Serialize, Serializer};
use serde_json::ser::{CompactFormatter, Formatter, PrettyFormatter, State};

use super::errors::PythonSerializerError;

macro_rules! tri {
    ($e:expr $(,)?) => {
        match $e {
            core::result::Result::Ok(val) => val,
            core::result::Result::Err(err) => return core::result::Result::Err(err),
        }
    };
}

type Result<T> = std::result::Result<T, PythonSerializerError>;
const TOKEN: &str = "$serde_json::private::Number";
pub struct PythonSerializer<W, F = CompactFormatter> {
    writer: W,
    formatter: F,
}

impl<W> PythonSerializer<W>
where
    W: io::Write,
{
    /// Creates a new JSON serializer.
    #[inline]
    pub fn new(writer: W) -> Self {
        PythonSerializer::with_formatter(writer, CompactFormatter)
    }
}

impl<'a, W> PythonSerializer<W, PrettyFormatter<'a>>
where
    W: io::Write,
{
    /// Creates a new JSON pretty print serializer.
    #[inline]
    pub fn pretty(writer: W) -> Self {
        PythonSerializer::with_formatter(writer, PrettyFormatter::new())
    }
}

impl<W, F> PythonSerializer<W, F>
where
    W: io::Write,
    F: Formatter,
{
    /// Creates a new JSON visitor whose output will be written to the writer
    /// specified.
    #[inline]
    pub fn with_formatter(writer: W, formatter: F) -> Self {
        PythonSerializer { writer, formatter }
    }

    /// Unwrap the `Writer` from the `Serializer`.
    #[inline]
    pub fn into_inner(self) -> W {
        self.writer
    }
}

impl<'a, W, F> Serializer for &'a mut PythonSerializer<W, F>
where
    W: io::Write,
    F: Formatter,
{
    type Ok = ();
    type Error = PythonSerializerError;

    type SerializeSeq = Compound<'a, W, F>;
    type SerializeTuple = Compound<'a, W, F>;
    type SerializeTupleStruct = Compound<'a, W, F>;
    type SerializeTupleVariant = Compound<'a, W, F>;
    type SerializeMap = Compound<'a, W, F>;
    type SerializeStruct = Compound<'a, W, F>;
    type SerializeStructVariant = Compound<'a, W, F>;

    #[inline]
    fn serialize_bool(self, value: bool) -> Result<()> {
        self.formatter
            .write_bool(&mut self.writer, value)
            .map_err(|e| PythonSerializerError { message: e.to_string() })
    }

    #[inline]
    fn serialize_i8(self, value: i8) -> Result<()> {
        self.formatter
            .write_i8(&mut self.writer, value)
            .map_err(|e| PythonSerializerError { message: e.to_string() })
    }

    fn serialize_i16(self, value: i16) -> Result<Self::Ok> {
        self.formatter
            .write_i16(&mut self.writer, value)
            .map_err(|e| PythonSerializerError { message: e.to_string() })
    }

    fn serialize_i32(self, value: i32) -> Result<Self::Ok> {
        self.formatter
            .write_i32(&mut self.writer, value)
            .map_err(|e| PythonSerializerError { message: e.to_string() })
    }

    fn serialize_i64(self, value: i64) -> Result<Self::Ok> {
        self.formatter
            .write_i64(&mut self.writer, value)
            .map_err(|e| PythonSerializerError { message: e.to_string() })
    }

    fn serialize_u8(self, value: u8) -> Result<Self::Ok> {
        self.formatter
            .write_u8(&mut self.writer, value)
            .map_err(|e| PythonSerializerError { message: e.to_string() })
    }

    fn serialize_u16(self, value: u16) -> Result<Self::Ok> {
        self.formatter
            .write_u16(&mut self.writer, value)
            .map_err(|e| PythonSerializerError { message: e.to_string() })
    }

    fn serialize_u32(self, value: u32) -> Result<Self::Ok> {
        self.formatter
            .write_u32(&mut self.writer, value)
            .map_err(|e| PythonSerializerError { message: e.to_string() })
    }

    fn serialize_u64(self, value: u64) -> Result<Self::Ok> {
        self.formatter
            .write_u64(&mut self.writer, value)
            .map_err(|e| PythonSerializerError { message: e.to_string() })
    }

    fn serialize_u128(self, value: u128) -> Result<()> {
        self.formatter
            .write_u128(&mut self.writer, value)
            .map_err(|e| PythonSerializerError { message: e.to_string() })
    }

    #[inline]
    fn serialize_f32(self, value: f32) -> Result<()> {
        match value.classify() {
            FpCategory::Nan => self
                .formatter
                .write_number_str(&mut self.writer, "NaN")
                .map_err(|e| PythonSerializerError { message: e.to_string() }),
            FpCategory::Infinite => {
                let infinity = if value.is_sign_negative() {
                    "-Infinity"
                } else {
                    "Infinity"
                };
                self.formatter
                    .write_number_str(&mut self.writer, infinity)
                    .map_err(|e| PythonSerializerError { message: e.to_string() })
            }
            _ => self
                .formatter
                .write_f32(&mut self.writer, value)
                .map_err(|e| PythonSerializerError { message: e.to_string() }),
        }
    }

    fn serialize_f64(self, value: f64) -> Result<Self::Ok> {
        match value.classify() {
            FpCategory::Nan => self
                .formatter
                .write_number_str(&mut self.writer, "NaN")
                .map_err(|e| PythonSerializerError { message: e.to_string() }),
            FpCategory::Infinite => {
                let infinity = if value.is_sign_negative() {
                    "-Infinity"
                } else {
                    "Infinity"
                };
                self.formatter
                    .write_number_str(&mut self.writer, infinity)
                    .map_err(|e| PythonSerializerError { message: e.to_string() })
            }
            _ => self
                .formatter
                .write_f64(&mut self.writer, value)
                .map_err(|e| PythonSerializerError { message: e.to_string() }),
        }
    }

    fn serialize_char(self, value: char) -> Result<Self::Ok> {
        // A char encoded as UTF-8 takes 4 bytes at most.
        let mut buf = [0; 4];
        self.serialize_str(value.encode_utf8(&mut buf))
    }

    fn serialize_str(self, value: &str) -> Result<Self::Ok> {
        format_escaped_str(&mut self.writer, &mut self.formatter, value)
            .map_err(|e| PythonSerializerError { message: e.to_string() })
    }

    fn serialize_bytes(self, value: &[u8]) -> Result<()> {
        self.formatter
            .write_byte_array(&mut self.writer, value)
            .map_err(|e| PythonSerializerError { message: e.to_string() })
    }

    fn serialize_none(self) -> Result<Self::Ok> {
        self.formatter
            .write_null(&mut self.writer)
            .map_err(|e| PythonSerializerError { message: e.to_string() })
    }

    fn serialize_some<T>(self, value: &T) -> Result<Self::Ok>
    where
        T: ?Sized + Serialize,
    {
        value.serialize(self)
    }

    fn serialize_unit(self) -> Result<Self::Ok> {
        self.formatter
            .write_null(&mut self.writer)
            .map_err(|e| PythonSerializerError { message: e.to_string() })
    }

    fn serialize_unit_struct(self, _name: &'static str) -> Result<Self::Ok> {
        self.serialize_unit()
    }

    fn serialize_unit_variant(
        self,
        _name: &'static str,
        _variant_index: u32,
        variant: &'static str,
    ) -> Result<Self::Ok> {
        self.serialize_str(variant)
    }

    fn serialize_newtype_struct<T: Serialize + ?Sized>(self, _name: &'static str, value: &T) -> Result<Self::Ok> {
        value.serialize(self)
    }

    fn serialize_newtype_variant<T: Serialize + ?Sized>(
        self,
        _name: &'static str,
        _variant_index: u32,
        variant: &'static str,
        value: &T,
    ) -> Result<Self::Ok> {
        tri!(self
            .formatter
            .begin_object(&mut self.writer)
            .map_err(|e| PythonSerializerError { message: e.to_string() }));
        tri!(self
            .formatter
            .begin_object_key(&mut self.writer, true)
            .map_err(|e| PythonSerializerError { message: e.to_string() }));
        tri!(self.serialize_str(variant));
        tri!(self
            .formatter
            .end_object_key(&mut self.writer)
            .map_err(|e| PythonSerializerError { message: e.to_string() }));
        tri!(self
            .formatter
            .begin_object_value(&mut self.writer)
            .map_err(|e| PythonSerializerError { message: e.to_string() }));
        tri!(value.serialize(&mut *self));
        tri!(self
            .formatter
            .end_object_value(&mut self.writer)
            .map_err(|e| PythonSerializerError { message: e.to_string() }));
        self.formatter
            .end_object(&mut self.writer)
            .map_err(|e| PythonSerializerError { message: e.to_string() })
    }

    fn serialize_seq(self, len: Option<usize>) -> Result<Self::SerializeSeq> {
        tri!(self
            .formatter
            .begin_array(&mut self.writer)
            .map_err(|e| PythonSerializerError { message: e.to_string() }));
        if len == Some(0) {
            tri!(self
                .formatter
                .end_array(&mut self.writer)
                .map_err(|e| PythonSerializerError { message: e.to_string() }));
            Ok(Compound::Map {
                ser: self,
                state: State::Empty,
            })
        } else {
            Ok(Compound::Map {
                ser: self,
                state: State::First,
            })
        }
    }

    fn serialize_tuple(self, len: usize) -> Result<Self::SerializeTuple> {
        self.serialize_seq(Some(len))
    }

    fn serialize_tuple_struct(self, _name: &'static str, len: usize) -> Result<Self::SerializeTupleStruct> {
        self.serialize_seq(Some(len))
    }

    fn serialize_tuple_variant(
        self,
        _name: &'static str,
        _variant_index: u32,
        variant: &'static str,
        len: usize,
    ) -> Result<Self::SerializeTupleVariant> {
        tri!(self
            .formatter
            .begin_object(&mut self.writer)
            .map_err(|e| PythonSerializerError { message: e.to_string() }));
        tri!(self
            .formatter
            .begin_object_key(&mut self.writer, true)
            .map_err(|e| PythonSerializerError { message: e.to_string() }));
        tri!(self.serialize_str(variant));
        tri!(self
            .formatter
            .end_object_key(&mut self.writer)
            .map_err(|e| PythonSerializerError { message: e.to_string() }));
        tri!(self
            .formatter
            .begin_object_value(&mut self.writer)
            .map_err(|e| PythonSerializerError { message: e.to_string() }));
        self.serialize_seq(Some(len))
    }

    fn serialize_map(self, len: Option<usize>) -> Result<Self::SerializeMap> {
        tri!(self
            .formatter
            .begin_object(&mut self.writer)
            .map_err(|e| PythonSerializerError { message: e.to_string() }));
        if len == Some(0) {
            tri!(self
                .formatter
                .end_object(&mut self.writer)
                .map_err(|e| PythonSerializerError { message: e.to_string() }));
            Ok(Compound::Map {
                ser: self,
                state: State::Empty,
            })
        } else {
            Ok(Compound::Map {
                ser: self,
                state: State::First,
            })
        }
    }

    fn serialize_struct(self, name: &'static str, len: usize) -> Result<Self::SerializeStruct> {
        match name {
            TOKEN => Ok(Compound::Number { ser: self }),
            _ => self.serialize_map(Some(len)),
        }
    }

    fn serialize_struct_variant(
        self,
        _name: &'static str,
        _variant_index: u32,
        variant: &'static str,
        len: usize,
    ) -> Result<Self::SerializeStructVariant> {
        tri!(self
            .formatter
            .begin_object(&mut self.writer)
            .map_err(|e| PythonSerializerError { message: e.to_string() }));
        tri!(self
            .formatter
            .begin_object_key(&mut self.writer, true)
            .map_err(|e| PythonSerializerError { message: e.to_string() }));
        tri!(self.serialize_str(variant));
        tri!(self
            .formatter
            .end_object_key(&mut self.writer)
            .map_err(|e| PythonSerializerError { message: e.to_string() }));
        tri!(self
            .formatter
            .begin_object_value(&mut self.writer)
            .map_err(|e| PythonSerializerError { message: e.to_string() }));
        self.serialize_map(Some(len))
    }
}

impl<'a, W, F> serde::ser::SerializeSeq for Compound<'a, W, F>
where
    W: io::Write,
    F: Formatter,
{
    type Ok = ();
    type Error = PythonSerializerError;

    #[inline]
    fn serialize_element<T>(&mut self, value: &T) -> Result<()>
    where
        T: ?Sized + Serialize,
    {
        match self {
            Compound::Map { ser, state } => {
                tri!(ser
                    .formatter
                    .begin_array_value(&mut ser.writer, *state == State::First)
                    .map_err(|e| PythonSerializerError { message: e.to_string() }));
                *state = State::Rest;
                tri!(value.serialize(&mut **ser));
                tri!(ser
                    .formatter
                    .end_array_value(&mut ser.writer)
                    .map_err(|e| PythonSerializerError { message: e.to_string() }));
                Ok(())
            }
            Compound::Number { .. } => unreachable!(),
        }
    }

    fn end(self) -> Result<()> {
        match self {
            Compound::Map { ser, state } => {
                match state {
                    State::Empty => {}
                    _ => tri!(ser
                        .formatter
                        .end_array(&mut ser.writer)
                        .map_err(|e| PythonSerializerError { message: e.to_string() })),
                }
                Ok(())
            }
            Compound::Number { .. } => unreachable!(),
        }
    }
}

impl<'a, W, F> serde::ser::SerializeTuple for Compound<'a, W, F>
where
    W: io::Write,
    F: Formatter,
{
    type Ok = ();
    type Error = PythonSerializerError;

    #[inline]
    fn serialize_element<T>(&mut self, value: &T) -> Result<()>
    where
        T: ?Sized + Serialize,
    {
        serde::ser::SerializeSeq::serialize_element(self, value)
    }

    #[inline]
    fn end(self) -> Result<()> {
        serde::ser::SerializeSeq::end(self)
    }
}

impl<'a, W, F> serde::ser::SerializeTupleStruct for Compound<'a, W, F>
where
    W: io::Write,
    F: Formatter,
{
    type Ok = ();
    type Error = PythonSerializerError;

    #[inline]
    fn serialize_field<T>(&mut self, value: &T) -> Result<()>
    where
        T: ?Sized + Serialize,
    {
        serde::ser::SerializeSeq::serialize_element(self, value)
    }

    #[inline]
    fn end(self) -> Result<()> {
        serde::ser::SerializeSeq::end(self)
    }
}

impl<'a, W, F> serde::ser::SerializeTupleVariant for Compound<'a, W, F>
where
    W: io::Write,
    F: Formatter,
{
    type Ok = ();
    type Error = PythonSerializerError;

    #[inline]
    fn serialize_field<T>(&mut self, value: &T) -> Result<()>
    where
        T: ?Sized + Serialize,
    {
        serde::ser::SerializeSeq::serialize_element(self, value)
    }

    #[inline]
    fn end(self) -> Result<()> {
        match self {
            Compound::Map { ser, state } => {
                match state {
                    State::Empty => {}
                    _ => tri!(ser
                        .formatter
                        .end_array(&mut ser.writer)
                        .map_err(|e| PythonSerializerError { message: e.to_string() })),
                }
                tri!(ser
                    .formatter
                    .end_object_value(&mut ser.writer)
                    .map_err(|e| PythonSerializerError { message: e.to_string() }));
                tri!(ser
                    .formatter
                    .end_object(&mut ser.writer)
                    .map_err(|e| PythonSerializerError { message: e.to_string() }));
                Ok(())
            }
            Compound::Number { .. } => unreachable!(),
        }
    }
}

impl<'a, W, F> serde::ser::SerializeMap for Compound<'a, W, F>
where
    W: io::Write,
    F: Formatter,
{
    type Ok = ();
    type Error = PythonSerializerError;

    #[inline]
    fn serialize_key<T>(&mut self, key: &T) -> Result<()>
    where
        T: ?Sized + Serialize,
    {
        match self {
            Compound::Map { ser, state } => {
                tri!(ser
                    .formatter
                    .begin_object_key(&mut ser.writer, *state == State::First)
                    .map_err(|e| PythonSerializerError { message: e.to_string() }));
                *state = State::Rest;

                tri!(key.serialize(MapKeySerializer { ser: *ser }));

                tri!(ser
                    .formatter
                    .end_object_key(&mut ser.writer)
                    .map_err(|e| PythonSerializerError { message: e.to_string() }));
                Ok(())
            }
            Compound::Number { .. } => unreachable!(),
        }
    }

    #[inline]
    fn serialize_value<T>(&mut self, value: &T) -> Result<()>
    where
        T: ?Sized + Serialize,
    {
        match self {
            Compound::Map { ser, .. } => {
                tri!(ser
                    .formatter
                    .begin_object_value(&mut ser.writer)
                    .map_err(|e| PythonSerializerError { message: e.to_string() }));
                tri!(value.serialize(&mut **ser));
                tri!(ser
                    .formatter
                    .end_object_value(&mut ser.writer)
                    .map_err(|e| PythonSerializerError { message: e.to_string() }));
                Ok(())
            }
            Compound::Number { .. } => unreachable!(),
        }
    }

    #[inline]
    fn end(self) -> Result<()> {
        match self {
            Compound::Map { ser, state } => {
                match state {
                    State::Empty => {}
                    _ => tri!(ser
                        .formatter
                        .end_object(&mut ser.writer)
                        .map_err(|e| PythonSerializerError { message: e.to_string() })),
                }
                Ok(())
            }
            Compound::Number { .. } => unreachable!(),
        }
    }
}

impl<'a, W, F> serde::ser::SerializeStruct for Compound<'a, W, F>
where
    W: io::Write,
    F: Formatter,
{
    type Ok = ();
    type Error = PythonSerializerError;

    #[inline]
    fn serialize_field<T>(&mut self, key: &'static str, value: &T) -> Result<()>
    where
        T: ?Sized + Serialize,
    {
        match self {
            Compound::Map { .. } => serde::ser::SerializeMap::serialize_entry(self, key, value),
            Compound::Number { ser, .. } => {
                if key == TOKEN {
                    tri!(value.serialize(NumberStrEmitter(ser)));
                    Ok(())
                } else {
                    Err(invalid_number())
                }
            }
        }
    }

    #[inline]
    fn end(self) -> Result<()> {
        match self {
            Compound::Map { .. } => serde::ser::SerializeMap::end(self),
            Compound::Number { .. } => Ok(()),
        }
    }
}

impl<'a, W, F> serde::ser::SerializeStructVariant for Compound<'a, W, F>
where
    W: io::Write,
    F: Formatter,
{
    type Ok = ();
    type Error = PythonSerializerError;

    #[inline]
    fn serialize_field<T>(&mut self, key: &'static str, value: &T) -> Result<()>
    where
        T: ?Sized + Serialize,
    {
        match *self {
            Compound::Map { .. } => serde::ser::SerializeStruct::serialize_field(self, key, value),
            Compound::Number { .. } => unreachable!(),
        }
    }

    #[inline]
    fn end(self) -> Result<()> {
        match self {
            Compound::Map { ser, state } => {
                match state {
                    State::Empty => {}
                    _ => tri!(ser
                        .formatter
                        .end_object(&mut ser.writer)
                        .map_err(|e| PythonSerializerError { message: e.to_string() })),
                }
                tri!(ser
                    .formatter
                    .end_object_value(&mut ser.writer)
                    .map_err(|e| PythonSerializerError { message: e.to_string() }));
                tri!(ser
                    .formatter
                    .end_object(&mut ser.writer)
                    .map_err(|e| PythonSerializerError { message: e.to_string() }));
                Ok(())
            }
            Compound::Number { .. } => unreachable!(),
        }
    }
}

fn format_escaped_str<W, F>(writer: &mut W, formatter: &mut F, value: &str) -> io::Result<()>
where
    W: ?Sized + io::Write,
    F: ?Sized + Formatter,
{
    tri!(formatter.begin_string(writer));
    tri!(format_escaped_str_contents(writer, formatter, value));
    formatter.end_string(writer)
}

fn format_escaped_str_contents<W, F>(writer: &mut W, formatter: &mut F, value: &str) -> io::Result<()>
where
    W: ?Sized + io::Write,
    F: ?Sized + Formatter,
{
    let bytes = value.as_bytes();

    let mut start = 0;

    for (i, &byte) in bytes.iter().enumerate() {
        let escape = ESCAPE[byte as usize];
        if escape == 0 {
            continue;
        }

        if start < i {
            tri!(formatter.write_string_fragment(writer, &value[start..i]));
        }

        let char_escape = CharEscape::from_escape_table(escape, byte);
        tri!(formatter.write_char_escape(writer, char_escape));

        start = i + 1;
    }

    if start == bytes.len() {
        return Ok(());
    }

    formatter.write_string_fragment(writer, &value[start..])
}

const BB: u8 = b'b'; // \x08
const TT: u8 = b't'; // \x09
const NN: u8 = b'n'; // \x0A
const FF: u8 = b'f'; // \x0C
const RR: u8 = b'r'; // \x0D
const QU: u8 = b'"'; // \x22
const BS: u8 = b'\\'; // \x5C
const UU: u8 = b'u'; // \x00...\x1F except the ones above
const __: u8 = 0;

// Lookup table of escape sequences. A value of b'x' at index i means that byte
// i is escaped as "\x" in JSON. A value of 0 means that byte i is not escaped.
static ESCAPE: [u8; 256] = [
    //   1   2   3   4   5   6   7   8   9   A   B   C   D   E   F
    UU, UU, UU, UU, UU, UU, UU, UU, BB, TT, NN, UU, FF, RR, UU, UU, // 0
    UU, UU, UU, UU, UU, UU, UU, UU, UU, UU, UU, UU, UU, UU, UU, UU, // 1
    __, __, QU, __, __, __, __, __, __, __, __, __, __, __, __, __, // 2
    __, __, __, __, __, __, __, __, __, __, __, __, __, __, __, __, // 3
    __, __, __, __, __, __, __, __, __, __, __, __, __, __, __, __, // 4
    __, __, __, __, __, __, __, __, __, __, __, __, BS, __, __, __, // 5
    __, __, __, __, __, __, __, __, __, __, __, __, __, __, __, __, // 6
    __, __, __, __, __, __, __, __, __, __, __, __, __, __, __, __, // 7
    __, __, __, __, __, __, __, __, __, __, __, __, __, __, __, __, // 8
    __, __, __, __, __, __, __, __, __, __, __, __, __, __, __, __, // 9
    __, __, __, __, __, __, __, __, __, __, __, __, __, __, __, __, // A
    __, __, __, __, __, __, __, __, __, __, __, __, __, __, __, __, // B
    __, __, __, __, __, __, __, __, __, __, __, __, __, __, __, __, // C
    __, __, __, __, __, __, __, __, __, __, __, __, __, __, __, __, // D
    __, __, __, __, __, __, __, __, __, __, __, __, __, __, __, __, // E
    __, __, __, __, __, __, __, __, __, __, __, __, __, __, __, __, // F
];

pub enum Compound<'a, W: 'a, F: 'a> {
    Map {
        ser: &'a mut PythonSerializer<W, F>,
        state: State,
    },
    Number {
        ser: &'a mut PythonSerializer<W, F>,
    },
}

/// Represents a character escape code in a type-safe manner.
pub enum CharEscape {}

impl CharEscape {
    #[inline]
    fn from_escape_table(escape: u8, byte: u8) -> serde_json::ser::CharEscape {
        match escape {
            self::BB => serde_json::ser::CharEscape::Backspace,
            self::TT => serde_json::ser::CharEscape::Tab,
            self::NN => serde_json::ser::CharEscape::LineFeed,
            self::FF => serde_json::ser::CharEscape::FormFeed,
            self::RR => serde_json::ser::CharEscape::CarriageReturn,
            self::QU => serde_json::ser::CharEscape::Quote,
            self::BS => serde_json::ser::CharEscape::ReverseSolidus,
            self::UU => serde_json::ser::CharEscape::AsciiControl(byte),
            _ => unreachable!(),
        }
    }
}

struct MapKeySerializer<'a, W: 'a, F: 'a> {
    ser: &'a mut PythonSerializer<W, F>,
}

fn key_must_be_a_string() -> PythonSerializerError {
    PythonSerializerError {
        message: "Key must be a string".to_string(),
    }
}
fn invalid_number() -> PythonSerializerError {
    PythonSerializerError {
        message: "Invalid Number".to_string(),
    }
}

impl<'a, W, F> serde::ser::Serializer for MapKeySerializer<'a, W, F>
where
    W: io::Write,
    F: Formatter,
{
    type Ok = ();
    type Error = PythonSerializerError;

    #[inline]
    fn serialize_str(self, value: &str) -> Result<()> {
        self.ser.serialize_str(value)
    }

    #[inline]
    fn serialize_unit_variant(self, _name: &'static str, _variant_index: u32, variant: &'static str) -> Result<()> {
        self.ser.serialize_str(variant)
    }

    #[inline]
    fn serialize_newtype_struct<T>(self, _name: &'static str, value: &T) -> Result<()>
    where
        T: ?Sized + Serialize,
    {
        value.serialize(self)
    }

    type SerializeSeq = Impossible<(), PythonSerializerError>;
    type SerializeTuple = Impossible<(), PythonSerializerError>;
    type SerializeTupleStruct = Impossible<(), PythonSerializerError>;
    type SerializeTupleVariant = Impossible<(), PythonSerializerError>;
    type SerializeMap = Impossible<(), PythonSerializerError>;
    type SerializeStruct = Impossible<(), PythonSerializerError>;
    type SerializeStructVariant = Impossible<(), PythonSerializerError>;

    fn serialize_bool(self, _value: bool) -> Result<()> {
        Err(key_must_be_a_string())
    }

    fn serialize_i8(self, value: i8) -> Result<()> {
        tri!(self
            .ser
            .formatter
            .begin_string(&mut self.ser.writer)
            .map_err(|e| PythonSerializerError { message: e.to_string() }));
        tri!(self
            .ser
            .formatter
            .write_i8(&mut self.ser.writer, value)
            .map_err(|e| PythonSerializerError { message: e.to_string() }));
        tri!(self
            .ser
            .formatter
            .end_string(&mut self.ser.writer)
            .map_err(|e| PythonSerializerError { message: e.to_string() }));
        Ok(())
    }

    fn serialize_i16(self, value: i16) -> Result<()> {
        tri!(self
            .ser
            .formatter
            .begin_string(&mut self.ser.writer)
            .map_err(|e| PythonSerializerError { message: e.to_string() }));
        tri!(self
            .ser
            .formatter
            .write_i16(&mut self.ser.writer, value)
            .map_err(|e| PythonSerializerError { message: e.to_string() }));
        tri!(self
            .ser
            .formatter
            .end_string(&mut self.ser.writer)
            .map_err(|e| PythonSerializerError { message: e.to_string() }));
        Ok(())
    }

    fn serialize_i32(self, value: i32) -> Result<()> {
        tri!(self
            .ser
            .formatter
            .begin_string(&mut self.ser.writer)
            .map_err(|e| PythonSerializerError { message: e.to_string() }));
        tri!(self
            .ser
            .formatter
            .write_i32(&mut self.ser.writer, value)
            .map_err(|e| PythonSerializerError { message: e.to_string() }));
        tri!(self
            .ser
            .formatter
            .end_string(&mut self.ser.writer)
            .map_err(|e| PythonSerializerError { message: e.to_string() }));
        Ok(())
    }

    fn serialize_i64(self, value: i64) -> Result<()> {
        tri!(self
            .ser
            .formatter
            .begin_string(&mut self.ser.writer)
            .map_err(|e| PythonSerializerError { message: e.to_string() }));
        tri!(self
            .ser
            .formatter
            .write_i64(&mut self.ser.writer, value)
            .map_err(|e| PythonSerializerError { message: e.to_string() }));
        tri!(self
            .ser
            .formatter
            .end_string(&mut self.ser.writer)
            .map_err(|e| PythonSerializerError { message: e.to_string() }));
        Ok(())
    }

    serde_if_integer128! {
        fn serialize_i128(self, value: i128) -> Result<()> {
            tri!(self
                .ser
                .formatter
                .begin_string(&mut self.ser.writer)
                .map_err(|e| PythonSerializerError { message: e.to_string() }));
            tri!(self
                .ser
                .formatter
                .write_number_str(&mut self.ser.writer, &value.to_string())
                .map_err(|e| PythonSerializerError { message: e.to_string() }));
            tri!(self
                .ser
                .formatter
                .end_string(&mut self.ser.writer)
                .map_err(|e| PythonSerializerError { message: e.to_string() }));
            Ok(())
        }
    }

    fn serialize_u8(self, value: u8) -> Result<()> {
        tri!(self
            .ser
            .formatter
            .begin_string(&mut self.ser.writer)
            .map_err(|e| PythonSerializerError { message: e.to_string() }));
        tri!(self
            .ser
            .formatter
            .write_u8(&mut self.ser.writer, value)
            .map_err(|e| PythonSerializerError { message: e.to_string() }));
        tri!(self
            .ser
            .formatter
            .end_string(&mut self.ser.writer)
            .map_err(|e| PythonSerializerError { message: e.to_string() }));
        Ok(())
    }

    fn serialize_u16(self, value: u16) -> Result<()> {
        tri!(self
            .ser
            .formatter
            .begin_string(&mut self.ser.writer)
            .map_err(|e| PythonSerializerError { message: e.to_string() }));
        tri!(self
            .ser
            .formatter
            .write_u16(&mut self.ser.writer, value)
            .map_err(|e| PythonSerializerError { message: e.to_string() }));
        tri!(self
            .ser
            .formatter
            .end_string(&mut self.ser.writer)
            .map_err(|e| PythonSerializerError { message: e.to_string() }));
        Ok(())
    }

    fn serialize_u32(self, value: u32) -> Result<()> {
        tri!(self
            .ser
            .formatter
            .begin_string(&mut self.ser.writer)
            .map_err(|e| PythonSerializerError { message: e.to_string() }));
        tri!(self
            .ser
            .formatter
            .write_u32(&mut self.ser.writer, value)
            .map_err(|e| PythonSerializerError { message: e.to_string() }));
        tri!(self
            .ser
            .formatter
            .end_string(&mut self.ser.writer)
            .map_err(|e| PythonSerializerError { message: e.to_string() }));
        Ok(())
    }

    fn serialize_u64(self, value: u64) -> Result<()> {
        tri!(self
            .ser
            .formatter
            .begin_string(&mut self.ser.writer)
            .map_err(|e| PythonSerializerError { message: e.to_string() }));
        tri!(self
            .ser
            .formatter
            .write_u64(&mut self.ser.writer, value)
            .map_err(|e| PythonSerializerError { message: e.to_string() }));
        tri!(self
            .ser
            .formatter
            .end_string(&mut self.ser.writer)
            .map_err(|e| PythonSerializerError { message: e.to_string() }));
        Ok(())
    }

    serde_if_integer128! {
        fn serialize_u128(self, value: u128) -> Result<()> {
            tri!(self
                .ser
                .formatter
                .begin_string(&mut self.ser.writer)
                .map_err(|e| PythonSerializerError { message: e.to_string() }));
            tri!(self
                .ser
                .formatter
                .write_number_str(&mut self.ser.writer, &value.to_string())
                .map_err(|e| PythonSerializerError { message: e.to_string() }));
            tri!(self
                .ser
                .formatter
                .end_string(&mut self.ser.writer)
                .map_err(|e| PythonSerializerError { message: e.to_string() }));
            Ok(())
        }
    }

    fn serialize_f32(self, _value: f32) -> Result<()> {
        Err(key_must_be_a_string())
    }

    fn serialize_f64(self, _value: f64) -> Result<()> {
        Err(key_must_be_a_string())
    }

    fn serialize_char(self, value: char) -> Result<()> {
        self.ser.serialize_str(&value.to_string())
    }

    fn serialize_bytes(self, _value: &[u8]) -> Result<()> {
        Err(key_must_be_a_string())
    }

    fn serialize_unit(self) -> Result<()> {
        Err(key_must_be_a_string())
    }

    fn serialize_unit_struct(self, _name: &'static str) -> Result<()> {
        Err(key_must_be_a_string())
    }

    fn serialize_newtype_variant<T>(
        self,
        _name: &'static str,
        _variant_index: u32,
        _variant: &'static str,
        _value: &T,
    ) -> Result<()>
    where
        T: ?Sized + Serialize,
    {
        Err(key_must_be_a_string())
    }

    fn serialize_none(self) -> Result<()> {
        Err(key_must_be_a_string())
    }

    fn serialize_some<T>(self, _value: &T) -> Result<()>
    where
        T: ?Sized + Serialize,
    {
        Err(key_must_be_a_string())
    }

    fn serialize_seq(self, _len: Option<usize>) -> Result<Self::SerializeSeq> {
        Err(key_must_be_a_string())
    }

    fn serialize_tuple(self, _len: usize) -> Result<Self::SerializeTuple> {
        Err(key_must_be_a_string())
    }

    fn serialize_tuple_struct(self, _name: &'static str, _len: usize) -> Result<Self::SerializeTupleStruct> {
        Err(key_must_be_a_string())
    }

    fn serialize_tuple_variant(
        self,
        _name: &'static str,
        _variant_index: u32,
        _variant: &'static str,
        _len: usize,
    ) -> Result<Self::SerializeTupleVariant> {
        Err(key_must_be_a_string())
    }

    fn serialize_map(self, _len: Option<usize>) -> Result<Self::SerializeMap> {
        Err(key_must_be_a_string())
    }

    fn serialize_struct(self, _name: &'static str, _len: usize) -> Result<Self::SerializeStruct> {
        Err(key_must_be_a_string())
    }

    fn serialize_struct_variant(
        self,
        _name: &'static str,
        _variant_index: u32,
        _variant: &'static str,
        _len: usize,
    ) -> Result<Self::SerializeStructVariant> {
        Err(key_must_be_a_string())
    }

    fn collect_str<T>(self, value: &T) -> Result<()>
    where
        T: ?Sized + std::fmt::Display,
    {
        self.ser.collect_str(value)
    }
}

struct NumberStrEmitter<'a, W: 'a + io::Write, F: 'a + Formatter>(&'a mut PythonSerializer<W, F>);

impl<'a, W: io::Write, F: Formatter> serde::ser::Serializer for NumberStrEmitter<'a, W, F> {
    type Ok = ();
    type Error = PythonSerializerError;

    type SerializeSeq = Impossible<(), PythonSerializerError>;
    type SerializeTuple = Impossible<(), PythonSerializerError>;
    type SerializeTupleStruct = Impossible<(), PythonSerializerError>;
    type SerializeTupleVariant = Impossible<(), PythonSerializerError>;
    type SerializeMap = Impossible<(), PythonSerializerError>;
    type SerializeStruct = Impossible<(), PythonSerializerError>;
    type SerializeStructVariant = Impossible<(), PythonSerializerError>;

    fn serialize_bool(self, _v: bool) -> Result<()> {
        Err(invalid_number())
    }

    fn serialize_i8(self, _v: i8) -> Result<()> {
        Err(invalid_number())
    }

    fn serialize_i16(self, _v: i16) -> Result<()> {
        Err(invalid_number())
    }

    fn serialize_i32(self, _v: i32) -> Result<()> {
        Err(invalid_number())
    }

    fn serialize_i64(self, _v: i64) -> Result<()> {
        Err(invalid_number())
    }

    serde_if_integer128! {
        fn serialize_i128(self, _v: i128) -> Result<()> {
            Err(invalid_number())
        }
    }

    fn serialize_u8(self, _v: u8) -> Result<()> {
        Err(invalid_number())
    }

    fn serialize_u16(self, _v: u16) -> Result<()> {
        Err(invalid_number())
    }

    fn serialize_u32(self, _v: u32) -> Result<()> {
        Err(invalid_number())
    }

    fn serialize_u64(self, _v: u64) -> Result<()> {
        Err(invalid_number())
    }

    serde_if_integer128! {
        fn serialize_u128(self, _v: u128) -> Result<()> {
            Err(invalid_number())
        }
    }

    fn serialize_f32(self, _v: f32) -> Result<()> {
        Err(invalid_number())
    }

    fn serialize_f64(self, _v: f64) -> Result<()> {
        Err(invalid_number())
    }

    fn serialize_char(self, _v: char) -> Result<()> {
        Err(invalid_number())
    }

    fn serialize_str(self, value: &str) -> Result<()> {
        let NumberStrEmitter(serializer) = self;
        serializer
            .formatter
            .write_number_str(&mut serializer.writer, value)
            .map_err(|e| PythonSerializerError { message: e.to_string() })
    }

    fn serialize_bytes(self, _value: &[u8]) -> Result<()> {
        Err(invalid_number())
    }

    fn serialize_none(self) -> Result<()> {
        Err(invalid_number())
    }

    fn serialize_some<T>(self, _value: &T) -> Result<()>
    where
        T: ?Sized + Serialize,
    {
        Err(invalid_number())
    }

    fn serialize_unit(self) -> Result<()> {
        Err(invalid_number())
    }

    fn serialize_unit_struct(self, _name: &'static str) -> Result<()> {
        Err(invalid_number())
    }

    fn serialize_unit_variant(self, _name: &'static str, _variant_index: u32, _variant: &'static str) -> Result<()> {
        Err(invalid_number())
    }

    fn serialize_newtype_struct<T>(self, _name: &'static str, _value: &T) -> Result<()>
    where
        T: ?Sized + Serialize,
    {
        Err(invalid_number())
    }

    fn serialize_newtype_variant<T>(
        self,
        _name: &'static str,
        _variant_index: u32,
        _variant: &'static str,
        _value: &T,
    ) -> Result<()>
    where
        T: ?Sized + Serialize,
    {
        Err(invalid_number())
    }

    fn serialize_seq(self, _len: Option<usize>) -> Result<Self::SerializeSeq> {
        Err(invalid_number())
    }

    fn serialize_tuple(self, _len: usize) -> Result<Self::SerializeTuple> {
        Err(invalid_number())
    }

    fn serialize_tuple_struct(self, _name: &'static str, _len: usize) -> Result<Self::SerializeTupleStruct> {
        Err(invalid_number())
    }

    fn serialize_tuple_variant(
        self,
        _name: &'static str,
        _variant_index: u32,
        _variant: &'static str,
        _len: usize,
    ) -> Result<Self::SerializeTupleVariant> {
        Err(invalid_number())
    }

    fn serialize_map(self, _len: Option<usize>) -> Result<Self::SerializeMap> {
        Err(invalid_number())
    }

    fn serialize_struct(self, _name: &'static str, _len: usize) -> Result<Self::SerializeStruct> {
        Err(invalid_number())
    }

    fn serialize_struct_variant(
        self,
        _name: &'static str,
        _variant_index: u32,
        _variant: &'static str,
        _len: usize,
    ) -> Result<Self::SerializeStructVariant> {
        Err(invalid_number())
    }
}
