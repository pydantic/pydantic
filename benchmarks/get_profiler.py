"""
At first I tried to put this function inside profile_lines.py, but I ran into very strange issues
where the line_profiler would be recreated if imported in pydantic files (I'm still not sure why).

"""
from functools import lru_cache

from line_profiler import LineProfiler


@lru_cache()  # ensures the same instance is always returned
def get_line_profiler():
    return LineProfiler()
