# Demonstration of pydantic unit tests running in the browser

[Run tests in your browser at this web link](https://githubproxy.samuelcolvin.workers.dev/pydantic/pydantic/blob/main/pydantic-core/wasm-preview/index.html).

The full pydantic test suite is run using [Pyodide](https://pyodide.org/), against the Pyodide wheel published to PyPI.
Test dependencies are installed from the same lockfile as in CI (`.github/pyodide/pylock.<python version>.toml`).

To test with a specific version of pydantic, add a query parameter `?pydantic_version=...` to the URL, e.g. `?pydantic_version=2.14.0`,
defaults to the latest release.

If the output appears to stop prematurely, try looking in the developer console for more details.
