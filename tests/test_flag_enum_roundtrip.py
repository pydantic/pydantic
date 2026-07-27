from enum import Flag, auto

import pytest

from pydantic import BaseModel


class Color(Flag):
    RED = auto()
    GREEN = auto()
    BLUE = auto()


class Palette(BaseModel):
    counts: dict[Color, int]


def test_single_member_key_roundtrips():
    m = Palette(counts={Color.RED: 1})
    reloaded = Palette.model_validate_json(m.model_dump_json())
    assert reloaded == m


def test_combined_member_key_roundtrips():
    m = Palette(counts={Color.RED | Color.BLUE: 5})
    reloaded = Palette.model_validate_json(m.model_dump_json())
    assert reloaded == m


def test_multiple_keys_including_combined_roundtrip():
    m = Palette(counts={
        Color.RED: 1,
        Color.GREEN | Color.BLUE: 2,
        Color.RED | Color.GREEN | Color.BLUE: 3,
    })
    reloaded = Palette.model_validate_json(m.model_dump_json())
    assert reloaded == m