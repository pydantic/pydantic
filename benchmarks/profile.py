import json
from test_pydantic import TestPydantic

with open('./benchmarks/cases.json') as f:
    cases = json.load(f)

count, pass_count = 0, 0
test = TestPydantic(False)
for case in cases:
    passed, result = test.validate(case)
    count += 1
    pass_count += passed
