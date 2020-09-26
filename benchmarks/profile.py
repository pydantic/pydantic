import json

from line_profiler import LineProfiler

import pydantic.datetime_parse
import pydantic.validators
from pydantic import validate_model
from pydantic.fields import ModelField
from test_pydantic import TestPydantic

with open('./benchmarks/cases.json') as f:
    cases = json.load(f)


def run():
    count, pass_count = 0, 0
    test = TestPydantic(False)
    for case in cases:
        passed, result = test.validate(case)
        count += 1
        pass_count += passed
    print('success percentage:', pass_count / count * 100)


funcs_to_profile = [validate_model, ModelField.validate, ModelField._validate_singleton, ModelField._apply_validators]
module_objects = {**vars(pydantic.validators), **vars(pydantic.datetime_parse), **vars(ModelField)}
funcs_to_profile += [v for k, v in module_objects.items() if not k.startswith('_') and str(v).startswith('<cyfunction')]


def main():
    profiler = LineProfiler()
    for f in funcs_to_profile:
        profiler.add_function(f)
    profiler.wrap_function(run)()
    profiler.print_stats(stripzeros=True)


if __name__ == '__main__':
    main()
