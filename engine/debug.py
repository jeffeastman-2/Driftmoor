"""Shared debug flag and helper used across engine modules."""

DEBUG = True  # set True to print LOS/perception/intent diagnostics


def _dbg(*args) -> None:
    if DEBUG:
        print(*args)
