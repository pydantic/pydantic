"""TOON (Token-Oriented Object Notation) parser and validator for Pydantic.

TOON is a token-efficient data format designed for LLM applications.
This module provides parsing functionality to convert TOON format strings
into Python dictionaries that can be validated by Pydantic models.
"""

from __future__ import annotations as _annotations

import re
from typing import Any

from pydantic.errors import PydanticUserError


class ToonParseError(PydanticUserError):
    """Raised when TOON parsing fails."""

    def __init__(self, message: str, position: int | None = None) -> None:
        """Initialize a TOON parse error.

        Args:
            message: Error message describing the parse failure.
            position: Optional character position where the error occurred.
        """
        super().__init__(message, code='toon-parse-error')
        self.position = position


def parse_toon(toon_data: str | bytes | bytearray) -> Any:
    """Parse TOON format string into Python data structures.

    TOON (Token-Oriented Object Notation) is a token-efficient format
    designed for LLM applications. This parser converts TOON format
    into Python dictionaries and lists that can be validated by Pydantic.

    Args:
        toon_data: TOON format string, bytes, or bytearray.

    Returns:
        Parsed Python data structure (dict, list, or primitive values).

    Raises:
        ToonParseError: If the TOON data cannot be parsed.

    Examples:
        >>> parse_toon('users[2]{id,name}:\\n  1,Alice\\n  2,Bob')
        {'users': [{'id': 1, 'name': 'Alice'}, {'id': 2, 'name': 'Bob'}]}

        >>> parse_toon('settings:\\n  theme: dark\\n  notifications: true')
        {'settings': {'theme': 'dark', 'notifications': True}}
    """
    if isinstance(toon_data, (bytes, bytearray)):
        try:
            toon_str = toon_data.decode('utf-8')
        except UnicodeDecodeError as e:
            raise ToonParseError(f'Invalid UTF-8 encoding: {e}') from e
    else:
        toon_str = toon_data

    if not toon_str.strip():
        return {}

    parser = _ToonParser(toon_str)
    return parser.parse()


class _ToonParser:
    """Internal TOON parser implementation."""

    def __init__(self, data: str) -> None:
        """Initialize the parser with TOON data.

        Args:
            data: TOON format string to parse.
        """
        self.data = data
        self.pos = 0
        self.lines = data.splitlines()
        self.current_line = 0
        self.current_col = 0

    def parse(self) -> Any:
        """Parse the TOON data starting from the current position.

        Returns:
            Parsed Python data structure.
        """
        result = {}
        while self.current_line < len(self.lines):
            line = self.lines[self.current_line].rstrip()
            if not line or line.strip().startswith('#'):
                # Skip empty lines and comments
                self.current_line += 1
                continue

            key, value = self._parse_line(line)
            if key is not None:
                result[key] = value

            self.current_line += 1

        return result if result else None

    def _parse_line(self, line: str) -> tuple[str | None, Any]:
        """Parse a single line of TOON data.

        Args:
            line: Line to parse.

        Returns:
            Tuple of (key, value) or (None, None) if line should be skipped.
        """
        line = line.strip()
        if not line or line.startswith('#'):
            return None, None

        # Check for array declaration: key[count]{field1,field2,...}:
        array_match = re.match(r'^(\w+)\[(\d+)\]\{([^}]+)\}\s*:', line)
        if array_match:
            key = array_match.group(1)
            count = int(array_match.group(2))
            fields = [f.strip() for f in array_match.group(3).split(',')]
            array_data = self._parse_array_data(count, fields)
            return key, array_data

        # Check for key: value (simple key-value pair)
        if ':' in line:
            parts = line.split(':', 1)
            if len(parts) == 2:
                key = parts[0].strip()
                value_str = parts[1].strip()
                
                # Check if next line has indentation (nested object)
                if self.current_line + 1 < len(self.lines):
                    next_line = self.lines[self.current_line + 1]
                    next_indent = self._get_line_indent(self.current_line + 1)
                    current_indent = self._get_line_indent(self.current_line)
                    
                    # If next line is indented more and value is empty, it's a nested object
                    if next_indent > current_indent and not value_str:
                        nested_data = self._parse_nested_object()
                        return key, nested_data
                
                # Otherwise, parse as simple value
                value = self._parse_value(value_str)
                return key, value

        return None, None

    def _parse_array_data(self, count: int, fields: list[str]) -> list[dict[str, Any]]:
        """Parse array data rows.

        Args:
            count: Expected number of rows.
            fields: List of field names.

        Returns:
            List of dictionaries representing the array items.
        """
        array_data = []
        initial_indent = self._get_line_indent(self.current_line)

        for i in range(count):
            self.current_line += 1
            if self.current_line >= len(self.lines):
                if i < count - 1:
                    raise ToonParseError(
                        f'Expected {count} array items, but only found {i + 1}',
                        position=self.pos,
                    )
                break

            line = self.lines[self.current_line].rstrip()
            line_indent = self._get_line_indent(self.current_line)

            # Check if we've moved to a different indentation level (end of array)
            # But only if the line is not empty and not a comment
            if line.strip() and not line.strip().startswith('#'):
                if line_indent <= initial_indent:
                    if i < count - 1:
                        raise ToonParseError(
                            f'Expected {count} array items, but only found {i + 1}',
                            position=self.pos,
                        )
                    # Put the line back for the next parser iteration
                    self.current_line -= 1
                    break

            if not line.strip() or line.strip().startswith('#'):
                # Skip empty lines and comments within array
                i -= 1  # Don't count this as an array item
                continue

            # Parse comma-separated values
            values = [v.strip() for v in line.split(',')]
            if len(values) != len(fields):
                raise ToonParseError(
                    f'Row {i + 1} has {len(values)} values but {len(fields)} fields expected',
                    position=self.pos,
                )

            # Create dictionary from fields and values
            item = {}
            for field, value_str in zip(fields, values):
                item[field] = self._parse_value(value_str)
            array_data.append(item)

        if len(array_data) != count:
            raise ToonParseError(
                f'Expected {count} array items, but found {len(array_data)}',
                position=self.pos,
            )

        return array_data

    def _parse_nested_object(self) -> dict[str, Any]:
        """Parse a nested object structure.

        Returns:
            Dictionary representing the nested object.
        """
        nested = {}
        base_indent = self._get_line_indent(self.current_line)

        # Parse nested content, consuming lines as we go
        self.current_line += 1
        while self.current_line < len(self.lines):
            line = self.lines[self.current_line].rstrip()
            if not line or line.strip().startswith('#'):
                self.current_line += 1
                continue

            line_indent = self._get_line_indent(self.current_line)

            # If indentation decreased or equal, we've left this object
            if line_indent <= base_indent and line.strip():
                # Put the line back for the next parser iteration
                self.current_line -= 1
                break

            # Parse this nested line
            if line_indent > base_indent:
                # Check if it's an array
                array_match = re.match(
                    r'^' + ' ' * line_indent + r'(\w+)\[(\d+)\]\{([^}]+)\}\s*:', line
                )
                if array_match:
                    key = array_match.group(1)
                    count = int(array_match.group(2))
                    fields = [f.strip() for f in array_match.group(3).split(',')]
                    array_data = self._parse_array_data(count, fields)
                    nested[key] = array_data
                    # _parse_array_data already advances current_line, so continue
                    continue
                else:
                    # Regular key-value pair
                    if ':' in line:
                        parts = line.split(':', 1)
                        if len(parts) == 2:
                            key = parts[0].strip()
                            value_str = parts[1].strip()
                            # Check if this is another nested object
                            if self.current_line + 1 < len(self.lines):
                                next_line = self.lines[self.current_line + 1]
                                next_indent = self._get_line_indent(self.current_line + 1)
                                if next_indent > line_indent and not value_str:
                                    # Recursively parse nested object
                                    saved_line = self.current_line
                                    nested_value = self._parse_nested_object()
                                    nested[key] = nested_value
                                    # _parse_nested_object already advances current_line
                                    continue
                            value = self._parse_value(value_str)
                            nested[key] = value

            self.current_line += 1

        return nested

    def _parse_value(self, value_str: str) -> Any:
        """Parse a single value string into Python value.

        Args:
            value_str: String representation of the value.

        Returns:
            Parsed Python value (int, float, bool, str, or None).
        """
        if not value_str:
            return None

        # Try to parse as boolean
        if value_str.lower() == 'true':
            return True
        if value_str.lower() == 'false':
            return False

        # Try to parse as null/None
        if value_str.lower() == 'null' or value_str.lower() == 'none':
            return None

        # Try to parse as number (int or float)
        try:
            # Check if it's an integer
            if '.' not in value_str and 'e' not in value_str.lower():
                return int(value_str)
            return float(value_str)
        except ValueError:
            pass

        # Return as string (remove quotes if present)
        if value_str.startswith('"') and value_str.endswith('"'):
            return value_str[1:-1]
        if value_str.startswith("'") and value_str.endswith("'"):
            return value_str[1:-1]

        return value_str

    def _get_line_indent(self, line_num: int) -> int:
        """Get the indentation level of a line.

        Args:
            line_num: Line number to check.

        Returns:
            Number of leading spaces.
        """
        if line_num >= len(self.lines):
            return 0
        line = self.lines[line_num]
        return len(line) - len(line.lstrip())

