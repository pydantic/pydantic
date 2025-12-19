from pydantic import BaseModel

def test_issue_10630_recursion_error():
    class A(BaseModel):
        a: 'A | None' = None

    a = A()
    a.a = a
    a2 = A()
    a2.a = a2

    # Should not raise RecursionError
    assert a == a2
