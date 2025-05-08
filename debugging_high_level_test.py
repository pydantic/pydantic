"""
debug_schema_custom_names.py

Run with:

    python debug_schema_custom_names.py

The script generates JSON Schema for a series of generic–literal models,
then prints **expected vs. actual** `$defs` keys so you can visually confirm
the custom-naming patch (#7376).

It is *not* a pytest file; no assertions are raised.
"""

from pprint import pprint
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel
from pydantic.json_schema import models_json_schema

T = TypeVar("T")


def defs_keys(model, mode: str = "validation") -> set[str]:
    """
    Return the set of `$defs` keys created for *model* when we ask Pydantic
    to generate a schema for that single (model, mode) pair.

    Using ``models_json_schema`` rather than ``model_json_schema`` guarantees
    Pydantic places every model in the `$defs` section (it never in-lines).
    """
    _, defs = models_json_schema([(model, mode)])
    return set(defs.get("$defs", {}))


def show(label: str, expected: set[str] | str, actual: set[str]) -> None:
    print(f"\n── {label} ──")
    print("expected :", expected)
    print("actual   :", actual)
    if isinstance(expected, set):
        print("subset?  :", expected <= actual)


# single custom named generic
class MixBarBaz(BaseModel):
    @classmethod
    def model_parametrized_name(cls, params: tuple) -> str:
        return "G_bar_baz"


class G(MixBarBaz, Generic[T]):
    foo: T


single_keys = defs_keys(G[Literal["bar", "baz"]])
show("single-mode", {"G_bar_baz-Input"}, single_keys)


# spam/eggs in both modes
class MixSE(BaseModel):
    @classmethod
    def model_parametrized_name(cls, p: tuple) -> str:
        return f"Box_{p[0].__args__[0]}"


class Box(MixSE, Generic[T]):
    x: T


for mode, suff in [("validation", "Input"), ("serialization", "Output")]:
    keys = defs_keys(Box[Literal["spam"]], mode) | defs_keys(
        Box[Literal["eggs"]], mode
    )
    show(f"spam/eggs  ({mode})", {f"Box_spam-{suff}", f"Box_eggs-{suff}"}, keys)


# nested usage
class MixXY(BaseModel):
    @classmethod
    def model_parametrized_name(cls, p: tuple) -> str:
        return "Wrapper_xy"


class Wrapper(MixXY, Generic[T]):
    v: T


class UsesWrapper(BaseModel):
    w: Wrapper[Literal["x", "y"]]


nested_keys = defs_keys(UsesWrapper)
show("nested", {"Wrapper_xy-Input"}, nested_keys)


# legacy generic (no override)
class Legacy(BaseModel, Generic[T]):
    foo: T


legacy_expected = {"Legacy_Literal__a____b___-Input"}
legacy_keys = defs_keys(Legacy[Literal["a", "b"]])
show("legacy (no override)", legacy_expected, legacy_keys)


# custom generic + plain model, same call
class PrettyMixin(BaseModel):
    @classmethod
    def model_parametrized_name(cls, p: tuple) -> str:
        return "PrettyWrapper"


class PrettyWrapper(PrettyMixin, Generic[T]):
    v: T


class Plain(BaseModel):
    colour: str


_, defs_mix = models_json_schema(
    [(PrettyWrapper[Literal["red"]], "validation"), (Plain, "validation")]
)
mix_keys = set(defs_mix.get("$defs", {}))
show("mixed custom + plain", {"PrettyWrapper-Input", "Plain"}, mix_keys)


# collision -- two classes claim same custom name
class ClashMixin(BaseModel):
    @classmethod
    def model_parametrized_name(cls, p: tuple) -> str:  # noqa: D401
        return "Clash"


class G1(ClashMixin, Generic[T]):
    a: T


class G2(ClashMixin, Generic[T]):
    b: T


_, defs_collision = models_json_schema(
    [(G1[Literal["q"]], "validation"), (G2[Literal["q"]], "validation")]
)
collision_keys = set(defs_collision.get("$defs", {}))
show("collision (one shared key expected)", {"Clash-Input"}, collision_keys)
print("$defs content:")
pprint(defs_collision["$defs"], width=100, sort_dicts=False)
