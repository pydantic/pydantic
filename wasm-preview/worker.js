let chunks = []
let last_post = 0

function print(tty) {
  if (tty.output && tty.output.length > 0) {
    chunks.push(tty.output)
    tty.output = []
    const now = performance.now()
    if (now - last_post > 100) {
      post()
      last_post = now
    }
  }
}

function post() {
  self.postMessage(chunks)
  chunks = []
}

function make_tty_ops() {
  return {
    put_char(tty, val) {
      if (val !== null) {
        tty.output.push(val)
      }
      if (val === null || val === 10) {
        print(tty)
      }
    },
    flush(tty) {
      print(tty)
    },
  }
}

function setupStreams(FS, TTY) {
  let mytty = FS.makedev(FS.createDevice.major++, 0)
  let myttyerr = FS.makedev(FS.createDevice.major++, 0)
  TTY.register(mytty, make_tty_ops())
  TTY.register(myttyerr, make_tty_ops())
  FS.mkdev('/dev/mytty', mytty)
  FS.mkdev('/dev/myttyerr', myttyerr)
  FS.unlink('/dev/stdin')
  FS.unlink('/dev/stdout')
  FS.unlink('/dev/stderr')
  FS.symlink('/dev/mytty', '/dev/stdin')
  FS.symlink('/dev/mytty', '/dev/stdout')
  FS.symlink('/dev/myttyerr', '/dev/stderr')
  FS.closeStream(0)
  FS.closeStream(1)
  FS.closeStream(2)
  FS.open('/dev/stdin', 0)
  FS.open('/dev/stdout', 1)
  FS.open('/dev/stderr', 1)
}

async function get(url, mode) {
  const r = await fetch(url)
  if (r.ok) {
    if (mode === 'text') {
      return await r.text()
    } else {
      const blob = await r.blob();
      let buffer = await blob.arrayBuffer();
      return btoa(new Uint8Array(buffer).reduce((data, byte) => data + String.fromCharCode(byte), ''))
    }
  } else {
    let text = await r.text()
    console.error('unexpected response', r, text)
    throw new Error(`${r.status}: ${text}`)
  }
}

self.onmessage = async () => {
  self.postMessage('Downloading repo archive to get tests...\n')
  try {
    const [python_code, tests_zip,] = await Promise.all([
      get(`./run_tests.py?v=${Date.now()}`, 'text'),
      // e4cf2e2 commit matches the pydantic-core wheel being used, so tests should pass
      get('https://githubproxy.samuelcolvin.workers.dev/samuelcolvin/pydantic-core/archive/e4cf2e2.zip', 'blob'),
      importScripts('https://cdn.jsdelivr.net/pyodide/v0.21.0a3/full/pyodide.js')
    ])

    const pyodide = await loadPyodide()
    const {FS} = pyodide
    setupStreams(FS, pyodide._module.TTY)
    FS.mkdir('/test_dir')
    FS.chdir('/test_dir')
    await pyodide.loadPackage(['micropip', 'pytest', 'pytz'])
    await pyodide.runPythonAsync(python_code, {globals: pyodide.toPy({tests_zip})})
    post()
  } catch (err) {
    console.error(err)
    self.postMessage(`Error: ${err}\n`)
  }
}
