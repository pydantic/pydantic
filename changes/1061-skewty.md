Trick Cython into allowing str subclassing.

Without this "trick" passing in values that subclassed `ConstrainedStr` always raised a `Field` `ValidationError`.  
This `ValidationError` issue only seems to manifest in the **Cython** compiled variant (not in **CPython**).