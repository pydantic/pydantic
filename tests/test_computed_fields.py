from pydantic import BaseModel
from pydantic.fields import field


def test_computed_fields():
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
