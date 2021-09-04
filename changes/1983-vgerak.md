Create `FileUrl` type that allows URLs that conform to [RFC 8089](https://tools.ietf.org/html/rfc8089#section-2).
Add `host_required` parameter, which is `True` by default (`AnyUrl` and subclasses), `False` in `RedisDsn`, `FileUrl`.
