Changes to email validation: whitespace is stripped from names, e.g. `' Fred Smith <fred@example.com>'`,
unicode NFC normalization is applied to the local part, the domain part is cleaned to the internationalized form 
by round-tripping through IDNA ASCII, better error messages are provided when validation fails
