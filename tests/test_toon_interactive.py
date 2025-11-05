#!/usr/bin/env python
"""Interactive TOON validator testing script.

This script allows you to test TOON (Token-Oriented Object Notation) parsing
and validation with Pydantic models.

Usage:
    cd pydantic
    uv run python tests/test_toon_interactive.py                    # Interactive mode
    uv run python tests/test_toon_interactive.py --input "toon_data"  # Command line input
    uv run python tests/test_toon_interactive.py --file path/to/file.toon  # From file
"""

import argparse
import sys
from pathlib import Path
from typing import Any

try:
    from pydantic import BaseModel, ValidationError
    from pydantic.toon import ToonParseError, parse_toon
except ImportError:
    # If running from tests directory, try relative import
    import sys
    from pathlib import Path
    
    # Add parent directory to path
    pydantic_path = Path(__file__).parent.parent
    sys.path.insert(0, str(pydantic_path))
    
    try:
        from pydantic import BaseModel, ValidationError
        from pydantic.toon import ToonParseError, parse_toon
    except ImportError:
        print("Error: Pydantic not found. Please install it first.")
        print("Run: cd pydantic && uv sync")
        sys.exit(1)


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


def print_result(data: Any, title: str = "Result") -> None:
    """Print formatted result."""
    print_section(title)
    if isinstance(data, dict):
        import json
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(data)
    print()


def test_parse_only(toon_data: str) -> None:
    """Test parsing TOON without validation."""
    try:
        result = parse_toon(toon_data)
        print_result(result, "Parsed TOON Data")
        print("[SUCCESS] Parsing successful!")
    except ToonParseError as e:
        print_section("Parsing Error")
        print(f"[ERROR] {e}")
        if e.position:
            print(f"   Position: {e.position}")


def test_with_model(toon_data: str, model_class: type[BaseModel] | None = None) -> None:
    """Test TOON parsing and validation with a Pydantic model."""
    if model_class is None:
        # Create a simple generic model
        class GenericModel(BaseModel):
            model_config = {"extra": "allow"}

            pass

        model_class = GenericModel

    try:
        # First parse to show structure
        parsed = parse_toon(toon_data)
        print_result(parsed, "Parsed TOON Structure")

        # Then validate
        instance = model_class.model_validate_toon(toon_data)
        print_result(instance.model_dump(), "Validated Model")
        print("[SUCCESS] Validation successful!")
        print(f"\nModel instance: {instance}")
    except ToonParseError as e:
        print_section("Parsing Error")
        print(f"[ERROR] Parse Error: {e}")
    except ValidationError as e:
        print_section("Validation Error")
        print(f"[ERROR] Validation failed:")
        print(e)
    except Exception as e:
        print_section("Error")
        print(f"[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()


def create_example_model() -> type[BaseModel]:
    """Create an example model for testing."""
    from typing import Optional

    class User(BaseModel):
        id: int
        name: str
        department: str
        salary: int

    class Settings(BaseModel):
        theme: str
        notifications: bool
        max_users: int = 100

    class ExampleModel(BaseModel):
        users: list[User]
        settings: Settings

    return ExampleModel


def interactive_mode() -> None:
    """Run in interactive mode."""
    print_section("TOON Validator Interactive Tester")
    print("Enter TOON data. Use Ctrl+D (Unix) or Ctrl+Z+Enter (Windows) to finish.")
    print("Or type 'exit' to quit.")
    print("\nExample TOON format:")
    print("  users[2]{id,name,age}:")
    print("    1,Alice,30")
    print("    2,Bob,25")
    print("  settings:")
    print("    theme: dark")
    print("    notifications: true")
    print("\n" + "-" * 60)

    lines = []
    while True:
        try:
            line = input()
            if line.strip().lower() == "exit":
                break
            lines.append(line)
        except EOFError:
            break

    toon_data = "\n".join(lines)

    if not toon_data.strip():
        print("No input provided. Exiting.")
        return

    print_section("Testing Options")
    print("1. Parse only (no validation)")
    print("2. Validate with generic model (allows extra fields)")
    print("3. Validate with example model (users + settings)")
    print("4. All of the above")

    choice = input("\nEnter choice (1-4, default=1): ").strip() or "1"

    if choice == "1":
        test_parse_only(toon_data)
    elif choice == "2":
        from pydantic import BaseModel, ConfigDict

        class GenericModel(BaseModel):
            model_config = ConfigDict(extra="allow")

        test_with_model(toon_data, GenericModel)
    elif choice == "3":
        model = create_example_model()
        test_with_model(toon_data, model)
    elif choice == "4":
        print("\n" + "=" * 60)
        print("  TEST 1: Parse Only")
        print("=" * 60)
        test_parse_only(toon_data)

        print("\n" + "=" * 60)
        print("  TEST 2: Generic Model")
        print("=" * 60)
        from pydantic import BaseModel, ConfigDict

        class GenericModel(BaseModel):
            model_config = ConfigDict(extra="allow")

        test_with_model(toon_data, GenericModel)

        print("\n" + "=" * 60)
        print("  TEST 3: Example Model")
        print("=" * 60)
        model = create_example_model()
        test_with_model(toon_data, model)
    else:
        print("Invalid choice. Running parse only.")
        test_parse_only(toon_data)


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Interactive TOON validator testing tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  cd pydantic
  uv run python tests/test_toon_interactive.py

  # From command line
  uv run python tests/test_toon_interactive.py --input "id: 1\\nname: Alice"

  # From file
  uv run python tests/test_toon_interactive.py --file ../example.toon

  # With model validation
  uv run python tests/test_toon_interactive.py --input "..." --model
        """,
    )
    parser.add_argument(
        "--input", "-i", type=str, help="TOON data as string (use \\n for newlines)"
    )
    parser.add_argument("--file", "-f", type=str, help="Path to TOON file")
    parser.add_argument(
        "--model",
        "-m",
        action="store_true",
        help="Validate with example model (default: parse only)",
    )
    parser.add_argument(
        "--generic",
        "-g",
        action="store_true",
        help="Validate with generic model that allows extra fields",
    )

    args = parser.parse_args()

    # Get TOON data
    toon_data = None

    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"Error: File not found: {args.file}")
            sys.exit(1)
        toon_data = file_path.read_text(encoding="utf-8")
    elif args.input:
        toon_data = args.input.replace("\\n", "\n")
    else:
        # Interactive mode
        interactive_mode()
        return

    if not toon_data:
        print("Error: No TOON data provided.")
        sys.exit(1)

    # Run tests
    if args.model:
        model = create_example_model()
        test_with_model(toon_data, model)
    elif args.generic:
        from pydantic import BaseModel, ConfigDict

        class GenericModel(BaseModel):
            model_config = ConfigDict(extra="allow")

        test_with_model(toon_data, GenericModel)
    else:
        test_parse_only(toon_data)


if __name__ == "__main__":
    main()

