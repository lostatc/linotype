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
import functools
import contextlib
from typing import Any, Callable, Tuple, Generator, Optional, NamedTuple, List

from docutils.frontend import OptionParser
from docutils.parsers.rst import Parser
from docutils.parsers.rst.states import Inliner

ARG_REGEX = re.compile(r"([\w-]+)")

MARKUP_CHARS = NamedTuple(
    "MarkupChars",
    [
        ("strong", Tuple[str, str]),
        ("em", Tuple[str, str])
        ])(("**", "**"), ("*", "*"))

# This keeps track of the positions of marked-up substrings in a string.
# Each tuple contains the substring and the instance of that substring for
# cases where there are more than one in the string.
MarkupPositions = NamedTuple(
    "MarkupPositions",
    [("strong", List[Tuple[str, int]]), ("em", List[Tuple[str, int]])])


class HelpFormatter:
    """Control how terminal output is formatted.

    Args:
        indent_increment: The number of spaces to increase/decrease the indent
            level by for each level.
        inline_space: The number of spaces to leave between the argument string
            and message of each definition when they are on the same line.
        width: The number of columns at which to wrap text in the help message.
        auto_markup: Automatically apply 'strong' and 'emphasized' formatting
            to certain text in the output.
        manual_markup: Parse reST 'strong' and 'emphasis' inline markup.
        visible: Make the text visible in the output.
        strong: The strings to print before and after strong text (default is
            ANSI bold). These are ignored when wrapping text.
        em: The strings to print before and after emphasized text (default is
            ANSI underlined). These are ignored when wrapping text.

    Attributes:
        indent_increment: The number of spaces to increase/decrease the indent
            level by for each level.
        inline_space: The number of spaces to leave between the argument string
            and message of each definition when they are on the same line.
        width: The number of columns at which to wrap text in the help message.
        auto_markup: Automatically apply 'strong' and 'emphasized' formatting
            to certain text in the output.
        manual_markup: Parse reST 'strong' and 'emphasis' inline markup.
        visible: Make the text visible in the output.
        strong: the strings to print before and after strong text (default is
            ANSI bold). These are ignored when wrapping text.
        em: The strings to print before and after emphasized text (default is
            ANSI underlined). These are ignored when wrapping text.
    """
    def __init__(
            self, indent_increment=4, inline_space=2, width=79,
            auto_markup=True, manual_markup=True, visible=True,
            strong=("\33[1m", "\33[0m"), em=("\33[4m", "\33[0m")) -> None:
        self.indent_increment = indent_increment
        self.inline_space = inline_space
        self.width = width
        self.auto_markup = auto_markup
        self.manual_markup = manual_markup
        self.visible = visible
        self.strong = strong
        self.em = em


class HelpItem:
    """Format an item in a help message.

    This class allows for formatting a help message consisting of a tree of
    "items". There are multiple types of items to choose from, and every
    item can contain zero or more other items. Each level of nested items
    increases the indentation level, and items at the same level are
    displayed at the order in which they were created. A help message can be
    printed starting at any point in the tree, and the output is
    automatically formatted according to the formatter object passed in.
    Formatter objects can be passed in whenever a new item is created to
    affect its formatting.

    New child items can be created using one of the available public
    methods, and new child items can be added using the '+=' operator.

    Args:
        formatter: The formatter object for the item tree.

    Attributes:
        type: The type of the current item.
        content: The content to display in the help message.
        id: The item ID.
        current_level: The current indentation level.
        _format_func: The function used to format the current content.
        _parent: The parent item object.
        _current_indent: The number of spaces that the item is currently
            indented.
        _formatter: The formatter object for the item tree.
        _children: A list of HelpItem objects in the help message.
    """
    def __init__(self, formatter: HelpFormatter) -> None:
        self.type = None
        self.content = None
        self.id = None
        self._format_func = None
        self._parent = None
        self._current_indent = 0
        self._formatter = formatter
        self._children = []

    @classmethod
    def _new_item(
            cls, item_type: str, content: Any, item_id: Optional[str],
            format_func: Callable, parent: "HelpItem", starting_indent: int,
            formatter: HelpFormatter) -> "HelpItem":
        """Construct a new item."""
        new_item = cls(formatter)
        new_item.type = item_type
        new_item.content = content
        new_item.id = item_id
        new_item._format_func = format_func
        new_item._parent = parent
        new_item._current_indent = starting_indent

        return new_item

    def __iadd__(self, other: "HelpItem") -> "HelpItem":
        """Add another HelpItem object to the list of items.

        Args:
            other: The HelpItem object to add.

        Raises:
            TypeError: The input was an unsupported type.
        """
        if isinstance(other, type(self)):
            for item in other.get_items():
                item._current_indent += self._formatter.indent_increment
            if other.type is None:
                for item in other._children:
                    # Exclude the empty root-level item so that formatting only
                    # to a certain depth works as expected.
                    self._children.append(item)
            else:
                self._children.append(other)
            return self
        else:
            raise TypeError(
                "unsupported operand type(s) for +=: '{0}' and '{1}'".format(
                    type(self), type(other)))

    @property
    def current_level(self) -> int:
        """The current indentation level."""
        return int(self._current_indent / self._formatter.indent_increment)

    # Message building methods
    # ========================

    def add_text(self, text: str, formatter=None, item_id=None) -> "HelpItem":
        """Add a text item to be printed.

        This item displays the given text wrapped to the given width.

        Args:
            text: The text to be printed.
            formatter: A HelpFormatter object for defining the formatting of
                the new item. If 'None,' it uses the help formatter of its
                parent item.
            item_id: A unique ID for the item that can be referenced in the
                Sphinx documentation.

        Returns:
            The new HelpItem object.
        """
        return self._add_item(
            "text", text, item_id, self._format_text, formatter=formatter)

    def add_definition(
            self, name: str, args: str, msg: str, style="heading",
            formatter=None, item_id=None) -> "HelpItem":
        """Add a definition to be printed.

        This item displays a formatted definition in one of multiple styles.
        Definitions consist of a name, an argument string and a message,
        any of which can be blank.

        Args:
            name: The command, option, etc. to be defined. If auto markup is
                enabled, this is strong in the terminal output.
            args: The list of arguments for the thing being defined as a
                single string. If auto markup is enabled, arguments are
                emphasized in the terminal output.
            msg: A description of the thing being defined, with arguments
                that appear in the argument string emphasized if auto markup
                is enabled.
            style: The style of definition to use. Each style has a long name
                and a short name, either of which can be used.

                "heading", "he": Display the message on a separate line from
                the name and argument string.

                "heading_aligned", "ha": Display the message on a separate
                line from the name and argument string and align the message
                with those of all other definitions that belong to the same
                parent item and have a style of "inline_aligned". Use a
                hanging indent if the message is too long.

                "inline", "in": Display the message on the same line as the
                name and argument string. Use a hanging indent if the
                message is too long.

                "inline_aligned", "ia": Display the message on the same line
                as the name and argument string and align the message with
                those of all other definitions that belong to the same
                parent item and have the style 'inline_aligned'. Use a
                hanging indent if the message is too long.
            formatter: A HelpFormatter object for defining the formatting of
                the new item. If 'None,' it uses the help formatter of its
                parent item.
            item_id: A unique ID for the item that can be referenced in the
                Sphinx documentation.

        Raises:
            ValueError: The given style was not recognized.

        Returns:
            The new HelpItem object.
        """
        if style in ["heading", "he"]:
            format_func = functools.partial(
                self._format_heading_def, aligned=False)
        elif style in ["heading_aligned", "ha"]:
            format_func = functools.partial(
                self._format_heading_def, aligned=True)
        elif style in ["inline", "in"]:
            format_func = functools.partial(
                self._format_inline_def, aligned=False)
        elif style in ["inline_aligned", "ia"]:
            format_func = functools.partial(
                self._format_inline_def, aligned=True)
        else:
            raise ValueError(
                "unrecognized definition style '{}'".format(style))

        return self._add_item(
            "definition", [name, args, msg], item_id, format_func,
            formatter=formatter)

    def _add_item(
            self, item_type: str, content: Any, item_id: Optional[str],
            format_func: Callable, formatter: Optional[HelpFormatter]
            ) -> "HelpItem":
        """Add a new item under the current item.

        Args:
            item_type: The type of item that the current item is.
            content: The content to print.
            item_id: A unique ID for the item that can be referenced in the
                Sphinx documentation.
            format_func: The function used to format the content.
            formatter: A HelpFormatter object for defining the formatting of
                the new item. If 'None,' it uses the help formatter of its
                parent item.

        Raises:
            ValueError: The given item ID is already in use.

        Returns:
            The new HelpItem object.
        """
        if item_id is not None and self.get_item_by_id(
                item_id, start_at_root=True):
            raise ValueError(
                "The item ID '{0}' is already in use".format(item_id))

        with contextlib.ExitStack() as stack:
            if self.content:
                stack.enter_context(self._indent())

            if formatter is None:
                formatter = self._formatter

            new_item = self._new_item(
                item_type, content, item_id, format_func, self,
                self._current_indent, formatter)
            self._children.append(new_item)

        return new_item

    # Message formatting methods
    # ==========================

    def format_help(self, levels=None, item_id=None) -> str:
        """Join the help messages of each item.

        This method will return the help messages from all descendants of
        the root item as determined by the 'item_id' argument. Whether or
        not the root item has parents, the output will be left-aligned and
        wrapped accordingly.

        Args:
            levels: The number of levels of nested items to descend into.
            item_id: The ID of the root item. If 'None,' this defaults to the
                current item.

        Returns:
            The joined help message as a string.
        """
        # Dedent the output so that it's flush with the left edge.
        if item_id is None:
            target_item = self
        else:
            target_item = self.get_item_by_id(item_id)

        dedent_amount = target_item._current_indent
        help_messages = []
        for item in self.get_items(levels=levels, item_id=item_id):
            item._current_indent -= dedent_amount
            if item.content is not None:
                help_messages.append(item._format_item())

        return "\n".join([
            message for message in help_messages if message is not None])

    def get_items(
            self, levels=None, item_id=None
            ) -> Generator["HelpItem", None, None]:
        """Recursively yield nested items.

        Args:
            levels: The number of levels of nested items to descend into.
                'None' means that there is no limit.
            item_id: The ID of the root item. If 'None,' this defaults to the
                current item.

        Yields:
            The root item and all of its descendants.
        """
        if item_id is None:
            target_item = self
        else:
            target_item = self.get_item_by_id(item_id)

        yield from self._depth_search(target_item, levels=levels)

    def _format_item(self) -> str:
        """Format the items belonging to this item.

        Returns:
            A formatted help message as a string.
        """
        if self.content and self._formatter.visible:
            # The formatting functions are static methods so that the
            # current item instance can be passed in instead of the parent
            # item instance.
            help_msg = self._format_func(self, self.content)
        else:
            help_msg = None

        return help_msg

    def _depth_search(
            self, item: "HelpItem", levels=None, counter=0
            ) -> Generator["HelpItem", None, None]:
        """Recursively yield nested items.

        Args:
            item: The item to find descendants of. If 'None,' this defaults to
                self.
            levels: The number of levels of nested items to descend into.
                'None' means that there is no limit.
            counter: This parameter tracks the recursion depth.

        Yields:
            Each item in the tree.
        """
        yield item

        if levels is None or counter < levels:
            for item in item._children:
                yield from self._depth_search(
                    item, levels, counter=counter+1)

    def get_item_by_id(
            self, item_id: str, start_at_root=False, raising=False
            ) -> "HelpItem":
        """Get an item by its ID.

        Args:
            item_id: The ID of the item to get.
            start_at_root: Begin searching at the root of the current item tree
                instead of at the current item.
            raising: Raise an exception if an item is not found.

        Returns:
            An item corresponding to the ID.
        """
        if start_at_root:
            root = self._get_root_item()
        else:
            root = self

        for item in self._depth_search(root):
            if item.id is not None and item.id == item_id:
                return item

        if raising:
            raise ValueError(
                "an item with the ID '{0}' does not exist".format(item_id))

    def _get_root_item(self) -> "HelpItem":
        """Get the root item in the item tree.

        Returns:
            The root item in the tree.
        """
        if not self._parent:
            return self

        parent = self._parent
        while parent._parent:
            parent = parent._parent

        return parent

    @contextlib.contextmanager
    def _indent(self) -> None:
        """Temporarily increase the indentation level."""
        self._current_indent += self._formatter.indent_increment
        yield
        self._current_indent -= self._formatter.indent_increment

    @staticmethod
    def parse_name_markup(name_string: str) -> MarkupPositions:
        """Get the position of markup for the definition name.

        Returns:
            The positions of the substrings wrapped by the markup characters.
        """
        return MarkupPositions([(name_string, 0)], [])

    @staticmethod
    def parse_args_markup(args_string: str) -> MarkupPositions:
        """Get the position of markup for the definition argument string.

        Returns:
            The positions of the substrings wrapped by the markup characters.
        """
        positions = MarkupPositions([], [])
        for word_match in ARG_REGEX.finditer(args_string):
            match_counter = 0
            match_string = word_match.group()
            for match_instance in re.finditer(
                    re.escape(match_string), args_string):
                if match_instance.span() == word_match.span():
                    positions.em.append((match_string, match_counter))
                match_counter += 1

        return positions

    @staticmethod
    def parse_msg_markup(args: str, text: str) -> MarkupPositions:
        """Get the positions of markup for the definition message.

        This method only formats arguments surrounded by non-word characters.

        Args:
            text: The string to have markup added to.
            args: The argument string to get arguments from.

        Returns:
            The positions of the substrings wrapped by the markup characters.
        """
        positions = MarkupPositions([], [])
        for arg in ARG_REGEX.findall(args):
            for word_match in re.finditer(
                    r"(?<!\w){}(?!\w)".format(re.escape(arg)), text):
                match_counter = 0
                match_string = word_match.group()
                for match_instance in re.finditer(
                        re.escape(match_string), text):
                    if match_instance.span() == word_match.span():
                        positions.em.append((match_string, match_counter))
                    match_counter += 1

        return positions

    @staticmethod
    def parse_manual_markup(text: str) -> Tuple[str, MarkupPositions]:
        """Remove reST markup characters from text and get their positions.

        This method only parses 'strong' and 'emphasized' inline markup.

        Example:
            >>> parse_manual_markup("*Is* markup only **markup**?")
            ("Is markup only markup?", MarkupPositions(
                strong=[("markup", 1)], em=[("Is", 0)]))

        Args:
            text: The text containing reST inline markup.

        Returns:
            The original text with markup characters removed and the positions
            of the substrings wrapped by the markup characters.
        """
        inliner = Inliner()
        default_settings = OptionParser(
            components=(Parser,)).get_default_values()
        inliner.init_customizations(default_settings)

        strong_spans = []
        em_spans = []
        remaining = text
        while inliner.patterns.initial.search(remaining):
            initial_match = inliner.patterns.initial.search(text)
            start_match_start = initial_match.start("start")
            start_match_end = initial_match.end("start")
            initial_match_string = initial_match.groupdict()["start"]

            if initial_match_string == MARKUP_CHARS.strong[0]:
                end_pattern = inliner.patterns.strong
            elif initial_match_string == MARKUP_CHARS.em[0]:
                end_pattern = inliner.patterns.emphasis
            else:
                continue

            end_match = end_pattern.search(initial_match.string[start_match_end:])
            if not end_match:
                remaining = remaining[start_match_end:]
                continue
            end_match_start = end_match.start(1) + start_match_end
            end_match_end = end_match.end(1) + start_match_end

            substring = text[start_match_end:end_match_start]
            position = (
                start_match_end - len(initial_match_string),
                end_match_start - len(initial_match_string))

            if initial_match_string == MARKUP_CHARS.strong[0]:
                strong_spans.append((substring, position))
            elif initial_match_string == MARKUP_CHARS.em[0]:
                em_spans.append((substring, position))

            text = text[:start_match_start] + substring + text[end_match_end:]
            remaining = remaining[end_match_end:]

        markup_positions = MarkupPositions([], [])

        # Record the substring that should be marked up as 'strong' and the
        # instance of it if it occurs multiple times in the text.
        for substring, span in strong_spans:
            match_counter = 0
            for match in re.finditer(re.escape(substring), text):
                if match.span() == span:
                    markup_positions.strong.append((substring, match_counter))
                match_counter += 1

        # Record the substring that should be marked up as 'emphasized' and the
        # instance of it if it occurs multiple times in the text.
        for substring, span in em_spans:
            match_counter = 0
            for match in re.finditer(re.escape(substring), text):
                if match.span() == span:
                    markup_positions.em.append((substring, match_counter))
                match_counter += 1

        return text, markup_positions

    def _apply_markup(
            self, text: str, manual_positions: MarkupPositions,
            auto_positions: MarkupPositions) -> str:
        """Apply markup to text at certain positions.

        Args:
            text: The text to apply markup to.
            manual_positions: The positions of substrings to apply manual
                markup to.
            auto_positions: The positions of substrings to apply auto markup
                to.

        Returns:
            The original text with markup added.
        """
        if manual_positions is None:
            manual_positions = MarkupPositions([], [])

        if auto_positions is None:
            auto_positions = MarkupPositions([], [])

        for markup_type in ["strong", "em"]:
            combined_positions = []

            # Add manual markup first so that it overrides automatic markup if
            # they overlap.
            if self._formatter.manual_markup:
                combined_positions += getattr(manual_positions, markup_type)
            if self._formatter.auto_markup:
                combined_positions += getattr(auto_positions, markup_type)

            for substring, instance in combined_positions:
                try:
                    match = list(re.finditer(re.escape(substring), text))[instance]
                except IndexError:
                    # This can occur when manual markup conflicts with
                    # automatic markup.
                    continue
                text = (
                    text[:match.start()]
                    + getattr(self._formatter, markup_type)[0]
                    + text[match.start():match.end()]
                    + getattr(self._formatter, markup_type)[1]
                    + text[match.end():])

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

    def _get_aligned_buffer(self) -> int:
        """Get the length of the buffer to leave before aligned messages.

        This value is the length of the longest signature (name + args) of
        any sibling items that are definitions with the 'inline_aligned'
        style plus the inline buffer space. If there are none, it is the
        indentation increment.

        Returns:
            The number of spaces to buffer.
        """
        inline_content = (
            item.content for item in self._parent._children
            if item.type == "definition"
            and item._format_func.func is self._format_inline_def
            and item._format_func.keywords["aligned"] is True)
        try:
            longest = max(
                len(" ".join([string for string in (name, args) if string]))
                for name, args, msg in inline_content)
            longest += self._formatter.inline_space
        except ValueError:
            # There are no siblings that are definitions with the
            # 'inline_aligned' style.
            longest = self._formatter.indent_increment

        return longest

    def _create_sig(
            self, name: str, args: str, name_positions: MarkupPositions,
            args_positions: MarkupPositions, sig_buffer: int) -> str:
        """Create a signature for a definition.

        A 'signature' is the concatenation of the definition's name and
        argument string.

        Args:
            name: The name to be defined.
            args: The argument string for the definition.
            name_positions: The positions at which to insert markup for the
                name string.
            args_positions: The positions at which to insert markup for the
                argument string.
            sig_buffer: The amount of space there should be between the
                beginning of the line and the message.

        Returns:
            The signature string for the definition.
        """
        name_buffer = len(name)

        # Markup must be added after all text formatting has occurred
        # because the markup strings should be ignored when wrapping the
        # text. To allow the formatting to be applied to each part of the
        # definition separately, spaces are used as filler in certain places
        # so that the text can be wrapped properly before the real text is
        # substituted.
        auto_name_positions = self.parse_name_markup(name)
        auto_args_positions = self.parse_args_markup(args)

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
            + self._apply_markup(
                output_name[self._current_indent:], name_positions,
                auto_name_positions)
            + self._apply_markup(
                output_args[name_buffer:], args_positions,
                auto_args_positions))

        return output_sig

    @staticmethod
    def _format_text(self, content: str) -> str:
        """Format plain text for the help message.

        Args:
            self: The instance of the calling item.
            content: The text to be formatted.

        Returns:
            The formatted text as a string.
        """
        if self._formatter.manual_markup:
            output_text, positions = self.parse_manual_markup(content)
        else:
            output_text, positions = content, None

        wrapper = self._get_wrapper()
        output_text = wrapper.fill(output_text)
        output_text = self._apply_markup(output_text, positions, None)
        return output_text

    @staticmethod
    def _format_inline_def(
            self, content: Tuple[str, str, str], aligned: bool) -> str:
        """Format an 'inline' definition for the help message.

        Args:
            self: The instance of the calling item.
            content: A tuple containing the name, args and message for the
                definition.

        Returns:
            The formatted definition as a string.
        """
        name, args, msg = content
        if self._formatter.manual_markup:
            name, name_positions = self.parse_manual_markup(name)
            args, args_positions = self.parse_manual_markup(args)
            msg, msg_positions = self.parse_manual_markup(msg)
        else:
            name_positions = args_positions = msg_positions = None

        if aligned:
            sig_buffer = self._get_aligned_buffer()
        else:
            sig_buffer = (len(
                " ".join([string for string in (name, args) if string]))
                + self._formatter.inline_space)

        output_sig = self._create_sig(
            name, args, name_positions, args_positions, sig_buffer)

        subsequent_indent = self._formatter.indent_increment
        if aligned:
            subsequent_indent += sig_buffer
        wrapper = self._get_wrapper(
            add_initial=-self._current_indent,
            add_subsequent=subsequent_indent)

        auto_msg_positions = self.parse_msg_markup(args, msg)
        output_msg = wrapper.fill(" "*sig_buffer + msg)
        output_msg = self._apply_markup(
            output_msg, msg_positions, auto_msg_positions)

        return output_sig + output_msg[sig_buffer:]

    @staticmethod
    def _format_heading_def(
            self, content: Tuple[str, str, str], aligned: bool) -> str:
        """Format a 'heading' definition for the help message.

        Args:
            self: The instance of the calling item.
            content: A tuple containing the name, args and message for the
                definition.

        Returns:
            The formatted definition as a string.
        """
        name, args, msg = content
        if self._formatter.manual_markup:
            name, name_positions = self.parse_manual_markup(name)
            args, args_positions = self.parse_manual_markup(args)
            msg, msg_positions = self.parse_manual_markup(msg)
        else:
            name_positions = args_positions = msg_positions = None

        output_sig = self._create_sig(
            name, args, name_positions, args_positions, 0)

        if not msg:
            return output_sig

        with contextlib.ExitStack() as stack:
            if aligned:
                sig_buffer = self._get_aligned_buffer()
                wrapper = self._get_wrapper(
                    add_initial=sig_buffer,
                    add_subsequent=(
                        sig_buffer + self._formatter.indent_increment))
            else:
                stack.enter_context(self._indent())
                wrapper = self._get_wrapper()

            auto_msg_positions = self.parse_msg_markup(args, msg)
            output_msg = wrapper.fill(msg)
            output_msg = self._apply_markup(
                output_msg, msg_positions, auto_msg_positions)

        return "\n".join([output_sig, output_msg])
