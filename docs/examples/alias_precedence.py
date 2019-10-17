from pydantic import BaseModel

class Voice(BaseModel):
    name: str
    language_code: str

    class Config:
        @classmethod
        def alias_generator(cls, string: str) -> str:
            # this is the same as `alias_generator = to_camel` above
            return ''.join(word.capitalize() for word in string.split('_'))

class Character(Voice):
    mood: str

    class Config:
        fields = {'mood': 'Mood', 'language_code': 'lang'}

c = Character(Mood='happy', Name='Filiz', lang='tr-TR')
print(c)
print(c.dict(by_alias=True))
