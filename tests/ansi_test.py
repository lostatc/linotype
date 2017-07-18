"""Test 'ansi.py'.

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
from linotype.ansi import ansi_format


def test_foreground_color():
    """Setting the foreground color results in correct output."""
    assert ansi_format("white", None, None) == ("\x1b[37m", "\x1b[0m")


def test_background_color():
    """Setting the background color results in correct output."""
    assert ansi_format(None, "white", None) == ("\x1b[47m", "\x1b[0m")


def test_style():
    """Setting the style results in correct output."""
    assert ansi_format(None, None, "bold") == ("\x1b[1m", "\x1b[0m")


def test_256_color():
    """Setting a 256-bit color value results in correct output."""
    assert ansi_format(128, None, None) == ("\x1b[38;5;128m", "\x1b[0m")


def test_hex_color():
    """Setting a hex color value results in correct output."""
    assert ansi_format(
        "#ade0e0", None, None) == ('\x1b[38;2;173;224;224m', '\x1b[0m')


def test_multiple_styles():
    """Using multiple styles results in correct output."""
    assert ansi_format(
        None, None, ["bold", "underline"]) == ("\x1b[1;4m", "\x1b[0m")