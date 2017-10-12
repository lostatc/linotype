"""Format terminal output.

Copyright © 2017 Garrett Powell <garrett@gpowell.net>

This file is part of linotype.

linotype is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

linotype is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with linotype.  If not, see <http://www.gnu.org/licenses/>.
"""
import re
from typing import Tuple, Union, Iterable

ANSI_COLORS = [
    "black", "red", "green", "yellow", "blue", "magenta", "cyan", "white"]


def _ansi_join(*args):
    """Convert values to strings and join with semicolons."""
    return ";".join(str(value) for value in args)


def _get_color_code(spec: Union[str, int], base: int):
    """Get the appropriate ansi color code based on input.

    Args:
        spec: The color specification to be parsed.
        base: The base value for color encoding.

    Raises:
        ValueError: The given color spec was unrecognized.

    Returns:
        The ANSI color code.
    """
    spec = str(spec).strip().lower()
    hex_match = re.search(r"^#?([0-9a-f]{6})$", spec)

    if spec in ANSI_COLORS:
        return _ansi_join(base + ANSI_COLORS.index(spec))
    elif hex_match:
        hex_code = hex_match.group(1)
        rgb = tuple(
            int(hex_code[digit:digit + 2], 16) for digit in range(0, 6, 2))
        return _ansi_join(base + 8, 2, _ansi_join(*rgb))
    elif 0 <= int(spec) <= 255:
        return _ansi_join(base + 8, 5, spec)
    else:
        raise ValueError("unrecognized color spec '{0}'".format(str(spec)))


def ansi_format(
        fg=None, bg=None, bold=False, underline=False) -> Tuple[str, str]:
    """Get the appropriate ANSI escape sequences based on input.

    Not all features are supported on all terminals.

    Args:
        fg: The foreground color specification. This can be the name of one of
            the eight ANSI colors, an integer in the range 0-255 or a CSS-style
            hex value. 'None' means no formatting.
        bg: The background color specification. This can be the name of one of
            the eight ANSI colors, an integer in the range 0-255 or a CSS-style
            hex value. 'None' means no formatting.
        bold: Make the text bold.
        underline: Make the text underlined.

    Raises:
        ValueError: The given color spec was unrecognized.

    Returns:
        A tuple containing the starting and ending ANSI escape sequences.
    """
    start_codes = []
    if fg:
        start_codes.append(_get_color_code(fg, 30))
    if bg:
        start_codes.append(_get_color_code(bg, 40))
    if bold:
        start_codes.append(1)
    if underline:
        start_codes.append(4)

    return "\x1b[{0}m".format(_ansi_join(*start_codes)), "\x1b[0m"
