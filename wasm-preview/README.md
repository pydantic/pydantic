# Demonstration of pydantic-core unit tests running in the browser

To run tests in your browser, go [here](https://githubproxy.samuelcolvin.workers.dev/pydantic/pydantic-core/blob/main/wasm-preview/index.html).

To test with a specific version of pydantic-core, add a query parameter `?pydantic_core_version=...` to the URL, e.g. `?pydantic_core_version=v0.25.0`, defaults to latest release.

This doesn't work for version of pydantic-core before v0.23.0 as before that we built 3.10 binaries, and pyodide now rust 3.11.

If the output appears to stop prematurely, try looking in the developer console for more details.

Tests are currently failing 10-15% of the wait through on Chrome due to a suspected V8 bug, see [pyodide/pyodide#3792](https://github.com/pyodide/pyodide/issues/3792) for more information.
