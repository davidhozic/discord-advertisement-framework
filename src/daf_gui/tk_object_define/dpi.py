"""
Module contains definitions for automatic scaling over different DPI displays.
"""
DPI_ORIGINAL = 96


class GLOBALS:
    current_dpi = 96


__all__ = (
    "dpi_scaled",
    "set_dpi"
)


def dpi_scaled(px: int) -> int:
    return int(px * GLOBALS.current_dpi / DPI_ORIGINAL)


def set_dpi(new_dpi: int):
    GLOBALS.current_dpi = new_dpi
