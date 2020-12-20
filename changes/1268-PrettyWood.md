**Possible Breaking Change:** Make dict validator strict so empty strings or lists won't be valid anymore by default
To keep old behaviour, set `loose_dict_validator = True` in the `Config` of your `BaseModel`.
To change it globally for all your _pydantic_ models, you can set `BaseConfig.loose_dict_validator = True`.