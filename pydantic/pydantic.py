from pydantic import BaseModel, AliasPath, Field

class ElegantClass(BaseModel):
    regular_ol_val: int
    could_be_nested: int = Field(..., validation_alias=AliasPath('nested', 'could_be_nested'))

class ElegantNestedClass(BaseModel):
    nested_elegant_val: int

# Example usage
result = ElegantClass.model_validate({
    'regular_ol_val': 1,
    'nested': ElegantNestedClass(could_be_nested=2)
})
print(result)