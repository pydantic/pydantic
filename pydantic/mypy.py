from collections import OrderedDict
from functools import partial
from typing import Callable, Dict, List, Set, Type as TypingType, TypeVar

from mypy.nodes import (
    ARG_NAMED,
    ARG_NAMED_OPT,
    ARG_STAR2,
    MDEF,
    Any,
    Argument,
    AssignmentStmt,
    CallExpr,
    ClassDef,
    EllipsisExpr,
    JsonDict,
    MemberExpr,
    NameExpr,
    PlaceholderNode,
    StrExpr,
    SymbolTableNode,
    TempNode,
    TypeInfo,
    Var,
)
from mypy.plugin import ClassDefContext, Plugin
from mypy.plugins.common import add_method
from mypy.server.trigger import make_wildcard_trigger
from mypy.types import AnyType, NoneTyp, Optional, TypeOfAny, UnionType

T = TypeVar('T')
CB = Optional[Callable[[T], None]]

BASEMODEL_NAME = 'pydantic.main.BaseModel'


class PydanticPlugin(Plugin):
    pydantic_strict: bool = False

    def get_base_class_hook(self, fullname: str) -> 'CB[ClassDefContext]':
        # This function is called on any class that is the base class for another class
        sym = self.lookup_fully_qualified(fullname)
        if sym and isinstance(sym.node, TypeInfo):
            if is_model(sym.node):
                return partial(pydantic_model_class_maker_callback, strict=self.pydantic_strict)
        return None


class StrictPydanticPlugin(PydanticPlugin):
    pydantic_strict: bool = True


def is_model(info: TypeInfo) -> bool:
    for base in info.mro:
        if base.fullname() == BASEMODEL_NAME:
            return True
    return False


class PydanticModelField:
    def __init__(self, name: str, has_default: bool, line: int, column: int) -> None:
        self.name = name
        self.has_default = has_default
        self.line = line
        self.column = column

    def to_argument(self, info: TypeInfo, strict: bool) -> Argument:
        if strict:
            type_annotation = info[self.name].type
        else:
            type_annotation = AnyType(TypeOfAny.explicit)
        return Argument(
            variable=self.to_var(info),
            type_annotation=type_annotation,
            initializer=None,
            kind=ARG_NAMED_OPT if self.has_default else ARG_NAMED,
        )

    def to_var(self, info: TypeInfo) -> Var:
        return Var(self.name, info[self.name].type)

    def serialize(self) -> JsonDict:
        return {'name': self.name, 'has_default': self.has_default, 'line': self.line, 'column': self.column}

    @classmethod
    def deserialize(cls, info: TypeInfo, data: JsonDict) -> 'PydanticModelField':
        return cls(**data)


class PydanticModelTransformer:
    def __init__(self, ctx: ClassDefContext, strict: bool) -> None:
        self._ctx = ctx
        self.config_fields = ('extra', 'allow_mutation', 'use_enum_values', 'arbitrary_types_allowed', 'orm_mode')
        self.strict = strict

    def add_basemodel_init(self, attributes: List[PydanticModelField], config: Dict[str, Any]) -> None:
        ctx = self._ctx
        init_arguments = [attribute.to_argument(ctx.cls.info, strict=self.strict) for attribute in attributes]
        if config.get('extra') is not False and not self.strict:
            var = Var('kwargs')
            init_arguments.append(Argument(var, AnyType(TypeOfAny.explicit), None, ARG_STAR2))
        add_method(ctx, '__init__', init_arguments, NoneTyp())

    def transform(self) -> None:
        ctx = self._ctx
        info = self._ctx.cls.info

        attributes = self.collect_attributes()

        config = self.collect_config()

        if ctx.api.options.new_semantic_analyzer:
            # Check if attribute types are ready.
            for attr in attributes:
                if info[attr.name].type is None:
                    # TODO: Figure out why this is necessary
                    if not ctx.api.final_iteration:
                        ctx.api.defer()
                    return

        self.add_basemodel_init(attributes, config)
        if config.get('allow_mutation') is False:
            self._freeze(attributes)
        info.metadata['pydanticmodel'] = {
            'attributes': OrderedDict((attr.name, attr.serialize()) for attr in attributes),
            'config': config,
        }

    def collect_config(self) -> Dict[str, Any]:
        ctx = self._ctx
        cls = self._ctx.cls
        config = {}
        for stmt in cls.defs.body:
            if not isinstance(stmt, ClassDef):
                continue
            for substmt in stmt.defs.body:
                if not isinstance(substmt, AssignmentStmt):
                    continue
                config.update(self.get_config_update(substmt))

        for info in cls.info.mro[1:-1]:  # 0 is the current class, -1 is object
            if 'pydanticmodel' not in info.metadata:
                continue

            # Each class depends on the set of attributes in its dataclass ancestors.
            ctx.api.add_plugin_dependency(make_wildcard_trigger(info.fullname()))

            for name, value in info.metadata['pydanticmodel']['config'].items():
                if name not in config:
                    config[name] = value
        return config

    def get_config_update(self, substmt: AssignmentStmt) -> Dict[str, Any]:
        lhs = substmt.lvalues[0]
        if not (isinstance(lhs, NameExpr) and lhs.name in self.config_fields):
            return {}
        if lhs.name == 'extra':
            if isinstance(substmt.rvalue, StrExpr):
                extra_value = substmt.rvalue.value != 'forbid'
            elif isinstance(substmt.rvalue, MemberExpr):
                extra_value = substmt.rvalue.name != 'forbid'
            else:
                return {}
            return {lhs.name: extra_value}
        if not isinstance(substmt.rvalue, NameExpr):
            return {}
        if substmt.rvalue.fullname in ('builtins.True', 'builtins.False'):
            return {lhs.name: substmt.rvalue.fullname == 'builtins.True'}
        return {}

    def collect_attributes(self) -> List[PydanticModelField]:
        # First, collect attributes belonging to the current class.
        ctx = self._ctx
        cls = self._ctx.cls
        attrs = []  # type: List[PydanticModelField]
        known_attrs = set()  # type: Set[str]
        for stmt in cls.defs.body:

            if not isinstance(stmt, AssignmentStmt):  # `and stmt.new_syntax` to require annotation
                continue

            lhs = stmt.lvalues[0]
            if not isinstance(lhs, NameExpr):
                continue

            if lhs.name == '__config__':  # BaseConfig not well handled; I'm not sure why yet
                continue

            sym = cls.info.names.get(lhs.name)
            if sym is None:
                assert ctx.api.options.new_semantic_analyzer
                continue

            node = sym.node
            if isinstance(node, PlaceholderNode):
                # This node is not ready yet.
                continue
            assert isinstance(node, Var)

            # x: ClassVar[int] is ignored by dataclasses.
            if node.is_classvar:
                continue

            has_default = self._get_has_default(cls, stmt, lhs)
            known_attrs.add(lhs.name)
            attrs.append(PydanticModelField(name=lhs.name, has_default=has_default, line=stmt.line, column=stmt.column))

        all_attrs = attrs.copy()
        for info in cls.info.mro[1:-2]:  # 0 is the current class, -2 is BaseModel, -1 is object
            if 'pydanticmodel' not in info.metadata:
                continue

            super_attrs = []
            # Each class depends on the set of attributes in its dataclass ancestors.
            ctx.api.add_plugin_dependency(make_wildcard_trigger(info.fullname()))

            for name, data in info.metadata['pydanticmodel']['attributes'].items():
                if name not in known_attrs:
                    attr = PydanticModelField.deserialize(info, data)
                    known_attrs.add(name)
                    super_attrs.append(attr)
                else:
                    (attr,) = [a for a in all_attrs if a.name == name]
                    all_attrs.remove(attr)
                    super_attrs.append(attr)
            all_attrs = super_attrs + all_attrs
        return all_attrs

    def _get_has_default(self, cls: ClassDef, stmt: AssignmentStmt, lhs: NameExpr) -> bool:
        if not isinstance(stmt.rvalue, TempNode):
            if isinstance(stmt.rvalue, CallExpr):
                callee = stmt.rvalue.callee
                if not isinstance(callee, (NameExpr, MemberExpr)):
                    return True
                callee_is_schema = callee.fullname == 'pydantic.schema.Schema'
                arg_is_ellipsis = len(stmt.rvalue.args) > 0 and type(stmt.rvalue.args[0]) is EllipsisExpr
                if callee_is_schema and arg_is_ellipsis:
                    return False
            return True
        value_type = cls.info[lhs.name].type
        if type(value_type) is UnionType:
            item_types = [type(item) for item in value_type.items]  # type: ignore
            if NoneTyp in item_types:
                # Optional has default of None
                return True
        return False

    def _freeze(self, attributes: List[PydanticModelField]) -> None:
        """
        Converts all attributes to @property methods in order to
        emulate frozen classes.
        """
        info = self._ctx.cls.info
        for attr in attributes:
            sym_node = info.names.get(attr.name)
            if sym_node is not None:
                var = sym_node.node
                assert isinstance(var, Var)
                var.is_property = True
            else:
                var = attr.to_var(info)
                var.info = info
                var.is_property = True
                var._fullname = info.fullname() + '.' + var.name()
                info.names[var.name()] = SymbolTableNode(MDEF, var)


def pydantic_model_class_maker_callback(ctx: ClassDefContext, strict: bool) -> None:
    transformer = PydanticModelTransformer(ctx, strict)
    transformer.transform()


def plugin(version: str) -> 'TypingType[Plugin]':
    return PydanticPlugin


def strict(version: str) -> 'TypingType[Plugin]':
    return StrictPydanticPlugin
