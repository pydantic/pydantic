# anthropic model corpus

Frozen from `anthropic==2.3.0`. Includes every production module-level
Pydantic model declaration found across the package, preserving original Python
package and file paths. `manifest.json` records the exact declaration inventory,
upstream versions and source hashes. SDK entry points and optional integrations
without model declarations are omitted; package initializers retain only required
exports. See LICENSE for upstream attribution.

Fields, inheritance, defaults, configuration, validators, serializers and schema
hooks are retained. Class docstrings are retained for schema descriptions and definition identity.
Attribute and function documentation, unrelated execution methods and transport
machinery are removed. Pydantic-v1 and TYPE_CHECKING-only branches are excluded;
runtime Python-version branches are retained. Deferral is explicitly disabled (`defer_build=False`) so schemas are built
as classes are defined; a final completion pass resolves forward references.
This overrides SDK defaults and environment switches, avoids deep deferred
rebuild chains, and keeps every measured run eager. This is a frozen workload, not a runnable SDK.

The shared importer compiles sources before measurement, imports a fresh isolated
package graph and builds all model schemas under CPU simulation. Source parsing,
disk imports and SDK startup are excluded. Process-wide caches can be warm.
Never import these files directly: the importer restores any installed packages
and prevents fallback to unvendored SDK modules.

The original HTTPX2 Timeout dataclass and its minimal supporting declarations are
included at their upstream paths so model field types need no HTTP client stack.
See HTTPX2-LICENSE for its BSD license and the manifest for source hashes.
