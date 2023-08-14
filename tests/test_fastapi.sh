#! /usr/bin/env bash

set -x
set -e

cd fastapi
git fetch --tags

pip install -r requirements.txt
# Install the version of pydantic from the current branch, not the released version used by fastapi
pip uninstall -y pydantic
cd .. && pip install . && cd fastapi

# ./scripts/test.sh accepts arbitrary arguments and passes them to the pytest call.
# This may be necessary if we make low-consequence changes to pydantic, such as minor changes the details of a JSON
# schema or the contents of a ValidationError
#
# To skip a specific test, add '--deselect path/to/test.py::test_name' to the end of this command
#
# To update the list of deselected tests, remove all deselections, run the tests, and re-add any remaining failures
./scripts/test.sh \
  --deselect tests/test_tutorial/test_body_updates/test_tutorial001.py \
  --deselect tests/test_tutorial/test_body_updates/test_tutorial001_py310.py \
  --deselect tests/test_tutorial/test_body_updates/test_tutorial001_py39.py \
  --deselect tests/test_tutorial/test_dataclasses/test_tutorial003.py \
  --deselect tests/test_tutorial/test_path_operation_advanced_configurations/test_tutorial004.py \
  --deselect tests/test_tutorial/test_path_operation_configurations/test_tutorial005.py \
  --deselect tests/test_tutorial/test_path_operation_configurations/test_tutorial005_py310.py \
  --deselect tests/test_tutorial/test_path_operation_configurations/test_tutorial005_py39.py \
  --deselect tests/test_multi_body_errors.py::test_jsonable_encoder_requiring_error \
  --deselect tests/test_multi_body_errors.py::test_put_incorrect_body_multiple \
