"""The vendored benchmark documents in `data/`, and how to check or rebuild them.

Three documents come from nativejson-benchmark rather than being generated, because they are
real and because other JSON projects benchmark on the same bytes. They are committed
compressed, which makes them opaque, so everything needed to prove what is in them lives here:
the upstream URL, the SHA-256 of the document, and the SHA-256 of the compressed file.

Check the committed files against those hashes, without network access:

    python -m tests.benchmarks.vendored_documents --check

Rebuild them from upstream and confirm the result is byte-for-byte what is committed:

    python -m tests.benchmarks.vendored_documents

Add `--write` to that to actually replace the files. Compression is `lzma` at preset 9 with a
CRC-64 check, which is reproducible: the same input gives the same bytes on Linux x86_64 and
macOS arm64, and matches `xz -9`.
"""

from __future__ import annotations

import argparse
import hashlib
import lzma
import sys
from dataclasses import dataclass
from pathlib import Path

DATA_DIR = Path(__file__).parent / 'data'

_UPSTREAM = 'https://raw.githubusercontent.com/miloyip/nativejson-benchmark/master/data'

# Compression parameters are pinned here rather than taken from a CLI's defaults, so that the
# committed bytes do not depend on which version of xz happens to be installed.
_FILTERS = [{'id': lzma.FILTER_LZMA2, 'preset': 9}]


@dataclass(frozen=True)
class Document:
    """What a vendored document must hash to, decompressed and as committed."""

    raw_size: int
    raw_sha256: str
    xz_sha256: str


DOCUMENTS: dict[str, Document] = {
    'twitter': Document(
        raw_size=631514,
        raw_sha256='a08b769f32b95f426cbc3abafcec65c1a19d3eb544d4ddf320eae142c99efc5d',
        xz_sha256='73e96118c9db8cf5af4f160e21767803842247bf2400282d0ec74f63ac561c3d',
    ),
    'canada': Document(
        raw_size=2251051,
        raw_sha256='f83b3b354030d5dd58740c68ac4fecef64cb730a0d12a90362a7f23077f50d78',
        xz_sha256='a963c043202955759c32399ba31d917e07e05a89bb897a5513f4c07e85c7b9b9',
    ),
    'citm_catalog': Document(
        raw_size=1727204,
        raw_sha256='a73e7a883f6ea8de113dff59702975e60119b4b58d451d518a929f31c92e2059',
        xz_sha256='ce8710fd2de08235d947a909946e79140c39450c72e8fcde93f488011929efd5',
    ),
}


def path_for(name: str) -> Path:
    return DATA_DIR / f'{name}.json.xz'


def url_for(name: str) -> str:
    return f'{_UPSTREAM}/{name}.json'


def load_vendored(name: str) -> bytes:
    """The decompressed document. Used by the benchmarks."""
    return lzma.decompress(path_for(name).read_bytes())


def compress(raw: bytes) -> bytes:
    return lzma.compress(raw, format=lzma.FORMAT_XZ, check=lzma.CHECK_CRC64, filters=_FILTERS)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def check_vendored_documents() -> list[str]:
    """Verify the committed files against the manifest. Returns a list of problems."""
    problems = []
    for name, doc in DOCUMENTS.items():
        path = path_for(name)
        if not path.exists():
            problems.append(f'{name}: {path} is missing')
            continue
        compressed = path.read_bytes()
        if _sha256(compressed) != doc.xz_sha256:
            problems.append(f'{name}: compressed file does not match the recorded SHA-256')
        raw = lzma.decompress(compressed)
        if len(raw) != doc.raw_size:
            problems.append(f'{name}: decompresses to {len(raw)} bytes, expected {doc.raw_size}')
        if _sha256(raw) != doc.raw_sha256:
            problems.append(f'{name}: decompressed document does not match the recorded SHA-256')
    return problems


def _rebuild(write: bool) -> int:
    import urllib.request

    failures = 0
    for name, doc in DOCUMENTS.items():
        with urllib.request.urlopen(url_for(name)) as response:
            raw = response.read()
        if _sha256(raw) != doc.raw_sha256:
            print(f'{name}: upstream no longer matches the recorded SHA-256, refusing to use it')
            failures += 1
            continue
        compressed = compress(raw)
        path = path_for(name)
        committed = path.read_bytes() if path.exists() else None
        identical = committed == compressed
        if write:
            path.write_bytes(compressed)
        state = 'identical to the committed file' if identical else 'DIFFERS from the committed file'
        print(f'{name:14} {len(raw):>9,} B -> {len(compressed):>7,} B  {state}')
        if not identical and not write:
            failures += 1
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        '--check',
        action='store_true',
        help='verify the committed files against the manifest, without network access',
    )
    parser.add_argument('--write', action='store_true', help='replace the committed files with the rebuilt ones')
    args = parser.parse_args(argv)

    if args.check:
        problems = check_vendored_documents()
        for problem in problems:
            print(problem)
        if not problems:
            print(f'{len(DOCUMENTS)} vendored documents match the manifest')
        return 1 if problems else 0

    return _rebuild(write=args.write)


if __name__ == '__main__':
    sys.exit(main())
