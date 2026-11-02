# Frozen model corpora

These corpora measure construction of real model graphs under the existing
CodSpeed CPU-simulation job, without importing the installed SDKs or starting
child interpreters.

| Corpus | Pinned distribution | Model declarations | Python |
| --- | --- | ---: | --- |
| MCP | mcp and mcp-types 2.3.0 | 518 | 3.10+ |
| OpenAI | openai 3.41.0 | 2,621 | 3.10+ |
| Anthropic | anthropic 2.3.0 | 1,186 | 3.10+ |
| Google Gen AI | google-genai 2.34.0 | 749 | 3.11+ |

Each snapshot includes all production module-level Pydantic model declarations
across its SDK, preserving their original package and file paths. Models outside
SDK types packages, such as pagination and streaming models, are included.
Generic specializations created by those declarations are also constructed and
completed, so runtime model counts can exceed declaration counts.

The sources retain fields, inheritance, defaults, configuration, validators and
schema hooks. SDK class docstrings are kept where removing them changes JSON
schema definition identity. Unrelated execution methods and dependencies are
removed. Each corpus contains its upstream license, an exact declaration inventory
and source hashes. The SDK manifests also record the upstream schema comparison:
descriptions and enum ordering are ignored, and unsupported JSON-schema outcomes
are compared by error type.

HTTPX Timeout support is vendored for OpenAI and Anthropic. Google freezes optional
integration availability and uses opaque HTTP client field-type markers, preserving
the arbitrary-type schema shape without transport implementations. These are
benchmark fixtures, not runnable SDKs. See individual corpus READMEs for details.

`model_corpus.py` compiles the source outside measurement. Each measured invocation
imports a fresh package graph in memory, eagerly builds schemas during class
definition, completes remaining forward references, and restores any
pre-existing packages and import hooks even on failure. Missing modules cannot
fall back to an installed SDK. Tests verify exact declaration coverage, eager
completion, fresh class identities, representative payloads, import isolation and
minimum-version syntax. SDK deferral is explicitly disabled, including SDK
environment switches, to avoid deep deferred rebuild chains. All tests that manipulate global import state run serially.
Process-wide Pydantic and Python caches can still be warm: this measures model
building, not cold SDK or interpreter startup.

Run the checks without installing any SDK dependencies:

```bash
uv run --no-sync pytest tests/benchmarks/test_model_corpus.py tests/benchmarks/test_mcp_model_corpus.py
```

For CodSpeed, add `--codspeed`. All four workloads use the same parametrized
benchmark, `test_model_corpus[<corpus>]`. The CodSpeed workflow runs each corpus in
its own matrix job alongside the existing benchmark suite, with identical build
and profiling settings. To select one corpus, add `-k "[openai]"`, for example.
Snapshot updates are explicit workload changes and should update
provenance, declaration inventories and coverage checks together.

On PyPy, the importer temporarily raises a smaller recursion limit to 2,000,
then restores it on success or failure. PyPy maps this limit to usable native
stack space; the default budget can overflow in cpyext while building the deep
SDK graphs. CPython's limit is untouched. See [PyPy's documented stack-limit
behavior](https://doc.pypy.org/cpython_differences.html).
