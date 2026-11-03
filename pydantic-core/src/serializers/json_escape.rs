use std::io;

use serde_json::ser::Formatter;

/// Write `value` to `writer` as a JSON string: wrapped in double quotes, with `"`, `\`
/// and control characters (below U+0020) escaped. Other characters, including non-ASCII
/// ones, are written as is.
pub(super) fn format_escaped_str<W, F>(writer: &mut W, formatter: &mut F, value: &str) -> io::Result<()>
where
    W: ?Sized + io::Write,
    F: ?Sized + Formatter,
{
    formatter.begin_string(writer)?;
    format_escaped_str_contents(writer, formatter, value)?;
    formatter.end_string(writer)
}

fn format_escaped_str_contents<W, F>(writer: &mut W, formatter: &mut F, value: &str) -> io::Result<()>
where
    W: ?Sized + io::Write,
    F: ?Sized + Formatter,
{
    let bytes = value.as_bytes();

    let mut start = 0;
    let mut i = 0;

    while i < bytes.len() {
        let byte = bytes[i];
        let escape = ESCAPE[byte as usize];
        if escape == 0 {
            // Only skip ahead after a byte that doesn't need escaping, so that
            // consecutive escaped bytes don't pay for the block scan:
            i = skip_to_escape(bytes, i + 1);
            continue;
        }

        if start < i {
            formatter.write_string_fragment(writer, &value[start..i])?;
        }

        let char_escape = CharEscape::from_escape_table(escape, byte);
        formatter.write_char_escape(writer, char_escape)?;

        i += 1;
        start = i;
    }

    if start == bytes.len() {
        return Ok(());
    }

    formatter.write_string_fragment(writer, &value[start..])
}

const U32_LEN: usize = size_of::<u32>();
const BLOCK_SIZE: usize = 4 * U32_LEN;

/// Returns the index of the first byte at or after `i` that needs to be escaped
/// (according to `ESCAPE`), or `bytes.len()` if there is none.
///
/// Instead of iterating over bytes one by one, they are checked 16 at a time (as four `u32` words),
/// and the remaining 0 to 15 bytes are checked one by one.
/// Code is adapted from https://github.com/serde-rs/json/pull/1363.
/// References:
/// - https://bits.stephan-brumme.com/null.html
/// - https://en.wikipedia.org/wiki/SWAR
#[inline]
fn skip_to_escape(bytes: &[u8], mut i: usize) -> usize {
    // The idea here is to process blocks of 16 bytes, but have the code iterate over the block
    // sequentially in "sub-blocks" of 4 bytes (where the bitwise operations are performed).
    // The compiler can then optimize the iteration in `block_needs_escaping()` into SIMD instructions.
    for block in bytes[i..].as_chunks::<BLOCK_SIZE>().0 {
        if block_needs_escaping(block) {
            for word in block.as_chunks::<U32_LEN>().0 {
                let bits = escape_bits(*word);
                if bits != 0 {
                    return i + bits.trailing_zeros() as usize / 8;
                }
                i += U32_LEN;
            }
        }
        i += BLOCK_SIZE;
    }

    while i < bytes.len() && ESCAPE[bytes[i] as usize] == 0 {
        i += 1;
    }
    i
}

#[inline]
fn block_needs_escaping(block: &[u8; BLOCK_SIZE]) -> bool {
    block
        .as_chunks::<U32_LEN>()
        .0
        .iter()
        .copied()
        .map(escape_bits)
        .fold(0, |acc, bits| acc | bits)
        != 0
}

/// Sets the high bit of the first byte of `word` that needs to be escaped to 1, other bits below it to 0.
/// Bits of later bytes are meaningless. `word` is read as little-endian.
///
/// Each byte of the result is `0x80` (`1000 0000`) if the corresponding byte of the `word` input
/// needs to be escaped, `0x00` otherwise. Bytes after the first `0x80` may be wrongly set to
/// `0x80`: this is fine, as callers only use the first `0x80` byte.
///
/// For example, `a"b\n` gives `0x80008000` (note the little-endian order): `"` and `\n` are flagged.
#[inline]
fn escape_bits(word: [u8; U32_LEN]) -> u32 {
    let word = u32::from_le_bytes(word);

    // The idea is as follows:
    // By looking at the `ESCAPE` table below, we can see that any byte < 0x20 needs to be escaped,
    // plus the two characters `"` (0x22) and `\` (0x5C).
    //
    // `bytes_less_than()` is used to perform several steps on the bytes (it performs the operations
    // on every byte of `word`, but we're going to walk the example on a single byte):
    //
    // - `b - 0x20`. This results in a negative value for every b < 0x20, so they get wrapped
    //   by adding 0xFF. This way, every `b < 0x20` that needs escaping are now in [0xE0, 0xFF] range.
    //   Their top bit is set to 1, which is what we aim for. However, most of the UTF-8 characters
    //   (the ones after 0xA0) still have their top bit set to 1 after the subtraction, so they are
    //   wrongly marked as needing an escape.
    //
    // - `& !b`: `!b` flips `b`'s bits, so the top bit is 1 if `b` was below 0x80 (1000 0000).
    //   Thus, any UTF-8 character will have the top bit to 0.
    //   When performing `(b - 0x20) & !b`, it keeps the top bit only for bytes that were below 0x80,
    //   so every UTF-8 character wrongly marked in previous step are discarded.
    //
    // - `& 0x80`: This acts as a mask: 0x80 is 1000 0000, so it only keeps the first bit, setting every
    //   other bit to 0.
    //
    // Note that because this is applied on the 4 bytes at once, the first subtraction operation can "leak"
    // to the next byte: a byte that wraps around borrows 1 from the next byte of the string (the more
    // significant one, as `word` is little-endian), which may then be wrongly marked as needing an escape.
    // In practice this is fine because only a byte that needs escaping can wrap around, so every byte up
    // to and including the first one to escape is correct, and callers only use that first marked byte
    // (the bytes after it are checked again once it has been escaped).

    // This leaves `"` and `\`, which are special cased with `bytes_equal_to()`.

    bytes_less_than(word, 0x20) | bytes_equal_to(word, b'"') | bytes_equal_to(word, b'\\')
}

#[inline]
fn bytes_less_than(word: u32, n: u8) -> u32 {
    debug_assert!(n <= 0x80);
    // See the explanation in `escape_bits()`:
    word.wrapping_sub(splat(n)) & !word & splat(0x80)
}

#[inline]
fn bytes_equal_to(word: u32, byte: u8) -> u32 {
    let word = word ^ splat(byte);
    word.wrapping_sub(splat(1)) & !word & splat(0x80)
}

/// A `u32` with each of its bytes set to `byte`.
#[inline]
const fn splat(byte: u8) -> u32 {
    u32::from_ne_bytes([byte; U32_LEN])
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
    // First two lines: control characters:
    UU, UU, UU, UU, UU, UU, UU, UU, BB, TT, NN, UU, FF, RR, UU, UU, // 0
    UU, UU, UU, UU, UU, UU, UU, UU, UU, UU, UU, UU, UU, UU, UU, UU, // 1
    // ASCII characters:
    __, __, QU, __, __, __, __, __, __, __, __, __, __, __, __, __, // 2
    __, __, __, __, __, __, __, __, __, __, __, __, __, __, __, __, // 3
    __, __, __, __, __, __, __, __, __, __, __, __, __, __, __, __, // 4
    __, __, __, __, __, __, __, __, __, __, __, __, BS, __, __, __, // 5
    __, __, __, __, __, __, __, __, __, __, __, __, __, __, __, __, // 6
    __, __, __, __, __, __, __, __, __, __, __, __, __, __, __, __, // 7
    // UTF-8 characters:
    __, __, __, __, __, __, __, __, __, __, __, __, __, __, __, __, // 8
    __, __, __, __, __, __, __, __, __, __, __, __, __, __, __, __, // 9
    __, __, __, __, __, __, __, __, __, __, __, __, __, __, __, __, // A
    __, __, __, __, __, __, __, __, __, __, __, __, __, __, __, __, // B
    __, __, __, __, __, __, __, __, __, __, __, __, __, __, __, __, // C
    __, __, __, __, __, __, __, __, __, __, __, __, __, __, __, __, // D
    __, __, __, __, __, __, __, __, __, __, __, __, __, __, __, __, // E
    __, __, __, __, __, __, __, __, __, __, __, __, __, __, __, __, // F
];

/// Represents a character escape code in a type-safe manner.
enum CharEscape {}

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
