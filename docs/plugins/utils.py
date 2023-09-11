"""Shared utility functions for docs plugins."""
from typing import List


def generate_table_row(col_values: List[str]) -> str:
    return f'| {" | ".join(col_values)} |\n'


def generate_table_heading(col_names: List[str]) -> str:
    return generate_table_row(col_names) + generate_table_row(['-'] * len(col_names))
