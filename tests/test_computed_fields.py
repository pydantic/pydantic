from pydantic import BaseModel
from pydantic.fields import field


def test_computed_fields_get():
    class Rectangle(BaseModel):
        width: int
        length: int

        @field
        @property
        def area(self) -> int:
            """An awesome area"""
            return self.width * self.length

        @field(title='Pikarea', description='Another area')
        @property
        def area2(self) -> int:
            return self.width * self.length

        @property
        def double_width(self) -> int:
            return self.width * 2

    rect = Rectangle(width=10, length=5)
    assert set(rect.__fields__) == {'width', 'length'}
    assert set(rect.__computed_fields__) == {'area', 'area2'}
    assert rect.__dict__ == {'width': 10, 'length': 5}

    assert rect.area == 50
    assert rect.double_width == 20
    assert rect.dict() == {'width': 10, 'length': 5, 'area': 50, 'area2': 50}
    assert rect.json() == '{"width": 10, "length": 5, "area": 50, "area2": 50}'
    assert rect.schema() == {
        'title': 'Rectangle',
        'type': 'object',
        'properties': {
            'width': {
                'title': 'Width',
                'type': 'integer',
            },
            'length': {
                'title': 'Length',
                'type': 'integer',
            },
            'area': {
                'title': 'Area',
                'description': 'An awesome area',
                'type': 'integer',
                'readOnly': True,
            },
            'area2': {
                'title': 'Pikarea',
                'description': 'Another area',
                'type': 'integer',
                'readOnly': True,
            },
        },
        'required': ['width', 'length'],
    }


def test_computed_fields_set():
    class Square(BaseModel):
        side: float

        @field
        def area(self) -> float:
            return self.side ** 2

        @area.setter
        def area(self, new_area: int):
            self.side = new_area ** 0.5

    r = Square(side=10)
    assert r.dict() == {'side': 10.0, 'area': 100.0}
    r.area = 64
    assert r.dict() == {'side': 8.0, 'area': 64.0}
