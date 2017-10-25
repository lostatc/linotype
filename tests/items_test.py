"""Test 'items.py'.

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
import textwrap

import pytest

from linotype import DefinitionStyle, Formatter, Item, ansi_format


@pytest.fixture
def formatter():
    """Return a new Formatter object.

    These values are explicitly passed in so that the defaults can be
    changed in the future without breaking the tests.
    """
    formatter_instance = Formatter(
        max_width=79, auto_width=False, indent_spaces=4, definition_gap=2,
        definition_style=DefinitionStyle.BLOCK, auto_markup=False,
        manual_markup=False, visible=True, strong=ansi_format(bold=True),
        em=ansi_format(underline=True))
    return formatter_instance


def test_text_formatting(formatter):
    """Text items format properly."""
    root_item = Item(formatter)
    root_item.add_text(
        "This is a long string of text that must be wrapped properly. No "
        "markup is applied, and the whole thing is indented to the same "
        "level.")
    expected_output = textwrap.dedent("""\
        This is a long string of text that must be wrapped properly. No markup is
        applied, and the whole thing is indented to the same level.""")

    assert root_item.format() == expected_output


def test_text_manual_markup(formatter):
    """Manual markup can be applied to text items."""
    formatter.manual_markup = True
    root_item = Item(formatter)
    root_item.add_text("This text has *emphasized* and **strong** markup.")
    expected_output = textwrap.dedent("""\
        This text has \x1b[4memphasized\x1b[0m and \x1b[1mstrong\x1b[0m markup.""")

    assert root_item.format() == expected_output


def test_text_manual_markup_across_line_breaks(formatter):
    """Manual markup that spans line breaks in the output is applied."""
    formatter.manual_markup = True
    root_item = Item(formatter)
    root_item.add_text(
        "This text string is so long that it can span multiple lines, which "
        "*may interrupt* the parsing of manual markup.")
    expected_output = textwrap.dedent("""\
        This text string is so long that it can span multiple lines, which \x1b[4mmay
        interrupt\x1b[0m the parsing of manual markup.""")
    assert root_item.format() == expected_output


def test_definition_block_formatting(formatter):
    """The BLOCK style of definition items format properly."""
    formatter.definition_style = DefinitionStyle.BLOCK
    root_item = Item(formatter)
    root_item.add_definition(
        "diff", "[options] number1..number2 [files]",
        "Compare the snapshots number1 and number2.")
    expected_output = textwrap.dedent("""\
        diff [options] number1..number2 [files]
            Compare the snapshots number1 and number2.""")

    assert root_item.format() == expected_output


def test_definition_inline_formatting(formatter):
    """The INLINE style of definition items format properly."""
    formatter.definition_style = DefinitionStyle.INLINE
    root_item = Item(formatter)
    root_item.add_definition(
        "diff", "[options] number1..number2 [files]",
        "Compare the snapshots number1 and number2.")
    expected_output = textwrap.dedent("""\
        diff [options] number1..number2 [files]  Compare the snapshots number1 and
            number2.""")

    assert root_item.format() == expected_output


def test_definition_overflow_formatting(formatter):
    """The OVERFLOW style of definition items format properly."""
    formatter.definition_style = DefinitionStyle.OVERFLOW
    root_item = Item(formatter)
    root_item.add_definition(
        "diff", "[options] number1..number2 [files]",
        "Compare the snapshots number1 and number2.")
    root_item.formatter.definition_style = DefinitionStyle.ALIGNED
    root_item.add_definition(
        "modify", "[options] number",
        "Modify a snapshot.")
    expected_output = textwrap.dedent("""\
        diff [options] number1..number2 [files]
                                 Compare the snapshots number1 and number2.
        modify [options] number  Modify a snapshot.""")

    assert root_item.format() == expected_output


def test_definition_aligned_formatting(formatter):
    """The ALIGNED style of definition items format properly."""
    formatter.definition_style = DefinitionStyle.ALIGNED
    root_item = Item(formatter)
    root_item.add_definition(
        "diff", "[options] number1..number2 [files]",
        "Compare the snapshots number1 and number2.")
    root_item.add_definition(
        "modify", "[options] number",
        "Modify a snapshot.")
    expected_output = textwrap.dedent("""\
        diff [options] number1..number2 [files]  Compare the snapshots number1 and
                                                     number2.
        modify [options] number                  Modify a snapshot.""")

    assert root_item.format() == expected_output


def test_definition_auto_markup(formatter):
    """Markup is automatically applied to definitions."""
    formatter.auto_markup = True
    root_item = Item(formatter)
    root_item.add_definition(
        "diff", "[options] number1..number2",
        "Compare the snapshots number1 and number2.")
    expected_output = textwrap.dedent("""\
        \x1b[1mdiff\x1b[0m [\x1b[4moptions\x1b[0m] \x1b[4mnumber1\x1b[0m..\x1b[4mnumber2\x1b[0m
            Compare the snapshots \x1b[4mnumber1\x1b[0m and \x1b[4mnumber2\x1b[0m.""")

    assert root_item.format() == expected_output


def test_definition_manual_markup(formatter):
    """Manual markup can be applied to definition items."""
    formatter.manual_markup = True
    root_item = Item(formatter)
    root_item.add_definition(
        "**--file**", "*FILE*", "Obtain patterns from *FILE*, one per line.")
    expected_output = textwrap.dedent("""\
        \x1b[1m--file\x1b[0m \x1b[4mFILE\x1b[0m
            Obtain patterns from \x1b[4mFILE\x1b[0m, one per line.""")

    assert root_item.format() == expected_output


def test_definition_nested_markup(formatter):
    """Auto markup nested in manual markup is applied properly."""
    formatter.auto_markup = True
    formatter.manual_markup = True
    root_item = Item(formatter)
    root_item.add_definition(
        "--file", "FILE", "Obtain patterns from **FILE, one per** line.")
    expected_output = textwrap.dedent("""\
        \x1b[1m--file\x1b[0m \x1b[4mFILE\x1b[0m
            Obtain patterns from \x1b[1m\x1b[4mFILE\x1b[0m\x1b[1m, one per\x1b[0m line.""")

    assert root_item.format() == expected_output


def test_definition_change_style_retroactively(formatter):
    root_item = Item(formatter)
    option = root_item.add_definition(
        "diff", "[options] number1..number2 [files]",
        "Compare the snapshots number1 and number2.")
    option.formatter.definition_style = DefinitionStyle.INLINE
    expected_output = textwrap.dedent("""\
        diff [options] number1..number2 [files]  Compare the snapshots number1 and
            number2.""")

    assert root_item.format() == expected_output


def test_nested_items_indent(formatter):
    """Nested items increase the indentation level."""
    root_item = Item(formatter)
    first_level = root_item.add_text("This is the first level of text.")
    second_level = first_level.add_text("This is the second level of text.")
    second_level.add_text("This is the third level of text.")
    root_item.add_text("This is the first level of text.")
    expected_output = textwrap.dedent("""\
        This is the first level of text.
            This is the second level of text.
                This is the third level of text.
        This is the first level of text.""")

    assert root_item.format() == expected_output


def test_nested_items_limit(formatter):
    """The number of levels of nested items to display can be limited."""
    root_item = Item(formatter)
    first_level = root_item.add_text("This is the first level of text.")
    first_level.add_text("This is the second level of text.")
    expected_output = "This is the first level of text."

    assert root_item.format(levels=1) == expected_output


def test_change_indent_spaces(formatter):
    """Changes to the indentation are reflected in the output."""
    formatter.indent_spaces = 2
    root_item = Item(formatter)
    first_level = root_item.add_text("This is the first level of text.")
    first_level.add_text("This is the second level of text.")
    expected_output = textwrap.dedent("""\
        This is the first level of text.
          This is the second level of text.""")

    assert root_item.format() == expected_output


def test_change_width(formatter):
    """Changes to the width are reflected in the output."""
    formatter.max_width = 99
    root_item = Item(formatter)
    root_item.add_text(
        "This is a long string of text that must be wrapped properly. No "
        "markup is applied, and the whole thing is indented to the same "
        "level.")
    expected_output = textwrap.dedent("""\
        This is a long string of text that must be wrapped properly. No markup is applied, and the whole
        thing is indented to the same level.""")

    assert root_item.format() == expected_output


def test_definition_inline_wrapping(formatter):
    """Definition items with the INLINE style wrap properly."""
    formatter.max_width = 48
    formatter.definition_style = DefinitionStyle.INLINE
    root_item = Item(formatter)
    root_item.add_definition(
        "diff", "[options] number1..number2 [files]",
        "Compare the snapshots number1 and number2. This text ensures that "
        "subsequent lines are wrapped properly.")
    expected_output = textwrap.dedent("""\
        diff [options] number1..number2 [files]  Compare
            the snapshots number1 and number2. This text
            ensures that subsequent lines are wrapped
            properly.""")

    assert root_item.format() == expected_output


def test_definition_aligned_wrapping(formatter):
    """Definition items with the ALIGNED style wrap properly."""
    formatter.max_width = 49
    formatter.definition_style = DefinitionStyle.ALIGNED
    root_item = Item(formatter)
    root_item.add_definition(
        "diff", "[options]",
        "Compare the snapshots number1 and number2. This text ensures that "
        "all subsequent lines are wrapped properly.")
    expected_output = textwrap.dedent("""\
        diff [options]  Compare the snapshots number1 and
                            number2. This text ensures
                            that all subsequent lines are
                            wrapped properly.""")

    assert root_item.format() == expected_output


def test_change_visible(formatter):
    """Items with the 'visible' flag set to 'False' don't appear."""
    formatter.visible = False
    root_item = Item(formatter)
    root_item.add_text("This text is invisible.")

    assert root_item.format() == ""


def test_change_definition_gap(formatter):
    """Changes to the definition buffer are reflected in the output."""
    formatter.definition_gap = 4
    formatter.definition_style = DefinitionStyle.INLINE
    root_item = Item(formatter)
    root_item.add_definition(
        "diff", "[options] number1..number2 [files]",
        "Compare the snapshots number1 and number2.")
    expected_output = textwrap.dedent("""\
        diff [options] number1..number2 [files]    Compare the snapshots number1 and
            number2.""")

    assert root_item.format() == expected_output


def test_duplicate_ids(formatter):
    """Adding items with duplicate item IDs raises an exception."""
    root_item = Item(formatter)
    root_item.add_text("foo", item_id="duplicate")
    with pytest.raises(ValueError):
        root_item.add_text("bar", item_id="duplicate")
