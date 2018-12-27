from pydantic import UrlStr
from pydantic.dataclasses import dataclass

@dataclass
class NavbarButton:
    href: UrlStr

@dataclass
class Navbar:
    button: NavbarButton

navbar = Navbar(button=('https://example.com',))
print(navbar)
# > Navbar(button=NavbarButton(href='https://example.com'))
