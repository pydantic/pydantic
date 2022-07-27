#!/usr/bin/env bash
# check for devtools debug commands in a python file
set -e

echo "checking: $1"

if grep -Rn "^ *debug(" "$1"; then
    echo "ERROR: debug commands found in $1"
    exit 1
fi
