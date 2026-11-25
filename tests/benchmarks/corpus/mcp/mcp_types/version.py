# Frozen from MCP 2.3.0; see corpus README.md and LICENSE.
from typing import Final
KNOWN_PROTOCOL_VERSIONS: Final[tuple[str, ...]] = ('2024-11-05', '2025-03-26', '2025-06-18', '2025-11-25', '2026-07-28')
HANDSHAKE_PROTOCOL_VERSIONS: Final[tuple[str, ...]] = ('2024-11-05', '2025-03-26', '2025-06-18', '2025-11-25')
MODERN_PROTOCOL_VERSIONS: Final[tuple[str, ...]] = ('2026-07-28',)
SUPPORTED_PROTOCOL_VERSIONS: tuple[str, ...] = (*HANDSHAKE_PROTOCOL_VERSIONS, *MODERN_PROTOCOL_VERSIONS)
LATEST_PROTOCOL_VERSION: Final[str] = KNOWN_PROTOCOL_VERSIONS[-1]
LATEST_HANDSHAKE_VERSION: Final[str] = HANDSHAKE_PROTOCOL_VERSIONS[-1]
LATEST_MODERN_VERSION: Final[str] = MODERN_PROTOCOL_VERSIONS[-1]
OLDEST_SUPPORTED_VERSION: Final[str] = HANDSHAKE_PROTOCOL_VERSIONS[0]

def is_version_at_least(version: str, minimum: str) -> bool:
    if minimum not in KNOWN_PROTOCOL_VERSIONS:
        raise ValueError(f'minimum must be a known protocol version, got {minimum!r}')
    if version not in KNOWN_PROTOCOL_VERSIONS:
        return False
    return KNOWN_PROTOCOL_VERSIONS.index(version) >= KNOWN_PROTOCOL_VERSIONS.index(minimum)
