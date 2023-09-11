"""Shared utility functions for docs plugins."""


def generate_table_row(col_values: list[str]) -> str:
    return f'| {" | ".join(col_values)} |\n'


def generate_table_heading(col_names: list[str]) -> str:
    return generate_table_row(col_names) + generate_table_row(['-'] * len(col_names))
