Allow for shallow copies of attributes, adjusting the behavior of #3642
`Config.copy_on_model_validation` is now a str enum of `["", "deep", "shallow"]` corresponding to reference, deep copy, shallow copy.
