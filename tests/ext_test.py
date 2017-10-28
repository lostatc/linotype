"""Test 'ext.py'.

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
from docutils.frontend import OptionParser
from docutils.parsers.rst import Parser
from docutils.parsers.rst import directives
from docutils.utils import new_document

from linotype.ext import LinotypeDirective
from linotype import Item


def get_test_item():
    root_item = Item()

    text_item = root_item.add_text(
        "This is the *parent* text item.", item_id="parent_text")
    text_item.add_text("This is the child text item.", item_id="child_text")
    root_item.add_def(
        "ls", "[options] files...", "List information about files.",
        item_id="definition")

    return root_item


def get_simple_test_item():
    root_item = Item()
    root_item.add_text("This is the *parent* text item.", item_id="text")
    return root_item


def parse_rst(text: str) -> str:
    """Parse reStructuredText into a tree of nodes."""
    directives.register_directive("linotype", LinotypeDirective)

    option_parser = OptionParser(components=(Parser,))
    settings = option_parser.get_default_values()
    parser = Parser()
    document = new_document("test", settings)
    parser.parse(text, document)
    return document.pformat()


def test_option_module():
    """The :module: option imports the function from the specified module."""
    rst = textwrap.dedent("""\
        .. linotype::
            :module: tests.ext_test
            :function: get_test_item
        """)

    expected = textwrap.dedent("""\
        <document source="test">
            <paragraph>
                This is the 
                <emphasis>
                    parent
                 text item.
            <definition_list>
                <definition_list_item>
                    <term>
                    <definition>
                        <paragraph>
                            This is the child text item.
                <definition_list_item>
                    <term>
                        <strong>
                            ls

                        [
                        <emphasis>
                            options
                        ] 
                        <emphasis>
                            files
                        ...
                    <definition>
                        <paragraph>
                            List information about 
                            <emphasis>
                                files
                            .
        """)

    # This is here because textwrap.dedent() removes whitespace from lines
    # containing only whitespace, and the whitespace in the output needs to
    # match the whitespace in the expected output.
    output = textwrap.dedent(parse_rst(rst))

    assert output == expected


def test_option_filepath():
    """The :filepath: option imports the function from the specified file."""
    rst = textwrap.dedent("""\
        .. linotype::
            :filepath: {0}
            :function: get_test_item
        """.format(__file__))

    expected = textwrap.dedent("""\
        <document source="test">
            <paragraph>
                This is the 
                <emphasis>
                    parent
                 text item.
            <definition_list>
                <definition_list_item>
                    <term>
                    <definition>
                        <paragraph>
                            This is the child text item.
                <definition_list_item>
                    <term>
                        <strong>
                            ls

                        [
                        <emphasis>
                            options
                        ] 
                        <emphasis>
                            files
                        ...
                    <definition>
                        <paragraph>
                            List information about 
                            <emphasis>
                                files
                            .
        """)

    output = textwrap.dedent(parse_rst(rst))

    assert output == expected


def test_option_item_id():
    """The :item_id: option limits the output to the selected item."""
    rst = textwrap.dedent("""\
        .. linotype::
            :module: tests.ext_test
            :function: get_test_item
            :item_id: parent_text
        """)

    expected = textwrap.dedent("""\
        <document source="test">
            <paragraph>
                This is the 
                <emphasis>
                    parent
                 text item.
            <definition_list>
                <definition_list_item>
                    <term>
                    <definition>
                        <paragraph>
                            This is the child text item.
        """)

    # This is here because textwrap.dedent() removes whitespace from lines
    # containing only whitespace, and the output needs to match the expected
    # output exactly.
    output = textwrap.dedent(parse_rst(rst))

    assert output == expected


def test_option_children():
    """The :children: option shows hides the item."""
    rst = textwrap.dedent("""\
        .. linotype::
            :module: tests.ext_test
            :function: get_test_item
            :item_id: parent_text
            :children:
        """)

    expected = textwrap.dedent("""\
        <document source="test">
            <paragraph>
                This is the child text item.
        """)

    output = textwrap.dedent(parse_rst(rst))

    assert output == expected


def test_option_children_without_item_id():
    """The :children: options does nothing without the :item_id: option."""
    rst = textwrap.dedent("""\
        .. linotype::
            :module: tests.ext_test
            :function: get_test_item
            :children:
        """)

    expected = textwrap.dedent("""\
        <document source="test">
            <paragraph>
                This is the 
                <emphasis>
                    parent
                 text item.
            <definition_list>
                <definition_list_item>
                    <term>
                    <definition>
                        <paragraph>
                            This is the child text item.
                <definition_list_item>
                    <term>
                        <strong>
                            ls

                        [
                        <emphasis>
                            options
                        ] 
                        <emphasis>
                            files
                        ...
                    <definition>
                        <paragraph>
                            List information about 
                            <emphasis>
                                files
                            .
        """)

    output = textwrap.dedent(parse_rst(rst))

    assert output == expected


def test_option_no_auto_markup():
    """The :no_auto_markup: option disables automatic markup."""
    rst = textwrap.dedent("""\
        .. linotype::
            :module: tests.ext_test
            :function: get_test_item
            :no_auto_markup:
        """)

    expected = textwrap.dedent("""\
        <document source="test">
            <paragraph>
                This is the 
                <emphasis>
                    parent
                 text item.
            <definition_list>
                <definition_list_item>
                    <term>
                    <definition>
                        <paragraph>
                            This is the child text item.
                <definition_list_item>
                    <term>
                        ls
                        
                        [options] files...
                    <definition>
                        <paragraph>
                            List information about files.
        """)

    output = textwrap.dedent(parse_rst(rst))

    assert output == expected


def test_option_no_manual_markup():
    """The :no_manual_markup: option disables manual markup."""
    rst = textwrap.dedent("""\
        .. linotype::
            :module: tests.ext_test
            :function: get_test_item
            :no_manual_markup:
        """)

    expected = textwrap.dedent("""\
        <document source="test">
            <paragraph>
                This is the *parent* text item.
            <definition_list>
                <definition_list_item>
                    <term>
                    <definition>
                        <paragraph>
                            This is the child text item.
                <definition_list_item>
                    <term>
                        <strong>
                            ls

                        [
                        <emphasis>
                            options
                        ] 
                        <emphasis>
                            files
                        ...
                    <definition>
                        <paragraph>
                            List information about 
                            <emphasis>
                                files
                            .
        """)

    output = textwrap.dedent(parse_rst(rst))

    assert output == expected


def test_extend_text_item():
    """The content of a text item can be extended."""
    rst = textwrap.dedent("""\
        .. linotype::
            :module: tests.ext_test
            :function: get_test_item
            
            parent_text
                This comes after the existing content.
        """)

    expected = textwrap.dedent("""\
        <document source="test">
            <paragraph>
                This is the 
                <emphasis>
                    parent
                 text item. This comes after the existing content.
            <definition_list>
                <definition_list_item>
                    <term>
                    <definition>
                        <paragraph>
                            This is the child text item.
                <definition_list_item>
                    <term>
                        <strong>
                            ls

                        [
                        <emphasis>
                            options
                        ] 
                        <emphasis>
                            files
                        ...
                    <definition>
                        <paragraph>
                            List information about 
                            <emphasis>
                                files
                            .
        """)

    output = textwrap.dedent(parse_rst(rst))

    assert output == expected


def test_extend_definition_item():
    """The content of a definition item can be extended."""
    rst = textwrap.dedent("""\
        .. linotype::
            :module: tests.ext_test
            :function: get_test_item
            
            definition
                This comes after the existing content.
        """)

    expected = textwrap.dedent("""\
        <document source="test">
            <paragraph>
                This is the 
                <emphasis>
                    parent
                 text item.
            <definition_list>
                <definition_list_item>
                    <term>
                    <definition>
                        <paragraph>
                            This is the child text item.
                <definition_list_item>
                    <term>
                        <strong>
                            ls

                        [
                        <emphasis>
                            options
                        ] 
                        <emphasis>
                            files
                        ...
                    <definition>
                        <paragraph>
                            List information about 
                            <emphasis>
                                files
                            . This comes after the existing content.
        """)

    output = textwrap.dedent(parse_rst(rst))

    assert output == expected


def test_extend_auto_with_markup():
    """Manual markup can be used to extend the content."""
    rst = textwrap.dedent("""\
        .. linotype::
            :module: tests.ext_test
            :function: get_simple_test_item
            
            text
                This comes **after** the existing content.
        """)

    expected = textwrap.dedent("""\
        <document source="test">
            <paragraph>
                This is the 
                <emphasis>
                    parent
                 text item. This comes 
                <strong>
                    after
                 the existing content.
        """)

    output = textwrap.dedent(parse_rst(rst))

    assert output == expected


def test_extend_auto_with_unsupported_markup():
    """Unsupported inline markup is ignored."""
    rst = textwrap.dedent("""\
        .. linotype::
            :module: tests.ext_test
            :function: get_simple_test_item
            
            text
                This doesn't allow for ``inline literals``. This comes 
                **after** the existing content.
        """)

    expected = textwrap.dedent("""\
        <document source="test">
            <paragraph>
                This is the 
                <emphasis>
                    parent
                 text item. This doesn't allow for ``inline literals``. This comes
                <strong>
                    after
                 the existing content.
        """)

    output = textwrap.dedent(parse_rst(rst))

    assert output == expected


def test_extend_auto_unclosed_markup():
    """Opening inline markup that isn't closed is ignored."""
    rst = textwrap.dedent("""\
        .. linotype::
            :module: tests.ext_test
            :function: get_simple_test_item
            
            text
                This comes **after** the *existing content.
        """)

    expected = textwrap.dedent("""\
        <document source="test">
            <paragraph>
                This is the 
                <emphasis>
                    parent
                 text item. This comes 
                <strong>
                    after
                 the *existing content. 
        """)

    output = textwrap.dedent(parse_rst(rst))

    assert output == expected


def test_extend_auto_before():
    """The @before classifier makes new content appear first."""
    rst = textwrap.dedent("""\
        .. linotype::
            :module: tests.ext_test
            :function: get_simple_test_item
            
            text : @before
                This comes before the existing content.
        """)

    expected = textwrap.dedent("""\
        <document source="test">
            <paragraph>
                This comes before the existing content. This is the 
                <emphasis>
                    parent
                 text item.
        """)

    output = textwrap.dedent(parse_rst(rst))

    assert output == expected


def test_extend_auto_replace():
    """The @replace classifier replaces existing content."""
    rst = textwrap.dedent("""\
        .. linotype::
            :module: tests.ext_test
            :function: get_simple_test_item
            
            text : @replace
                This replaces the existing content.
        """)

    expected = textwrap.dedent("""\
        <document source="test">
            <paragraph>
                This replaces the existing content.
        """)

    output = textwrap.dedent(parse_rst(rst))

    assert output == expected


def test_extend_rst():
    """The @rst classifier allows for reStructuredText markup."""
    rst = textwrap.dedent("""\
        .. linotype::
            :module: tests.ext_test
            :function: get_simple_test_item
            
            text : @rst
                This allows for ``inline literals``.
        """)

    expected = textwrap.dedent("""\
        <document source="test">
            <paragraph>
                This is the 
                <emphasis>
                    parent
                 text item.
            <paragraph>
                This allows for 
                <literal>
                    inline literals
                .
        """)

    output = textwrap.dedent(parse_rst(rst))

    assert output == expected


def test_extend_rst_before():
    """The @before classifier works with the @rst classifier."""
    rst = textwrap.dedent("""\
        .. linotype::
            :module: tests.ext_test
            :function: get_simple_test_item
            
            text : @rst : @before
                This allows for ``inline literals``.
        """)

    expected = textwrap.dedent("""\
        <document source="test">
            <paragraph>
                This allows for 
                <literal>
                    inline literals
                .
            <paragraph>
                This is the 
                <emphasis>
                    parent
                 text item.
        """)

    output = textwrap.dedent(parse_rst(rst))

    assert output == expected


def test_extend_rst_replace():
    """The @replace classifier works with the @rst classifier."""
    rst = textwrap.dedent("""\
        .. linotype::
            :module: tests.ext_test
            :function: get_simple_test_item
            
            text : @rst : @replace
                This allows for ``inline literals``.
        """)

    expected = textwrap.dedent("""\
        <document source="test">
            <paragraph>
                This allows for 
                <literal>
                    inline literals
                .
        """)

    output = textwrap.dedent(parse_rst(rst))

    assert output == expected


def test_extend_multiple():
    """The same item can be extended multiple times."""
    rst = textwrap.dedent("""\
        .. linotype::
            :module: tests.ext_test
            :function: get_simple_test_item
            
            text
                This comes **after** the existing content.
                
            text : @rst : @before
                This allows for ``inline literals``.
        """)

    expected = textwrap.dedent("""\
        <document source="test">
            <paragraph>
                This allows for 
                <literal>
                    inline literals
                .
            <paragraph>
                This is the 
                <emphasis>
                    parent
                 text item. This comes 
                <strong>
                    after
                 the existing content.
        """)

    output = textwrap.dedent(parse_rst(rst))

    assert output == expected
