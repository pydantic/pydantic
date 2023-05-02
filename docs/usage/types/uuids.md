`uuid.UUID`
: strings and bytes (converted to strings) are passed to `UUID(v)`, with a fallback to `UUID(bytes=v)` for `bytes` and `bytearray`

`UUID1`
: requires a valid UUID of type 1; see `UUID` above

`UUID3`
: requires a valid UUID of type 3; see `UUID` above

`UUID4`
: requires a valid UUID of type 4; see `UUID` above

`UUID5`
: requires a valid UUID of type 5; see `UUID` above
