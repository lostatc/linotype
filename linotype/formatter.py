"""Format a help message.

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
import textwrap
from typing import Any, Callable, Tuple, Generator


class HelpFormatter:
    """Dynamically format a help message.

    Args:
        indent_increment: The number of spaces to increase/decrease the indent
            level by for each level.
        width: The number of columns at which to wrap text in the help message.
        fancy_output: Apply 'strong' and 'emphasized' formatting to certain
            text in the output.
        strong: the strings to print before and after strong text (default is
            ANSI bold). These are ignored when wrapping text.
        em: The strings to print before and after emphasized text (default is
            ANSI underlined). These are ignored when wrapping text.

    Attributes:
        indent_increment: The number of spaces to increase/decrease the indent
            level by for each level.
        width: The number of columns at which to wrap text in the help message.
        fancy_output: Add additional output formatting with markup.
        strong: the strings to print before and after strong text (default is
            ANSI bold). These are ignored when wrapping text.
        em: The strings to print before and after emphasized text (default is
            ANSI underlined). These are ignored when wrapping text.
    """
    def __init__(
            self, indent_increment=4, width=79, fancy_output=True,
            strong=("\33[1m", "\33[0m"), em=("\33[4m", "\33[0m")) -> None:
        self.indent_increment = indent_increment
        self.width = width
        self.fancy_output = fancy_output
        self.strong = strong
        self.em = em


class HelpItem:
    """Format an item in a help message.

    This class allows for formatting a help message consisting of a tree of
    "items". There are multiple types of items to choose from. Every item
    can contain zero or more other items. A help message can be printed
    starting at any point in the tree, and the output is automatically
    formatted according to input parameters.

    Args:
        formatter: The formatter object for the item tree.

    Attributes:
        _ARG_REGEX: A regex object that denotes an argument from an argument
            string.
        _INLINE_SPACE: The number of spaces between the argument string and
            the message in definitions with the "inline" or "aligned" style.
        _items: A list of HelpItem objects in the help message.
        _content: The content to display in the help message.
        _format_func: The function used to format the current content.
        _current_indent: The current indent level as a number of spaces.
        _parent: The parent item object.
    """
    _ARG_REGEX = re.compile(r"([\w-]+)")
    _INLINE_SPACE = 2

    def __init__(self, formatter: HelpFormatter) -> None:
        self._formatter = formatter
        self._content = None
        self._format_func = None
        self._current_indent = 0
        self._parent = None
        self._items = []

    @classmethod
    def _new_item(
            cls, content: Any, format_func: Callable, starting_indent: int,
            parent: "HelpItem", formatter: HelpFormatter) -> "HelpItem":
        new_item = cls(formatter)
        new_item._items = []
        new_item._content = content
        new_item._format_func = format_func
        new_item._current_indent = starting_indent
        new_item._parent = parent

        return new_item

    # Message building methods
    # ========================

    def add_text(self, text: str, formatter=None) -> "HelpItem":
        """Add a text item to be printed.

        This item displays the given text wrapped to the given width.

        Args;
            text: The text to be printed.
            formatter: A HelpFormatter object for defining the formatting of
                the new item. If 'None', it uses the help formatter of its
                parent item.
        """
        return self._add_item(text, self._format_text, formatter=formatter)

    def add_definition(
            self, name: str, args: str, msg: str, style="heading",
            formatter=None) -> "HelpItem":
        """Add a definition to be printed.

        This item displays a formatted definition in one of two styles.
        Definitions consist of a name, an argument string and a message, any of
        which can be blank.

        Args:
            name: The command, option, etc. to be defined. If fancy output is
                enabled, this is strong in the terminal output.
            args: The list of arguments for the thing being defined as a
                single string. If fancy output is enabled, arguments are
                emphasized in the terminal output.
            msg: A description of the thing being defined, with arguments
                that appear in the argument string emphasized if fancy output
                is enabled.
            style: The style of definition to use.
                "heading": Display the message on a separate line from the name
                    and argument string.
                "inline": Display the message on the same line as the name and
                    argument string with a hanging indent if it is too long.
                "aligned" Display the message on the same line as the name and
                    argument string with a hanging in dent if it is too long.
                    Also align the message with all other definitions of the
                    same style belonging to the same parent item.
            formatter: A HelpFormatter object for defining the formatting of
                the new item. If 'None', it uses the help formatter of its
                parent item.
        """
        if style == "heading":
            format_func = self._format_heading_def
        elif style == "inline":
            format_func = self._format_inline_def
        elif style == "aligned":
            format_func = self._format_aligned_def
        else:
            raise ValueError(
                "unrecognized definition style '{}'".format(style))

        return self._add_item(
            (name, args, msg), format_func, formatter=formatter)

    def _add_item(
            self, content: Any, format_func: Callable, formatter=None
            ) -> "HelpItem":
        """Add a new item under the current item.

        Args:
            content: The content to print.
            format_func: The function used to format the content.
            formatter: A HelpFormatter object for defining the formatting of
                the new item. If 'None', it uses the help formatter of its
                parent item.
        """
        if self._content:
            self._indent()

        if formatter is None:
            formatter = self._formatter

        new_item = self._new_item(
            content, format_func, self._current_indent, self, formatter)
        self._items.append(new_item)

        if self._content:
            self._dedent()

        return new_item

    # Message formatting methods
    # ==========================

    def format_help(self, levels=None) -> str:
        """Join the help messages of each item.

        This method will return the help messages from all items under the
        current item in the tree. Whether or not the current item has
        parents, it will be left-aligned in the output and wrapped
        accordingly.

        Args:
            levels: The number of levels of nested items to descend into.

        Returns:
            The joined help message as a string.
        """
        # Dedent the output so that it's flush with the left edge.
        dedent_amount = self._current_indent
        help_messages = []
        for item in self._get_items(levels=levels):
            item._current_indent -= dedent_amount
            if item._content is not None:
                help_messages.append(item._format_item())

        return "\n".join(help_messages)

    def _format_item(self) -> str:
        """Format the items belonging to this item.

        Returns:
            A formatted help message as a string.
        """
        if self._content:
            # The formatting functions are static methods so that the
            # current item instance can be passed in instead of the parent
            # item instance.
            help_msg = self._format_func(self, self._content)
        else:
            help_msg = ""

        return help_msg

    def _get_items(
            self, item=None, levels=None, counter=0, last_item=None
            ) -> Generator["HelpItem", None, None]:
        """Recursively yield nested items.

        Args:
            item: The item to find descendants of. If 'None', this defaults to
                self.
            levels: The number of levels of nested items to descend into.
            counter: Do not override this attribute. It tracks the recursion
                depth.

        Yields:
            Each item in the tree.
        """
        if item is None:
            item = self

        yield item

        if levels is None or counter < levels:
            for item in item._items:
                yield from self._get_items(
                    item, levels=levels, counter=counter+1)

    def _indent(self) -> None:
        """Increase the indentation level."""
        self._current_indent += self._formatter.indent_increment

    def _dedent(self) -> None:
        """Decrease the indentation level."""
        new_indent = self._current_indent - self._formatter.indent_increment
        if new_indent < 0:
            self._current_indent = 0
        else:
            self._current_indent = new_indent

    def _markup_name(self, text: str) -> str:
        """Make the input string strong.

        Returns:
            The input string with markup for strong text added.
        """
        if self._formatter.fancy_output:
            return self._formatter.strong[0] + text + self._formatter.strong[1]
        else:
            return text

    def _markup_args(self, text: str) -> str:
        """Make argument names in the input string emphasized.

        Returns:
            The input string with markup for emphasized text added.
        """
        if self._formatter.fancy_output:
            return self._ARG_REGEX.sub(
                self._formatter.em[0] + r"\g<1>" + self._formatter.em[1], text)
        else:
            return text

    def _sub_args(self, args: str, text: str) -> str:
        """Search a string for arguments and add fancy formatting.

        This method only formats arguments surrounded by non-word characters.

        Args:
            text: The string to have control codes added.
            args: The argument string to get argument from.

        Returns:
            The given text with control codes added.
        """
        for arg in self._ARG_REGEX.findall(args):
            text = re.sub(
                r"(^|\W){}($|\W)".format(re.escape(arg)),
                r"\g<1>" + self._markup_args(arg) + r"\g<2>",
                text)
        return text

    def _get_wrapper(
            self, add_initial=0, add_subsequent=0, drop_whitespace=True
            ) -> textwrap.TextWrapper:
        """Get a text wrapper for formatting text.

        Args:
            add_initial: A number of spaces to add to the initial indent level.
            add_subsequent: A number of spaces to add to the subsequent indent
                level.
            drop_whitespace: Remove whitespace from the beginning and end of
                every line.

        Returns:
            A TextWrapper instance.
        """
        initial_indent = self._current_indent + add_initial
        subsequent_indent = self._current_indent + add_subsequent

        wrapper = textwrap.TextWrapper(
            width=self._formatter.width,
            drop_whitespace=drop_whitespace,
            initial_indent=" "*initial_indent,
            subsequent_indent=" "*subsequent_indent)

        return wrapper

    @staticmethod
    def _format_text(self, text: str) -> str:
        """Format plain text for the help message.

        This method accepts the instance of the calling item as its first
        argument.

        Args:
            text: The text to be formatted.

        Returns:
            The formatted text as a string.
        """
        wrapper = self._get_wrapper()
        return wrapper.fill(text)

    @staticmethod
    def _format_inline_def(
            self, definition: Tuple[str, str, str], aligned=False) -> str:
        """Format an inline definition for the help message.

        In an inline definition, the message is printed on the same line as
        the name and argument string and with a hanging indent as opposed to
        on a new line.

        This method accepts the instance of the calling item as its first
        argument.

        Args:
            definition: A tuple containing the name, args and message for
                the definition.
            aligned: Vertically align with all other definitions with the style
                "aligned" belonging to the same parent item.

        Returns:
            The formatted definition as a string.
        """
        name, args, msg = definition
        if aligned:
            inline_content = (
                item._content for item in self._parent._items
                if item._format_func == self._format_aligned_def)
            longest = max(
                len(" ".join([string for string in (name, args) if string]))
                for name, args, msg in inline_content)
        else:
            longest = len(
                " ".join([string for string in (name, args) if string]))
        sig_buffer = longest + self._INLINE_SPACE
        name_buffer = len(name)

        # Markup must be added after all text formatting has occurred
        # because the markup strings should be ignored when wrapping the
        # text. To allow the formatting to be applied to each part of the
        # definition separately, spaces are used as filler in certain places
        # so that the text can be wrapped properly before the real text is
        # substituted.
        wrapper = self._get_wrapper(
            add_initial=-self._formatter.indent_increment,
            drop_whitespace=False)
        output_args = "{0:<{1}}".format(
            " "*(name_buffer + 1) + args, sig_buffer)
        output_args = wrapper.fill(output_args)

        wrapper = self._get_wrapper()
        output_name = wrapper.fill(name)
        output_sig = (
            wrapper.initial_indent
            + self._markup_name(output_name[self._current_indent:])
            + self._markup_args(output_args)[name_buffer:])

        subsequent_indent = self._formatter.indent_increment
        if aligned:
            subsequent_indent += sig_buffer
        wrapper = self._get_wrapper(
            add_initial=-self._current_indent,
            add_subsequent=subsequent_indent)
        output_msg = " "*sig_buffer + self._sub_args(args, msg)
        output_msg = wrapper.fill(output_msg)

        return output_sig + output_msg[sig_buffer:]

    @staticmethod
    def _format_aligned_def(self, definition: Tuple[str, str, str]) -> str:
        """Format an aligned definition for the help message.

        In an aligned definition, the message is printed on the same line as
        the name and argument string and with a hanging indent as opposed to
        on a new line. The definition is vertically aligned with all other
        definitions of the same style belonging to the parent item.

        This method accepts the instance of the calling item as its first
        argument.

        Args:
            definition: A tuple containing the name, args and message for
                the definition.

        Returns:
            The formatted definition as a string.
        """
        return self._format_inline_def(self, definition, aligned=True)

    @staticmethod
    def _format_heading_def(self, definition: Tuple[str, str, str]) -> str:
        """Format a heading definition for the help message.

        In a heading definition, the message is printed on a new line as
        opposed to on the same line as the name and args.

        This method accepts the instance of the calling item as its first
        argument.

        Args:
            definition: A tuple containing the name, args and message for
                the definition.

        Returns:
            The formatted definition as a string.
        """
        name, args, msg = definition
        name_buffer = len(name)

        # Markup must be added after all text formatting has occurred
        # because the markup strings should be ignored when wrapping the
        # text. To allow the formatting to be applied to each part of the
        # definition separately, spaces are used as filler in certain places
        # so that the text can be wrapped properly before the real text is
        # substituted.
        wrapper = self._get_wrapper(
            add_initial=-self._formatter.indent_increment)
        output_args = " "*(name_buffer + 1) + args
        output_args = wrapper.fill(output_args)

        wrapper = self._get_wrapper()
        output_name = wrapper.fill(name)
        output_sig = (
            wrapper.initial_indent
            + self._markup_name(output_name[self._current_indent:])
            + self._markup_args(output_args)[name_buffer:])

        if msg:
            self._indent()
            wrapper = self._get_wrapper()
            output_msg = wrapper.fill(msg)
            output_msg = self._sub_args(args, output_msg)
            self._dedent()

            return "\n".join([output_sig, output_msg])
        else:
            return output_sig
