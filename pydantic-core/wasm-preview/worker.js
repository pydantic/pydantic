// Must match the Python version and platform tag of the pydantic-core wheels published to PyPI
// (see the `core-build-pyemscripten` job in `.github/workflows/ci.yml`):
const PYODIDE_VERSION = '314.0.7';
const WHEEL_TAG = 'cp314-cp314-pyemscripten_2026_0_wasm32';
// First pydantic release with pydantic-core Pyodide wheels published to PyPI:
const MIN_PYDANTIC_VERSION = [2, 14, 0];

let chunks = [];
let last_post = 0;

function post() {
  self.postMessage(chunks);
  chunks = [];
}

function write(buffer) {
  // the buffer may be reused by Pyodide, so copy it:
  chunks.push(buffer.slice());
  const now = performance.now();
  if (now - last_post > 100) {
    post();
    last_post = now;
  }
  return buffer.length;
}

async function get(url, mode) {
  const r = await fetch(url);
  if (r.ok) {
    if (mode === 'text') {
      return await r.text();
    } else if (mode === 'json') {
      return await r.json();
    } else {
      return new Uint8Array(await r.arrayBuffer());
    }
  } else {
    let text = await r.text();
    console.error('unexpected response', r, text);
    throw new Error(`${url}: ${r.status}: ${text}`);
  }
}

function checkPydanticVersion(version) {
  const match = version.match(/^(\d+)\.(\d+)\.(\d+)((?:a|b|rc)\d+)?$/);
  if (!match) {
    throw new Error(`Invalid pydantic version: ${version}`);
  }
  const parts = match.slice(1, 4).map(Number);
  const i = parts.findIndex((p, i) => p !== MIN_PYDANTIC_VERSION[i]);
  // pre-releases of the minimum version (e.g. 2.14.0b1) are also not supported:
  const supported = i === -1 ? !match[4] : parts[i] > MIN_PYDANTIC_VERSION[i];
  if (!supported) {
    throw new Error(
      `pydantic ${version} is not supported, the minimum supported version is ${MIN_PYDANTIC_VERSION.join('.')}`,
    );
  }
}

async function getPydanticVersion(query_args) {
  let pydantic_version = query_args.get('pydantic_version');
  if (pydantic_version) {
    return pydantic_version.replace(/^v/, '');
  }
  const latest_release = await get('https://pypi.org/pypi/pydantic/json', 'json');
  return latest_release.info.version;
}

async function getPydanticCoreWheelUrl(pydantic_version) {
  const pydantic_release = await get(`https://pypi.org/pypi/pydantic/${pydantic_version}/json`, 'json');
  const requirement = pydantic_release.info.requires_dist.find((r) => /^pydantic[-_]core\s*==/.test(r));
  if (!requirement) {
    throw new Error(`Could not find the pydantic-core requirement of pydantic ${pydantic_version}`);
  }
  const pydantic_core_version = requirement.split('==')[1].trim();
  const pydantic_core_release = await get(`https://pypi.org/pypi/pydantic-core/${pydantic_core_version}/json`, 'json');
  const wheel = pydantic_core_release.urls.find((f) => f.filename.endsWith(`-${WHEEL_TAG}.whl`));
  if (!wheel) {
    throw new Error(`No ${WHEEL_TAG} wheel found for pydantic-core ${pydantic_core_version}`);
  }
  return [pydantic_core_version, wheel.url];
}

async function main() {
  try {
    const query_args = new URLSearchParams(location.search);
    const pydantic_version = await getPydanticVersion(query_args);
    checkPydanticVersion(pydantic_version);
    const [pydantic_core_version, pydantic_core_wheel_url] = await getPydanticCoreWheelUrl(pydantic_version);
    self.postMessage(`Running tests against pydantic ${pydantic_version} (pydantic-core ${pydantic_core_version}).\n`);
    self.postMessage(`Downloading repo archive to get tests...\n`);
    const zip_url = `https://githubproxy.samuelcolvin.workers.dev/pydantic/pydantic/archive/refs/tags/v${pydantic_version}.zip`;
    const [python_code, repo_zip, {loadPyodide}] = await Promise.all([
      get(`./run_tests.py?v=${Date.now()}`, 'text'),
      get(zip_url, 'blob'),
      import(`https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/pyodide.mjs`),
    ]);

    const pyodide = await loadPyodide();
    pyodide.setStdout({write, isatty: true});
    pyodide.setStderr({write, isatty: true});
    pyodide.FS.writeFile('/repo.zip', repo_zip);
    pyodide.FS.mkdir('/test_dir');
    pyodide.FS.chdir('/test_dir');
    await pyodide.loadPackage(['micropip']);
    await pyodide.runPythonAsync(python_code, {
      globals: pyodide.toPy({repo_zip_path: '/repo.zip', pydantic_core_wheel_url}),
    });
    post();
  } catch (err) {
    console.error(err);
    post();
    self.postMessage(`${err}\n`);
  }
}

main();
