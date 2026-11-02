"""The type handlers API, used to generate core schemas for types (and the metadata attached to them).

The main components are:

- Type handlers (see `BaseTypeHandler`): responsible for generating the core schema of a type, applying
  the metadata it knows about (e.g. `Gt` for `int`).
- The annotations handler (see `AnnotationsHandler`): provides the metadata known by a type handler.
- The type registry (see `TypeRegistry`): holds the type handlers, and is used to find the type handler for a type.
"""
