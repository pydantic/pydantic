let chunks = [];
let last_post = 0;

function print(tty) {
  if (tty.output && tty.output.length > 0) {
    chunks.push(tty.output);
    tty.output = [];
    const now = performance.now();
    if (now - last_post > 100) {
      post();
      last_post = now;
    }
  }
}

function post() {
  self.postMessage(chunks);
  chunks = [];
}

function make_tty_ops() {
  return {
    put_char(tty, val) {
      if (val !== null) {
        tty.output.push(val);
      }
      if (val === null || val === 10) {
        print(tty);
      }
    },
    fsync(tty) {
      print(tty);
    },
  };
}

function setupStreams(FS, TTY) {
  let mytty = FS.makedev(FS.createDevice.major++, 0);
  let myttyerr = FS.makedev(FS.createDevice.major++, 0);
  TTY.register(mytty, make_tty_ops());
  TTY.register(myttyerr, make_tty_ops());
  FS.mkdev('/dev/mytty', mytty);
  FS.mkdev('/dev/myttyerr', myttyerr);
  FS.unlink('/dev/stdin');
  FS.unlink('/dev/stdout');
  FS.unlink('/dev/stderr');
  FS.symlink('/dev/mytty', '/dev/stdin');
  FS.symlink('/dev/mytty', '/dev/stdout');
  FS.symlink('/dev/myttyerr', '/dev/stderr');
  FS.closeStream(0);
  FS.closeStream(1);
  FS.closeStream(2);
  FS.open('/dev/stdin', 0);
  FS.open('/dev/stdout', 1);
  FS.open('/dev/stderr', 1);
}

async function get(url, mode) {
  const r = await fetch(url);
  if (r.ok) {
    if (mode === 'text') {
      return await r.text();
    } else if (mode === 'json') {
      return await r.json();
    } else {
      const blob = await r.blob();
      let buffer = await blob.arrayBuffer();
      return btoa(new Uint8Array(buffer).reduce((data, byte) => data + String.fromCharCode(byte), ''));
    }
  } else {
    let text = await r.text();
    console.error('unexpected response', r, text);
    throw new Error(`${r.status}: ${text}`);
  }
}

async function main() {
  const query_args = new URLSearchParams(location.search);
  let pydantic_core_version = query_args.get('pydantic_core_version');
  if (!pydantic_core_version) {
    const latest_release = await get('https://api.github.com/repos/pydantic/pydantic-core/releases/latest', 'json');
    pydantic_core_version = latest_release.tag_name;
  }
  self.postMessage(`Running tests against latest pydantic-core release (${pydantic_core_version}).\n`);
  self.postMessage(`Downloading repo archive to get tests...\n`);
  const zip_url = `https://githubproxy.samuelcolvin.workers.dev/pydantic/pydantic-core/archive/refs/tags/${pydantic_core_version}.zip`;
  try {
    const [python_code, tests_zip] = await Promise.all([
      get(`./run_tests.py?v=${Date.now()}`, 'text'),
      // e4cf2e2 commit matches the pydantic-core wheel being used, so tests should pass
      get(zip_url, 'blob'),
      importScripts('https://cdn.jsdelivr.net/pyodide/v0.23.0/full/pyodide.js'),
    ]);

    const pyodide = await loadPyodide();
    const {FS} = pyodide;
    setupStreams(FS, pyodide._module.TTY);
    FS.mkdir('/test_dir');
    FS.chdir('/test_dir');
    await pyodide.loadPackage(['micropip', 'pytest', 'pytz']);
    if (pydantic_core_version < '2.0.0') await pyodide.loadPackage(['typing-extensions']);
    await pyodide.runPythonAsync(python_code, {globals: pyodide.toPy({pydantic_core_version, tests_zip})});
    post();
  } catch (err) {
    console.error(err);
    self.postMessage(`Error: ${err}\n`);
  }
}

main();
