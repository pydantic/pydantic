from pydantic import AnyUrl
from pydantic.dataclasses import dataclass


@dataclass
class NavbarButton:
    href: AnyUrl


@dataclass
class Navbar:
    button: NavbarButton


navbar = Navbar(button=('https://example.com',))
print(navbar)
