#! /usr/bin/env bash

set -x
set -e

cd fastapi
git fetch --tags

pip install -r requirements.txt

# ./scripts/test.sh accepts arbitrary arguments and passes them to the pytest call.
# This may be necessary if we make low-consequence changes to pydantic, such as minor changes the details of a JSON
# schema or the contents of a ValidationError
#
# To skip a specific test, add '--deselect path/to/test.py::test_name' to the end of this command
#
# To update the list of deselected tests, remove all deselections, run the tests, and re-add any remaining failures
./scripts/test.sh \
  --deselect tests/test_filter_pydantic_sub_model_pv2.py::test_validator_is_cloned \
  --deselect tests/test_multi_body_errors.py::test_jsonable_encoder_requiring_error \
  --deselect tests/test_multi_body_errors.py::test_put_incorrect_body_multiple \

# TODO: Update the deselections after https://github.com/tiangolo/fastapi/pull/9943 is merged
