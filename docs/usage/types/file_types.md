`FilePath`
: like `Path`, but the path must exist and be a file

```py
from pydantic import BaseModel, FilePath, ValidationError


class Model(BaseModel):
    f: FilePath


m = Model(f='docs/usage/types/file_types.md')
print(m.model_dump())
#> {'f': PosixPath('docs/usage/types/file_types.md')}

try:
    Model(f='docs/usage/types/')  # directory
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    f
      Path does not point to a file [type=path_not_file, input_value='docs/usage/types/', input_type=str]
    """

try:
    Model(f='docs/usage/types/not-exists-file')
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    f
      Path does not point to a file [type=path_not_file, input_value='docs/usage/types/not-exists-file', input_type=str]
    """
```

`DirectoryPath`
: like `Path`, but the path must exist and be a directory

```py
from pydantic import BaseModel, DirectoryPath, ValidationError


class Model(BaseModel):
    f: DirectoryPath


m = Model(f='docs/usage/types/')
print(m.model_dump())
#> {'f': PosixPath('docs/usage/types')}

try:
    Model(f='docs/usage/types/file_types.md')  # file
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    f
      Path does not point to a directory [type=path_not_directory, input_value='docs/usage/types/file_types.md', input_type=str]
    """

try:
    Model(f='docs/usage/not-exists-directory')
except ValidationError as e:
    print(e)
    """
    1 validation error for Model
    f
      Path does not point to a directory [type=path_not_directory, input_value='docs/usage/not-exists-directory', input_type=str]
    """
```
