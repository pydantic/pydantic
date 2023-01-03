const {opendir} = require('node:fs/promises');
const {loadPyodide} = require('pyodide');
const path = require('path');

async function find_wheel(dist_dir) {
  const dir = await opendir(dist_dir);
  for await (const dirent of dir) {
    if (dirent.name.endsWith('.whl')) {
      return path.join(dist_dir, dirent.name);
    }
  }
}

function make_tty_ops(stream) {
  return {
    // get_char has 3 particular return values:
    // a.) the next character represented as an integer
    // b.) undefined to signal that no data is currently available
    // c.) null to signal an EOF
    get_char(tty) {
      if (!tty.input.length) {
        let result = null;
        const BUFSIZE = 256;
        const buf = Buffer.alloc(BUFSIZE);
        const bytesRead = fs.readSync(process.stdin.fd, buf, 0, BUFSIZE, -1);
        if (bytesRead === 0) {
          return null;
        }
        result = buf.slice(0, bytesRead);
        tty.input = Array.from(result);
      }
      return tty.input.shift();
    },
    put_char(tty, val) {
      try {
        if (val !== null) {
          tty.output.push(val);
        }
        if (val === null || val === 10) {
          process.stdout.write(Buffer.from(tty.output));
          tty.output = [];
        }
      } catch (e) {
        console.warn(e);
      }
    },
    fsync(tty) {
      if (!tty.output || tty.output.length === 0) {
        return;
      }
      stream.write(Buffer.from(tty.output));
      tty.output = [];
    },
  };
}

function setupStreams(FS, TTY) {
  let mytty = FS.makedev(FS.createDevice.major++, 0);
  let myttyerr = FS.makedev(FS.createDevice.major++, 0);
  TTY.register(mytty, make_tty_ops(process.stdout));
  TTY.register(myttyerr, make_tty_ops(process.stderr));
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

async function main() {
  const root_dir = path.resolve(__dirname, '..');
  const wheel_path = await find_wheel(path.join(root_dir, 'dist'));
  let errcode = 1;
  try {
    const pyodide = await loadPyodide();
    const FS = pyodide.FS;
    setupStreams(FS, pyodide._module.TTY);
    FS.mkdir('/test_dir');
    FS.mount(FS.filesystems.NODEFS, {root: path.join(root_dir, 'tests')}, '/test_dir');
    FS.chdir('/test_dir');
    await pyodide.loadPackage(['micropip', 'pytest', 'pytz']);
    // language=python
    errcode = await pyodide.runPythonAsync(`
import micropip
import importlib

# ugly hack to get tests to work on arm64 (my m1 mac)
# see https://github.com/pyodide/pyodide/issues/2840
# import sys; sys.setrecursionlimit(200)

await micropip.install([
    'dirty-equals',
    'hypothesis',
    'pytest-speed',
    'pytest-mock',
    'file:${wheel_path}',
])
importlib.invalidate_caches()

print('installed packages:', micropip.list())

import pytest
pytest.main()
`);
  } catch (e) {
    console.error(e);
    process.exit(1);
  }
  process.exit(errcode);
}

main();
