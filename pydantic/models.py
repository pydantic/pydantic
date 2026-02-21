class ElegantClass(BaseModel):
    regular_ol_val: int
    could_be_nested: int = Field(..., validation_alias=AliasPath('nested', 'could_be_nested'))

@model_validator(mode='before')
@classmethod
def nested_vals_as_dict(cls, data: Any) -> Any:
    if isinstance(data, dict):
        nested_fields = ['nested_elegant_val']
        for field in nested_fields:
            if field in data and isinstance(data[field], BaseModel):
                data_field: BaseModel = data[field]
                data[field] = data_field.model_dump()
    return data