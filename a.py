import pydantic


@pydantic.dataclasses.dataclass
class User:
    age: int

    # def __post_init__(self):
    #     print("triggered post init")

    def __post_init_post_parse__(self):
        print("triggered post init post parse")


# print(dir(User))
#
# print(User.__post_init_post_parse__())


a = User(age=1)
