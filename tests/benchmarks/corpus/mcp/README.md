# MCP model corpus

Frozen from `mcp==2.3.0` and `mcp-types==2.3.0`. The corpus covers all 518
module-level Pydantic model declarations in both distributions, including client,
server, authentication, JSON-RPC, version-superset protocol models and both
version-specific wire-model packages. Their exported generic specializations
bring the complete runtime inventory to 553 models across 29 model modules.

Original package names and relative Python file paths are preserved under `mcp/`
and `mcp_types/`. Supporting definitions live at their original paths too; parent
packages without model dependencies have empty initializers. No MCP installation,
HTTP client, async framework, or web framework is needed.

Model fields, defaults, inheritance, configuration, validators, serializers,
computed fields, custom initialization and schema hooks are retained. Unrelated
SDK execution methods, documentation and imports are removed. Supporting types
retain the declarations and schema hooks needed to build these models; this is
not a runnable copy of the SDK. The RequestId alias is imported from its original
`mcp_types/jsonrpc.py` file rather than inlined.

`manifest.json` records upstream distribution versions, SHA-256 hashes for every
extracted source file, the full model inventory keyed by original module and
class name (recorded on Python 3.14), and each module's model declarations.
Tests compare declaration names and the runtime model count because generated
generic class display names vary between Python versions. The upstream MIT license is
reproduced in LICENSE. Update the snapshot and manifest together: a dependency
update is an explicit benchmark workload change.

Before measurement, sources are compiled and Pydantic is imported. Each measured
invocation imports the corpus through an in-memory importer under its original
module names and completes every discovered schema. Sources never fall back to
an installed MCP package. Existing MCP modules are restored afterward, including
on failure. Every run creates a fresh module tree and model graph, while
process-wide Pydantic caches may be warm. Source compilation, disk imports,
interpreter startup and subprocess overhead are excluded. This is a model-building
benchmark, not cold-interpreter or SDK startup.
