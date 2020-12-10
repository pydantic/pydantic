**Possible Breaking Change:** Inherited models as fields are not reconstructed (copied) anymore on validation
To keep old behaviour, set `copy_on_model_validation = True` in the `Config` of your `BaseModel`.
To change it globally for all your _pydantic_ models, you can set `BaseConfig.copy_on_model_validation = True`
