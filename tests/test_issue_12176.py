# File location: tests/test_issue_12174.py
from pydantic.json_schema import GenerateJsonSchema

def test_custom_json_schema_suffix_logic():
    # 1. Create a generator with custom settings
    gen = GenerateJsonSchema(
        validation_name_strategy='Request',  # Custom suffix 1
        serialization_name_strategy='Response'  # Custom suffix 2
    )

    # 2. Create a dummy model reference
    # Format: "module_name:ClassName:ID"
    dummy_ref = "my_module:MyModel:12345"

    # 3. Call get_defs_ref method (Validation mode)
    gen.get_defs_ref((dummy_ref, 'validation'))

    # 4. Inspect internal name choices
    all_choices = []
    for choices in gen._prioritized_defsref_choices.values():
        all_choices.extend(choices)

    print("Generated choices (Validation):", all_choices)

    # 5. Verify (Assert)
    # Check if the full name prefixed with 'my_module_' is correctly generated
    assert 'my_module_MyModel-Request' in all_choices, "Validation suffix 'Request' was not generated"

    # 6. Check Serialization mode as well
    gen.get_defs_ref((dummy_ref, 'serialization'))

    # Check choices again
    all_choices_ser = []
    for choices in gen._prioritized_defsref_choices.values():
        all_choices_ser.extend(choices)

    print("Generated choices (Serialization):", all_choices_ser)

    # Verify the full name here as well
    assert 'my_module_MyModel-Response' in all_choices_ser, "Serialization suffix 'Response' was not generated"

# 2. Test for empty string suffix (Core fix for the reported issue)
def test_empty_json_schema_suffix_logic():
    gen = GenerateJsonSchema(
        validation_name_strategy='Input',  # Default value
        serialization_name_strategy=''  # <--- Empty string (Key test case)
    )
    dummy_ref = "my_module:MyModel:12345"

    # Check Serialization mode (where the empty string is applied)
    gen.get_defs_ref((dummy_ref, 'serialization'))

    all_choices_ser = []
    for choices in gen._prioritized_defsref_choices.values():
        all_choices_ser.extend(choices)

    print("Empty Suffix Choices:", all_choices_ser)  # For debugging

    # [Verify 1] The 'clean name' without a suffix must be present in the candidates
    # (This ensures a clean name can be selected without causing a StopIteration error)
    assert 'my_module_MyModel' in all_choices_ser, "Empty suffix candidate is missing"

    # [Verify 2] Important! There should be no name with a dangling dash like 'MyModel-'
    # This ensures that the fix prevents the generation of names with dangling dashes.
    assert 'my_module_MyModel-' not in all_choices_ser, "Dangling dash found! Logic is not clean."