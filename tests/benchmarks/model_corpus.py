"""Load frozen SDK model sources as fresh, isolated package graphs."""

import importlib
import importlib.abc
import importlib.machinery
import importlib.util
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from types import CodeType, ModuleType

from pydantic import BaseModel

IS_PYPY = sys.implementation.name == 'pypy'


class CorpusImporter(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.manifest = json.loads((directory / 'manifest.json').read_text())
        self.roots: tuple[str, ...] = tuple(self.manifest['roots'])
        self.sources: dict[str, tuple[CodeType, bool]] = {}
        for source in sorted(directory.rglob('*.py')):
            parts = source.relative_to(directory).with_suffix('').parts
            is_package = parts[-1] == '__init__'
            name = '.'.join(parts[:-1] if is_package else parts)
            self.sources[name] = compile(source.read_text(), str(source), 'exec'), is_package

    def is_corpus_module(self, name: str) -> bool:
        return any(name == root or name.startswith(root + '.') for root in self.roots)

    def find_spec(
        self, fullname: str, path: Sequence[str] | None = None, target: ModuleType | None = None
    ) -> importlib.machinery.ModuleSpec | None:
        if not self.is_corpus_module(fullname):
            return None
        if fullname not in self.sources:
            raise ModuleNotFoundError(f'Module missing from frozen corpus: {fullname}', name=fullname)
        return importlib.util.spec_from_loader(fullname, self, is_package=self.sources[fullname][1])

    def create_module(self, spec: importlib.machinery.ModuleSpec) -> None:
        return None

    def exec_module(self, module: ModuleType) -> None:
        exec(self.sources[module.__name__][0], module.__dict__)

    def build_models(self) -> list[type[BaseModel]]:
        previous = {name: module for name, module in sys.modules.copy().items() if self.is_corpus_module(name)}
        for name in previous:
            sys.modules.pop(name)
        sys.meta_path.insert(0, self)
        previous_limit = sys.getrecursionlimit() if IS_PYPY else None
        try:
            # PyPy uses this limit as a native-stack budget. Deep SDK graphs can
            # overflow cpyext's default budget instead of raising RecursionError.
            if previous_limit is not None and previous_limit < 2000:
                sys.setrecursionlimit(2000)
            modules = [importlib.import_module(name) for name in self.manifest['declarations']]
            models = list(
                dict.fromkeys(
                    value
                    for module in modules
                    for value in vars(module).values()
                    if isinstance(value, type)
                    and issubclass(value, BaseModel)
                    and self.is_corpus_module(value.__module__)
                )
            )
            for model in sorted(models, key=lambda cls: (cls.__module__, cls.__name__)):
                model.model_rebuild()
            return models
        finally:
            sys.meta_path.remove(self)
            for name in list(sys.modules):
                if self.is_corpus_module(name):
                    sys.modules.pop(name)
            sys.modules.update(previous)
            if previous_limit is not None and previous_limit < 2000:
                sys.setrecursionlimit(previous_limit)
