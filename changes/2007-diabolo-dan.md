Add parameterised subclasses to `__bases__` when constructing new parameterised classes, so that `A <: B => A[int] <: B[int]`.
