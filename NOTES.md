# Problems with Pypy

## AnyThing seems to be a _numbers.Rational ?

```txt
self = Decimal('NaN'), other = AnyThing(), equality_op = True

def _convert_for_comparison(self, other, equality_op=False):
    ...
    if isinstance(other, _numbers.Rational): # <- This returns True
        ...
```
