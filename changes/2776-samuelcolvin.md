**Security fix:** Fix `date` and `datetime` parsing so passing either `'infinity'` or `float('inf')` 
(or their negative values) does not cause an infinite loop.
