import gc
import pickle

from pydantic._internal._model_construction import _PydanticWeakRef


class IntWrapper:
    def __init__(self, v: int):
        self._v = v

    def get(self) -> int:
        return self._v

    def __eq__(self, other: 'IntWrapper') -> bool:
        return self.get() == other.get()


def test_pickle_pydantic_weakref():
    obj1 = IntWrapper(1)
    ref1 = _PydanticWeakRef(obj1)
    assert ref1() is obj1

    obj2 = IntWrapper(2)
    ref2 = _PydanticWeakRef(obj2)
    assert ref2() is obj2

    ref3 = _PydanticWeakRef(IntWrapper(3))
    gc.collect() # PyPy does not use reference counting and always relies on GC.
    assert ref3() is None

    d = {
        # Hold a hard reference to the underlying object for ref1 that will also
        # be pickled.
        'hard_ref': obj1,
        # ref1's underlying object has a hard reference in the pickled object so it
        # should maintain the reference after deserialization.
        'has_hard_ref': ref1,
        # ref2's underlying object has no hard reference in the pickled object so it
        # should be `None` after deserialization.
        'has_no_hard_ref': ref2,
        # ref3's underlying object had already gone out of scope before pickling so it
        # should be `None` after deserialization.
        'ref_out_of_scope': ref3,
    }

    loaded = pickle.loads(pickle.dumps(d))
    gc.collect() # PyPy does not use reference counting and always relies on GC.

    assert loaded['hard_ref'] == IntWrapper(1)
    assert loaded['has_hard_ref']() is loaded['hard_ref']
    assert loaded['has_no_hard_ref']() is None
    assert loaded['ref_out_of_scope']() is None
