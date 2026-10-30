# MCP model corpus

Frozen from `mcp-types==2.3.0`, `mcp_types/_types.py`, the protocol version-superset
models. This is a model-building workload, not an SDK import benchmark.

The source retains model classes, inheritance, annotations, defaults, validators,
aliases, configuration, and the six protocol union TypeAdapters. Comments and
standalone docstrings are removed. The sole SDK import, `RequestId`, is inlined
verbatim from `mcp_types/jsonrpc.py`. No MCP installation is needed.

Upstream source SHA-256: `0d07007bf5052c5fe123d6f12addae8fdcd4eabfd2b3a2fd639c3a47675b7d98`.
The upstream MIT license is reproduced in LICENSE.

The benchmark compiles the frozen source before measurement, then executes it in
a fresh registered module namespace and completes every exposed model schema.
Pydantic is already imported. Interpreter startup, source parsing/compilation,
SDK imports, and subprocess overhead are excluded. New classes prevent reuse of
the preceding run's model schemas and generic specializations; process-wide
Pydantic caches can still be warm. This is not cold-interpreter startup.

Keep this snapshot stable when comparing Pydantic versions. Updates are explicit
workload changes and should record their upstream version and source hash.
