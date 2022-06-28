const { opendir } = require('node:fs/promises');
const { loadPyodide } = require('pyodide');

async function findWheel(distDir) {
  const dir = await opendir(distDir);
  for await (const dirent of dir) {
    if (dirent.name.endsWith('whl')) {
      return dirent.name;
    }
  }
}

const pkgDir = process.argv[2];
const distDir = pkgDir + '/dist';
const testDir = pkgDir + '/tests';

function make_tty_ops(stream){
  return {
    // get_char has 3 particular return values:
    // a.) the next character represented as an integer
    // b.) undefined to signal that no data is currently available
    // c.) null to signal an EOF
    get_char(tty) {
      if (!tty.input.length) {
        var result = null;
        var BUFSIZE = 256;
        var buf = Buffer.alloc(BUFSIZE);
        var bytesRead = fs.readSync(process.stdin.fd, buf, 0, BUFSIZE, -1);
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
        if(val !== null){
          tty.output.push(val);
        }
        if (val === null || val === 10) {
          process.stdout.write(Buffer.from(tty.output));
          tty.output = [];
        }
      } catch(e){
        console.warn(e);
      }
    },
    flush(tty) {
      if (!tty.output || tty.output.length === 0) {
        return;
      }
      stream.write(Buffer.from(tty.output));
      tty.output = [];
    }
  };
}

function setupStreams(FS, TTY){
  let mytty = FS.makedev(FS.createDevice.major++, 0);
  let myttyerr = FS.makedev(FS.createDevice.major++, 0);
  TTY.register(mytty, make_tty_ops(process.stdout))
  TTY.register(myttyerr, make_tty_ops(process.stderr))
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
  var stdin = FS.open('/dev/stdin', 0);
  var stdout = FS.open('/dev/stdout', 1);
  var stderr = FS.open('/dev/stderr', 1);
}


async function main() {
  const wheelName = await findWheel(distDir);
  const wheelURL = `file:${distDir}/${wheelName}`;

  try {
    pyodide = await loadPyodide();
    const FS = pyodide.FS;
    setupStreams(FS, pyodide._module.TTY);
    const NODEFS = FS.filesystems.NODEFS;
    FS.mkdir('/test_dir');
    FS.mount(NODEFS, { root: testDir }, '/test_dir');
    await pyodide.loadPackage(['micropip', 'pytest', 'pytz']);
    const micropip = pyodide.pyimport('micropip');
    await micropip.install('dirty-equals');
    await micropip.install(wheelURL);
    const pytest = pyodide.pyimport('pytest');
    FS.chdir("/test_dir");
    errcode = pytest.main();
  } catch (e) {
    console.error(e);
    process.exit(1);
  }
}

main();
