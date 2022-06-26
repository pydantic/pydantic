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

async function main() {
  const wheelName = await findWheel(distDir);
  const wheelURL = `file:${distDir}/${wheelName}`;

  try {
    pyodide = await loadPyodide();
    const FS = pyodide.FS;
    const NODEFS = FS.filesystems.NODEFS;
    FS.mkdir('/test_dir');
    FS.mount(NODEFS, { root: testDir }, '/test_dir');
    await pyodide.loadPackage(['micropip', 'pytest', 'pytz']);
    const micropip = pyodide.pyimport('micropip');
    await micropip.install('dirty-equals');
    await micropip.install(wheelURL);
    const pytest = pyodide.pyimport('pytest');
    errcode = pytest.main(pyodide.toPy(['/test_dir', '-vv']));
  } catch (e) {
    console.error(e);
    process.exit(1);
  }
}

main();
