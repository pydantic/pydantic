Fix bug where generic models with fields where the typevar is nested in another type `a: List[T]` are considered to be concrete. This allows these models to be subclassed and composed as expected.
