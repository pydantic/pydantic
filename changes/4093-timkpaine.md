Allow for shallow copies of attributes, adjusting the behavior of #3642
`Config.copy_on_model_validation` is now a str enum of `["none", "deep", "shallow"]` corresponding to 
not copying, deep copy, shallow copy, default `"shallow"`.
