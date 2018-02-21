"""Define a tree of items.

Copyright © 2017-2018 Garrett Powell <garrett@gpowell.net>

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
import enum
import copy
import shutil
import textwrap
import functools
import contextlib
import collections
from typing import (
    Any, Tuple, Generator, Optional, NamedTuple, List, Callable)

from docutils.frontend import OptionParser
from docutils.parsers.rst import Parser
from docutils.parsers.rst.states import Inliner

from linotype.ansi import ansi_format

try:
    import colorama
except ImportError:
    pass
else:
    colorama.init()

ARG_REGEX = re.compile(r"([\w-]+)")
MARKUP_CHARS = collections.namedtuple(
    "MARKUP_CHARS", ["strong", "em"])("**", "*")

MarkupPositionsBase = NamedTuple(
    "MarkupPositions",
    [("strong", List[Tuple[str, int]]), ("em", List[Tuple[str, int]])])


class MarkupPositions(MarkupPositionsBase):
    """Keep track of the positions of marked-up substring in a string.

    Each tuple contains the substring and the instance of that substring for
    cases where there are more than one in the string.
    """
    def __add__(self, other: "MarkupPositions"):
        return MarkupPositions(
            self.strong + other.strong,
            self.em + other.em)


class DefStyle(enum.Enum):
    """Styles for definition items.

    Attributes:
        PARAGRAPH, P: Display the message as a paragraph on a separate line
            from the term and argument string.
        INLINE, I: Display the message on the same line as the term and
            argument string. Use a hanging indent if the message is too long.
        ALIGNED, A: Display the message on the same line as the term and
            argument string and align the message with those of all other
            definitions that belong to the same parent item and have the style
            ALIGNED. Use a hanging indent if the message is too long.
        OVERFLOW, O: Display the message on a separate line from the term and
            argument string and align the message with those of all other
            definitions that belong to the same parent item and have a style of
            ALIGNED. Use a hanging indent if the message is too long.
    """
    PARAGRAPH = P = 1
    OVERFLOW = O = 2
    INLINE = I = 3
    ALIGNED = A = 4


class Formatter:
    """Control how the text output is formatted.

    Attributes:
        max_width: The maximum number of columns at which to wrap text in the
            text output.
        auto_width: Wrap the text to the size of the terminal.
        indent_spaces: The number of spaces to increase/decrease the indent
            level by for each level.
        def_gap: The minimum number of spaces to leave between the argument
            string and message of each definition when they are on the same
            line.
        def_style: A DefStyle instance representing the style of definition to
            use.
        auto_markup: Automatically apply 'strong' and 'emphasized' formatting
            to certain text in the output.
        manual_markup: Parse reST 'strong' and 'emphasized' inline markup.
        visible: Make the text visible in the output.
        strong: A 2-tuple containing the strings to print before and after
            strings marked up as 'strong'. The default is ANSI bold.
        em: A 2-tuple containing the strings to print before and after strings
            marked up as 'emphasized'. The default is ANSI underlined.
    """
    def __init__(
            self, max_width=79, auto_width=True, indent_spaces=4,
            def_gap=2, def_style=DefStyle.PARAGRAPH,
            auto_markup=True, manual_markup=True, visible=True,
            strong=ansi_format(bold=True), em=ansi_format(underline=True)
            ) -> None:
        self.max_width = max_width
        self.auto_width = auto_width
        self.indent_spaces = indent_spaces
        self.def_gap = def_gap
        self.def_style = def_style
        self.auto_markup = auto_markup
        self.manual_markup = manual_markup
        self.visible = visible
        self.strong = strong
        self.em = em


class Item:
    """An item to be displayed in the output.

    This class allows for formatting text output consisting of a tree of
    "items". There are multiple types of items to choose from, and every
    item can contain other items which are indented relative to the parent
    item. Items at the same level are displayed at the order in which they
    were created.

    This class is used to create a root-level item, and new child items can
    be created using its public methods. Every item has a Formatter instance
    which determines how it is formatted in the text output. Every item also
    has an ID which can be referenced in the Sphinx documentation or when
    formatting the text output.

    Args:
        formatter: The Formatter object for the item tree.

    Attributes:
        content: The content to display in the output.
        formatter: The Formatter object for the item tree.
        id: The item ID.
        current_level: The current indentation level.
        parent: The parent Item object.
        _format_func: The function used for formatting the text output.
        _current_indent: The number of spaces that the item is currently
            indented.
        children: A list of all Item objects belonging to this item.
    """
    def __init__(self, formatter=Formatter()) -> None:
        self.content = None
        self.formatter = formatter
        self.id = None
        self.parent = None
        self.children = []
        self._current_indent = 0

    def __repr__(self) -> str:
        if self.children:
            child_reprs = [
                "<{}>".format(type(child).__name__) for child in self.children]
        else:
            child_reprs = [""]

        return "<{0}: {1}>".format(type(self).__name__, " ".join(child_reprs))

    @property
    def _format_func(self) -> Callable:
        """Get the function for formatting the text output."""
        return lambda: None

    @property
    def current_level(self) -> int:
        """The current indentation level."""
        return int(self._current_indent / self.formatter.indent_spaces)

    # Message building methods
    # ========================

    def add_text(self, text: str, formatter=None, item_id=None) -> "Item":
        """Add a text item to be printed.

        This item displays the given text wrapped to the given width.

        Args:
            text: The text to be printed.
            formatter: A Formatter object for defining the formatting of the
                new item. If 'None,' it uses the formatter of its parent item.
            item_id: A unique ID for the item that can be referenced in the
                Sphinx documentation or when formatting the text output.

        Returns:
            The new Item object.
        """
        return self._add_item(TextItem, text, formatter, item_id)

    def add_def(
            self, term: str, args: str, message: str, formatter=None,
            item_id=None) -> "Item":
        """Add a definition item to be printed.

        This item displays a formatted definition in one of multiple styles.
        The style is set by the Formatter instance. Definitions consist of a
        term, an argument string and a message, any of which can be blank.

        Args:
            term: The command, option, etc. to be defined. If auto markup is
                enabled, this is strong in the text output.
            args: The list of arguments for the thing being defined as a
                single string. If auto markup is enabled, arguments are
                emphasized in the text output. Arguments are consecutive
                strings of unicode word characters
            message: A description of the thing being defined, with arguments
                that appear in the argument string emphasized if auto markup
                is enabled.
            formatter: A Formatter instance for defining the formatting of the
                new item. If 'None,' it uses the formatter of its parent item.
            item_id: A unique ID for the item that can be referenced in the
                Sphinx documentation or when formatting the text output.

        Returns:
            The new Item object.
        """
        return self._add_item(
            DefinitionItem, [term, args, message], formatter, item_id)

    def _add_item(
            self, item_type, content: Any,
            formatter: Optional[Formatter], item_id: Optional[str]) -> "Item":
        """Add a new item under the current item.

        Args:
            item_type: The type of the new item.
            content: The content to print.
            formatter: A Formatter object for the item. If 'None,' it uses the
                formatter of its parent item.
            item_id: A unique ID for the item.

        Raises:
            ValueError: The given item ID is already in use.

        Returns:
            The new Item object.
        """
        if item_id is not None and self.get_item_by_id(
                item_id, start_at_root=True):
            raise ValueError(
                "the item ID '{0}' is already in use".format(item_id))

        with contextlib.ExitStack() as stack:
            if self.parent:
                stack.enter_context(self._indent())

            if formatter is None:
                # Making this a copy ensures that modifying the formatter of
                # an item doesn't modify the formatter of its parent.
                formatter = copy.copy(self.formatter)

            new_item = item_type(content, self, formatter, item_id)
            self.children.append(new_item)

        return new_item

    # Message formatting methods
    # ==========================

    def format(self, levels=None, item_id=None) -> str:
        """Print a tree of items.

        Args:
            levels: The number of levels of nested items to descend into.
            item_id: The ID of the root item. If 'None,' this defaults to the
                current item.

        Returns:
            The text output as a single string.
        """
        # Dedent the output so that it's flush with the left edge.
        if item_id is None:
            target_item = self
        else:
            target_item = self.get_item_by_id(item_id)

        if not target_item:
            raise ValueError(
                "an item with the ID '{0}' does not exist".format(item_id))

        dedent_amount = target_item._current_indent
        help_messages = []
        for item in self.get_items(levels=levels, item_id=item_id):
            item._current_indent -= dedent_amount
            if item.parent:
                help_messages.append(item._format_item())

        return "\n".join([
            message for message in help_messages if message is not None])

    def get_items(
            self, levels=None, item_id=None
            ) -> Generator["Item", None, None]:
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
            The formatted text output as a string.
        """
        if self.parent and self.formatter.visible:
            help_message = self._format_func(self.content)
        else:
            help_message = None

        return help_message

    def _depth_search(
            self, item: "Item", levels=None, counter=0
            ) -> Generator["Item", None, None]:
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
            for item in item.children:
                yield from self._depth_search(
                    item, levels, counter=counter+1)

    def get_item_by_id(
            self, item_id: str, start_at_root=False, raising=False
            ) -> "Item":
        """Get an item by its ID.

        Args:
            item_id: The ID of the item to get.
            start_at_root: Begin searching at the root of the current item tree
                instead of at the current item.
            raising: Raise an exception if an item is not found.

        Raises:
            ValueError: An item with the given item ID doesn't exist.

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

    def _get_root_item(self) -> "Item":
        """Get the root item in the item tree.

        Returns:
            The root item in the tree.
        """
        if not self.parent:
            return self

        parent_item = self.parent
        while parent_item.parent:
            parent_item = parent_item.parent

        return parent_item

    @contextlib.contextmanager
    def _indent(self) -> None:
        """Temporarily increase the indentation level."""
        self._current_indent += self.formatter.indent_spaces
        yield
        self._current_indent -= self.formatter.indent_spaces

    @property
    def _width(self) -> int:
        """Get the number of columns to wrap text to.

        This is either the width of the terminal window or the maximum width
        set in the Formatter instance, whichever is smaller.
        """
        if self.formatter.auto_width:
            return min(
                self.formatter.max_width, shutil.get_terminal_size().columns)
        else:
            return self.formatter.max_width

    @staticmethod
    def parse_manual_markup(text: str) -> Tuple[str, MarkupPositions]:
        """Remove reST markup characters from text and get their positions.

        This method only parses 'strong' and 'emphasized' inline markup.

        Example:
            >>> parse_manual_markup("The **ants** were marching two by *two*.")
            ("The ants were marching two by two.", MarkupPositions(
                strong=[("ants", 0)], em=[("two", 1)]))

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
        previous_match_end = 0
        offset = 0  # Adjust for characters removed from the original string.
        for initial_match in inliner.patterns.initial.finditer(text):
            initial_match_start = initial_match.start() + offset
            initial_match_end = initial_match.end() + offset
            if initial_match_start < previous_match_end:
                # The current initial match comes before the previous match.
                continue

            previous_match_end = initial_match_end

            # Determine what type of markup it is.
            initial_match_string = initial_match.groupdict()["start"]
            if initial_match_string == MARKUP_CHARS.strong:
                end_pattern = inliner.patterns.strong
            elif initial_match_string == MARKUP_CHARS.em:
                end_pattern = inliner.patterns.emphasis
            else:
                continue

            # Search the end markup that corresponds to the initial markup.
            end_match = end_pattern.search(
                initial_match.string[initial_match_end:])

            if not end_match:
                # Opening markup without closing markup is left alone. This
                # prevents that opening markup from creating an infinite loop
                # where it is matched over and over again.
                continue

            end_match_start = end_match.start() + initial_match_end + offset
            end_match_end = end_match.end() + initial_match_end + offset

            content = text[initial_match_end:end_match_start]
            span = (
                initial_match_end - len(initial_match_string),
                end_match_start - len(initial_match_string))

            if initial_match_string == MARKUP_CHARS.strong:
                strong_spans.append((content, span))
            elif initial_match_string == MARKUP_CHARS.em:
                em_spans.append((content, span))

            # Remove markup characters from the string and keep track of the
            # index offset.
            new_text = text[:initial_match_start] + content + text[end_match_end:]
            offset -= len(text) - len(new_text)
            text = new_text
            previous_match_end = end_match_end

        markup_positions = MarkupPositions([], [])

        # Record the substring that should be marked up as 'strong' and the
        # instance of it if it occurs multiple times in the text.
        for content, span in strong_spans:
            match_counter = 0
            for match in re.finditer(re.escape(content), text):
                if match.span() == span:
                    markup_positions.strong.append((content, match_counter))
                match_counter += 1

        # Record the substring that should be marked up as 'emphasized' and the
        # instance of it if it occurs multiple times in the text.
        for content, span in em_spans:
            match_counter = 0
            for match in re.finditer(re.escape(content), text):
                if match.span() == span:
                    markup_positions.em.append((content, match_counter))
                match_counter += 1

        return text, markup_positions

    def _apply_markup(self, text: str, positions: MarkupPositions) -> str:
        """Apply ANSI escape sequences to text at certain positions.

        Args:
            text: The text to apply the markup to.
            positions: The positions of substrings to apply markup to.

        Returns:
            The original text with ANSI escape sequences added.
        """
        markup_spans = []
        for markup_type in ["strong", "em"]:
            for substring, instance in getattr(positions, markup_type):
                # Match any number of whitespace and newline characters
                # between each word in the substring since line breaks can
                # only happen between words. It is necessary to strip out
                # spaces because sometimes spaces are replaced with newlines
                # in the formatted text, which is a problem when the text
                # isn't indented.
                words = re.split(r"(\w+)", substring)
                substring_regex = re.compile("[\n\\s]*".join(
                    re.escape(word) for word in words if word.strip()))
                match = list(substring_regex.finditer(text))[instance]
                markup_spans.append((match.span(), markup_type))

        markup_spans.sort(key=lambda x: x[0][1], reverse=True)
        markup_spans.sort(key=lambda x: x[0][0])

        # Get the positions of ANSI escape sequences in the text. Keep track of
        # which sequences are still "open" so that the ends of other sequences
        # don't close them. This allows for nested markup.
        markup_sequences = []
        open_sequences = []
        for (start, end), markup_type in markup_spans:
            start_sequence, end_sequence = getattr(
                self.formatter, markup_type)

            open_sequences = [
                (position, sequence) for position, sequence in open_sequences
                if position > start]

            markup_sequences.append((start, start_sequence))
            markup_sequences.append((end, end_sequence))
            markup_sequences += [
                (end, sequence) for position, sequence in open_sequences]

            open_sequences.append((end, start_sequence))

        markup_sequences.sort(key=lambda x: x[0])

        # Get a list of strings that will make up the output. This is the
        # ordered ANSI escape sequences with the appropriate text between them.
        prev_position = 0
        text_sequences = []
        for position, sequence in markup_sequences:
            text_sequences.append(text[prev_position:position])
            text_sequences.append(sequence)
            prev_position = position
        text_sequences.append(text[prev_position:])

        return "".join(text_sequences)


class TextItem(Item):
    """A text item to be displayed in the output.

    Args:
        content: The content to display in the output.
        parent: The parent Item object.
        formatter: The Formatter object for the item tree.
        item_id: The item ID.

    Attributes:
        content: The content to display in the output.
        id: The item ID.
        parent: The parent Item object.
        _format_func: The function used for formatting the text output.
        _current_indent: The number of spaces that the item is currently
            indented.
    """
    def __init__(
            self, content: Any, parent: Item, formatter: Formatter,
            item_id: Optional[str]) -> None:
        super().__init__(formatter)
        self.content = content
        self.id = item_id
        self.parent = parent
        self._current_indent = parent._current_indent

    @property
    def _format_func(self) -> Callable:
        """Get the function for formatting the text output."""
        return self._format

    def _format(self, content: str) -> str:
        """Format plain text for the text output.

        Args:
            content: The text to be formatted.

        Returns:
            The formatted text as a string.
        """
        if self.formatter.manual_markup:
            output_text, positions = self.parse_manual_markup(content)
        else:
            output_text, positions = content, MarkupPositions([], [])

        wrapper = textwrap.TextWrapper(width=self._width)
        output_text = wrapper.fill(output_text)
        output_text = self._apply_markup(output_text, positions)
        return textwrap.indent(output_text, " "*self._current_indent)


class DefinitionItem(Item):
    """A definition item to be displayed in the output.

    Args:
        content: The content to display in the output.
        parent: The parent Item object.
        formatter: The Formatter object for the item tree.
        item_id: The item ID.

    Attributes:
        content: The content to display in the output.
        id: The item ID.
        parent: The parent Item object.
        _format_func: The function used for formatting the text output.
        _current_indent: The number of spaces that the item is currently
            indented.
    """
    def __init__(
            self, content: Any, parent: Item, formatter: Formatter,
            item_id: Optional[str]) -> None:
        super().__init__(formatter)
        self.content = content
        self.id = item_id
        self.parent = parent
        self._current_indent = parent._current_indent

    @property
    def _format_func(self) -> Callable:
        """Get the function for formatting the text output.

        Raises:
            ValueError: The definition style was unrecognized.

        Returns:
             The function for formatting the text output.
        """
        style = self.formatter.def_style
        if style is DefStyle.PARAGRAPH:
            return functools.partial(self._format_newline, aligned=False)
        elif style is DefStyle.OVERFLOW:
            return functools.partial(self._format_newline, aligned=True)
        elif style is DefStyle.INLINE:
            return functools.partial(self._format_sameline, aligned=False)
        elif style is DefStyle.ALIGNED:
            return functools.partial(self._format_sameline, aligned=True)

    @staticmethod
    def parse_term_markup(term_string: str) -> MarkupPositions:
        """Get the position of markup for the definition term.

        Returns:
            The positions of the substrings that should have markup applied.
        """
        return MarkupPositions([(term_string, 0)], [])

    @staticmethod
    def parse_args_markup(args_string: str) -> MarkupPositions:
        """Get the position of markup for the definition argument string.

        Returns:
            The positions of the substrings that should have markup applied.
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
    def parse_message_markup(args: str, text: str) -> MarkupPositions:
        """Get the positions of markup for the definition message.

        This method only formats arguments surrounded by non-word characters.

        Args:
            text: The string to have markup added to.
            args: The argument string to get arguments from.

        Returns:
            The positions of the substrings that should have markup applied.
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

    def _get_aligned_buffer(self) -> int:
        """Get the length of the buffer to leave before aligned messages.

        This value is the length of the longest signature (term + args) of
        any sibling items that are definitions with the ALIGNED style plus
        the definition buffer space. If there are none, it is the indentation
        increment.

        Returns:
            The number of spaces to buffer.
        """
        aligned_content = (
            item.content for item in self.parent.children
            if isinstance(item, type(self))
            and item.formatter.def_style is DefStyle.ALIGNED)
        try:
            longest = max(
                len(" ".join([string for string in (term, args) if string]))
                for term, args, message in aligned_content)
            longest += self.formatter.def_gap
        except ValueError:
            # There are no siblings that are definitions with the ALIGNED
            # style.
            longest = self.formatter.indent_spaces

        return longest

    def _create_signature(
            self, term: str, args: str, term_positions: MarkupPositions,
            args_positions: MarkupPositions, signature_buffer: int) -> str:
        """Create a signature for a definition.

        A 'signature' is the concatenation of the definition's term and
        argument string. It is not wrapped, no matter how long it is.

        Args:
            term: The term to be defined.
            args: The argument string for the definition.
            term_positions: The positions at which to insert markup for the
                term string.
            args_positions: The positions at which to insert markup for the
                argument string.
            signature_buffer: The amount of space there should be between the
                beginning of the line and the message.

        Returns:
            The signature string for the definition.
        """
        term_buffer = len(term)

        # Markup must be added after all text formatting has occurred
        # because the markup strings shouldn't affect the text wrapping. To
        # allow the formatting to be applied to each part of the definition
        # separately, spaces are used as filler in certain places so that
        # the text can be wrapped properly before the real text is
        # substituted.
        if self.formatter.auto_markup:
            term_positions += self.parse_term_markup(term)
            args_positions += self.parse_args_markup(args)

        output_args = "{0:<{1}}".format(
            " "*(term_buffer + 1) + args, signature_buffer)

        output_signature = (
            self._apply_markup(term, term_positions)
            + self._apply_markup(
                output_args[term_buffer:], args_positions))

        return output_signature

    def _format_sameline(
            self, content: Tuple[str, str, str], aligned: bool) -> str:
        """Format an INLINE or ALIGNED definition for the text output.

        Args:
            content: A tuple containing the term, args and message for the
                definition.
            aligned: Align the definition with all others belonging to the same
                parent item and with a style of ALIGNED.

        Returns:
            The formatted definition as a string.
        """
        term, args, message = content
        if self.formatter.manual_markup:
            term, term_positions = self.parse_manual_markup(term)
            args, args_positions = self.parse_manual_markup(args)
            message, message_positions = self.parse_manual_markup(message)
        else:
            term_positions = args_positions = message_positions = (
                MarkupPositions([], []))

        if self.formatter.auto_markup:
            message_positions += self.parse_message_markup(args, message)

        # Get the total length of the term and argument string.
        if aligned:
            signature_buffer = self._get_aligned_buffer()
        else:
            signature_buffer = (
                len(" ".join([string for string in (term, args) if string]))
                + self.formatter.def_gap)

        # This is the combined term and argument string.
        output_signature = self._create_signature(
            term, args, term_positions, args_positions, signature_buffer)

        subsequent_indent = self.formatter.indent_spaces
        if aligned:
            subsequent_indent += signature_buffer
        wrapper = textwrap.TextWrapper(
            width=self._width - self._current_indent,
            subsequent_indent=" "*subsequent_indent)

        output_message = wrapper.fill(" "*signature_buffer + message)
        output_message = self._apply_markup(output_message, message_positions)

        return textwrap.indent(
            output_signature + output_message[signature_buffer:],
            " "*self._current_indent)

    def _format_newline(
            self, content: Tuple[str, str, str], aligned: bool) -> str:
        """Format a PARAGRAPH or OVERFLOW definition for the text output.

        Args:
            content: A tuple containing the term, args and message for the
                definition.
            aligned: Align the definition with all others belonging to the same
                parent item and with a style of ALIGNED.

        Returns:
            The formatted definition as a string.
        """
        term, args, message = content
        if self.formatter.manual_markup:
            term, term_positions = self.parse_manual_markup(term)
            args, args_positions = self.parse_manual_markup(args)
            message, message_positions = self.parse_manual_markup(message)
        else:
            term_positions = args_positions = message_positions = (
                MarkupPositions([], []))

        if self.formatter.auto_markup:
            message_positions += self.parse_message_markup(args, message)

        # This is the combined term and argument string.
        output_signature = self._create_signature(
            term, args, term_positions, args_positions, 0)

        if not message:
            return textwrap.indent(output_signature, " "*self._current_indent)

        if aligned:
            signature_buffer = self._get_aligned_buffer()
            initial_indent = " "*signature_buffer
            subsequent_indent = " "*(signature_buffer + self.formatter.indent_spaces)
        else:
            initial_indent = " "*self.formatter.indent_spaces
            subsequent_indent = " "*self.formatter.indent_spaces
        wrapper = textwrap.TextWrapper(
            width=self._width - self._current_indent,
            initial_indent=initial_indent,
            subsequent_indent=subsequent_indent)

        output_message = wrapper.fill(message)
        output_message = self._apply_markup(output_message, message_positions)

        return textwrap.indent(
            "\n".join([output_signature, output_message]), " "*self._current_indent)
