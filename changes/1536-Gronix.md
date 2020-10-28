Add a new post-validator that converts the validated 
dictionary which is returned by method `__validate_mapping` into a defaultdict
with correct `default_factory` attribute.