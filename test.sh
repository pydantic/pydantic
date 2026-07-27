#!/usr/bin/env bash
set -uo pipefail
cd /app

OUTPUT_PATH=""
if [ "${1:-}" = "--output_path" ]; then
  OUTPUT_PATH="$2"
  shift 2
fi

MODE="${1:-new}"

case "$MODE" in
  base)
    ARGS="tests/test_types.py -k flag or Flag"
    ;;
  new)
    ARGS="tests/test_flag_enum_roundtrip.py"
    ;;
  *)
    echo "unknown mode: $MODE" >&2
    exit 2
    ;;
esac

if [ -n "$OUTPUT_PATH" ]; then
  python -m pytest $ARGS --junitxml="$OUTPUT_PATH" -v
else
  python -m pytest $ARGS -v
fi