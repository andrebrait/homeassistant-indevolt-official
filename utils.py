"""Utility functions for Indevolt integration."""


def get_device_gen(str) -> int:
    """Return the device generation."""
    if str == "BK1600/BK1600Ultra":
        return 1

    return 2
