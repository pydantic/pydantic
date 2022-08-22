Allow type checkers to infer inner type of `Json` type. `Json[list[str]]` will be now inferred as `list[str]`. 
`Json[Any]` should be used instead of plain `Json`.
Runtime behaviour is not changed.
