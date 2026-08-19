from pydantic import BaseModel
def test_multiple_inheritance_mro_fields():
    class Base(BaseModel):
        f: str = "base"
    class Override(Base):
        f: str = "override"
    class Plain(Base):
        pass
    class Swapped(Plain, Override):
        pass
    class Composed(Override, Plain):
        pass

    assert Swapped().f == "override"
    assert Composed().f == "override"
