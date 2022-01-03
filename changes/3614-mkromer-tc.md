# Fix 3614

Insert `_guard_list_of_dicts()` as a guard point against trying
to instantiate a dict() of a list of dictionaries, which will inevitably give
incorrect results.

Python will convert `dict([{'key_a': 'value_a', 'key_b': 'value_b'}])` to `{'key_a': 'key_b'}`
but because the conversion succeeds (albeit with incorrect results) it is impossible to allow
model fields of the type `Union[Thing, List[Thing]]` whereas `Union[List[Thing], Thing]` works as
expected.  Raising an exception when trying to perform a `dict()` operation on a list of
dictionaries allows both forms to work.