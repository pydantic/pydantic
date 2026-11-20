import pytest

from pydantic import BaseModel, ImportString, TypeAdapter, ValidationError


@pytest.mark.parametrize('value', ['.os', '..os', '.', '..', '.os:path', '.os.path', ' .os', '\t.os'])
def test_import_string_relative_path_is_validation_error(value: str) -> None:
    with pytest.raises(
        ValidationError,
        check=lambda err: (
            err.errors()[0]['type'] == 'import_error'
            and err.errors()[0]['msg']
            == f'Invalid python path: Import strings should not be relative; received {value!r}'
        ),
    ):
        TypeAdapter(ImportString).validate_python(value)


def test_import_string_relative_path_in_model() -> None:
    class ImportThings(BaseModel):
        obj: ImportString

    with pytest.raises(
        ValidationError,
        check=lambda err: err.errors()[0]['loc'] == ('obj',) and err.errors()[0]['type'] == 'import_error',
    ):
        ImportThings(obj='.os')
