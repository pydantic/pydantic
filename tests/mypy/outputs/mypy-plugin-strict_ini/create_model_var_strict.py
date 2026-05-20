from typing import Any

from pydantic import create_model


def get_fields() -> Any:
    return {'runtime_parameter': (int, ...)}


field_definitions = {'x': (int, ...)}
Model = create_model('Model', **field_definitions)

Model()
# MYPY: error: Missing named argument "x" for "Model"  [call-arg]
Model(x='bad')
# MYPY: error: Argument "x" to "Model" has incompatible type "str"; expected "int"  [arg-type]
Model(y=1)
# MYPY: error: Unexpected keyword argument "y" for "Model"  [call-arg]

model = Model(x=1)
reveal_type(model.x)
# MYPY: note: Revealed type is "builtins.int"

stale_field_definitions: Any = {'stale_parameter': (int, ...)}
stale_field_definitions = get_fields()
StaleModel = create_model('StaleModel', **stale_field_definitions)
stale_model = StaleModel(stale_parameter=1)
# MYPY: error: Unexpected keyword argument "stale_parameter" for "StaleModel"  [call-arg]
stale_parameter = stale_model.stale_parameter
# MYPY: error: "StaleModel" has no attribute "stale_parameter"  [attr-defined]

latest_field_definitions: Any = {'x': (int, ...)}
latest_field_definitions = {'y': (str, ...)}
LatestModel = create_model('LatestModel', **latest_field_definitions)
latest_model = LatestModel(y='ok')
latest_y = latest_model.y
reveal_type(latest_y)
# MYPY: note: Revealed type is "builtins.str"
