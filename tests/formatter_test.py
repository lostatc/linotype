"""Test 'formatter.py'.

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

from linotype import HelpFormatter, HelpItem


class TestHelpItem:
    @pytest.fixture
    def formatter(self):
        """Return a new HelpFormatter object.

        These values are explicitly passed in so that the defaults can be
        changed in the future without breaking the tests.
        """
        formatter = HelpFormatter(
            indent_increment=4, width=79, auto_markup=False, visible=True,
            inline_space=2, strong=("**", "**"), em=("*", "*"))
        return formatter

    def test_text_formatting(self, formatter):
        """Text items format properly."""
        help_root = HelpItem(formatter)
        help_root.add_text(
            "This is a long string of text that must be wrapped properly. No "
            "markup is applied, and the whole thing is indented to the same "
            "level.")
        expected_output = textwrap.dedent("""\
            This is a long string of text that must be wrapped properly. No markup is
            applied, and the whole thing is indented to the same level.""")
            
        assert help_root.format_help() == expected_output

    def test_definition_heading_formatting(self, formatter):
        """The 'heading' style of definition items format properly."""
        help_root = HelpItem(formatter)
        help_root.add_definition(
            "diff", "[options] number1..number2 [files]",
            "Compare the snapshots number1 and number2.", style="heading")
        expected_output = textwrap.dedent("""\
            diff [options] number1..number2 [files]
                Compare the snapshots number1 and number2.""")

        assert help_root.format_help() == expected_output

    def test_definition_inline_formatting(self, formatter):
        """The 'inline' style of definition items format properly."""
        help_root = HelpItem(formatter)
        help_root.add_definition(
            "diff", "[options] number1..number2 [files]",
            "Compare the snapshots number1 and number2.", style="inline")
        expected_output = textwrap.dedent("""\
            diff [options] number1..number2 [files]  Compare the snapshots number1 and
                number2.""")

        assert help_root.format_help() == expected_output

    def test_definition_heading_aligned_formatting(self, formatter):
        """The 'heading_aligned' style of definition items format properly."""
        help_root = HelpItem(formatter)
        help_root.add_definition(
            "diff", "[options] number1..number2 [files]",
            "Compare the snapshots number1 and number2.",
            style="heading_aligned")
        help_root.add_definition(
            "modify", "[options] number",
            "Modify a snapshot.", style="inline_aligned")
        expected_output = textwrap.dedent("""\
            diff [options] number1..number2 [files]
                                     Compare the snapshots number1 and number2.
            modify [options] number  Modify a snapshot.""")

        assert help_root.format_help() == expected_output

    def test_definition_inline_aligned_formatting(self, formatter):
        """The 'inline_aligned' style of definition items format properly."""
        help_root = HelpItem(formatter)
        help_root.add_definition(
            "diff", "[options] number1..number2 [files]",
            "Compare the snapshots number1 and number2.",
            style="inline_aligned")
        help_root.add_definition(
            "modify", "[options] number",
            "Modify a snapshot.", style="inline_aligned")
        expected_output = textwrap.dedent("""\
            diff [options] number1..number2 [files]  Compare the snapshots number1 and
                                                         number2.
            modify [options] number                  Modify a snapshot.""")

        assert help_root.format_help() == expected_output

    def test_definition_auto_markup(self, formatter):
        """Markup is automatically applied to definitions."""
        formatter.auto_markup = True
        help_root = HelpItem(formatter)
        help_root.add_definition(
            "diff", "[options] number1..number2 [files]",
            "Compare the snapshots number1 and number2.", style="heading")
        expected_output = textwrap.dedent("""\
            **diff** [*options*] *number1*..*number2* [*files*]
                Compare the snapshots *number1* and *number2*.""")

        assert help_root.format_help() == expected_output

    def test_nested_items_indent(self, formatter):
        """Nested items increase the indentation level."""
        help_root = HelpItem(formatter)
        first_level = help_root.add_text("This is the first level of text.")
        second_level = first_level.add_text("This is the second level of text.")
        second_level.add_text("This is the third level of text.")
        help_root.add_text("This is the first level of text.")
        expected_output = textwrap.dedent("""\
            This is the first level of text.
                This is the second level of text.
                    This is the third level of text.
            This is the first level of text.""")

        assert help_root.format_help() == expected_output

    def test_nested_items_limit(self, formatter):
        """The number of levels of nested items to display can be limited."""
        help_root = HelpItem(formatter)
        first_level = help_root.add_text("This is the first level of text.")
        first_level.add_text("This is the second level of text.")
        expected_output = "This is the first level of text."

        assert help_root.format_help(levels=1) == expected_output

    def test_change_indent_increment(self, formatter):
        """Changes to the indentation are reflected in the output."""
        formatter.indent_increment = 2
        help_root = HelpItem(formatter)
        first_level = help_root.add_text("This is the first level of text.")
        first_level.add_text("This is the second level of text.")
        expected_output = textwrap.dedent("""\
            This is the first level of text.
              This is the second level of text.""")

        assert help_root.format_help() == expected_output

    def test_change_width(self, formatter):
        """Changes to the text width are reflected in the output."""
        formatter.width = 99
        help_root = HelpItem(formatter)
        help_root.add_text(
            "This is a long string of text that must be wrapped properly. No "
            "markup is applied, and the whole thing is indented to the same "
            "level.")
        expected_output = textwrap.dedent("""\
            This is a long string of text that must be wrapped properly. No markup is applied, and the whole
            thing is indented to the same level.""")

        assert help_root.format_help() == expected_output

    def test_change_visible(self, formatter):
        """Items with the 'visible' flag set to 'False' don't appear."""
        formatter.visible = False
        help_root = HelpItem(formatter)
        help_root.add_text("This text is invisible.")

        assert help_root.format_help() == ""

    def test_change_inline_space(self, formatter):
        """Changes to the inline spacing are reflected in the output."""
        formatter.inline_space = 4
        help_root = HelpItem(formatter)
        help_root.add_definition(
            "diff", "[options] number1..number2 [files]",
            "Compare the snapshots number1 and number2.", style="inline")
        expected_output = textwrap.dedent("""\
            diff [options] number1..number2 [files]    Compare the snapshots number1 and
                number2.""")

        assert help_root.format_help() == expected_output

    def test_duplicate_ids(self, formatter):
        """Adding items with duplicate item IDs raises an exception."""
        help_root = HelpItem(formatter)
        help_root.add_text("foo", item_id="duplicate")
        with pytest.raises(ValueError):
            help_root.add_text("bar", item_id="duplicate")
