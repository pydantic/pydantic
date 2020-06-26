Added support for UUID instantiation through 16 byte strings such as `b'\x12\x34\x56\x78' * 4`. This was done to support `BINARY(16)` columns in sqlalchemy.
