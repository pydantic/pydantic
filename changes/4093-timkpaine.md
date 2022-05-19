Allow for shallow copies of attributes, adjusting the behavior of #3642
`Config.copy_on_model_validation` does a shallow copy and not a deep one if `Config.copy_on_model_validation_shallow` is also `True`.
