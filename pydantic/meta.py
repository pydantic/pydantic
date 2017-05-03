import ast
import sys
from pathlib import Path


def find_fields(module, cls_name):

    path = Path(sys.modules[module].__file__).resolve()

    file_node = ast.parse(path.read_text(), filename=path.name)
    cls_node = None
    for n in file_node.body:
        if isinstance(n, ast.ClassDef) and n.name == cls_name:
            cls_node = n
            break
    if cls_name is None:
        raise RuntimeError(f"can't find {cls_name} in {file_node}")
    _expression = None
    for n in cls_node.body:
        if isinstance(n, ast.Expr) and isinstance(n.value, ast.Str):
            _expression = n.value.s
            continue
        # print(ast.dump(n))
        if not isinstance(n, (ast.AnnAssign, ast.Assign)):
            _expression = None
            continue
        target = getattr(n, 'target', None) or n.targets[0]
        name = target.id
        if name.startswith('_'):
            _expression = None
            continue

        yield name, _expression
        _expression = None
