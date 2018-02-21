"""Extend Sphinx to allow importing items into a reStructuredText document.

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
import os
import re
import importlib
import collections
from typing import List, Tuple, NamedTuple, Optional, Dict, Set

from docutils import nodes
from docutils.parsers.rst import Directive
from docutils.parsers.rst.directives import unchanged, flag

from linotype.items import Item, TextItem, DefinitionItem, MarkupPositions


# These keep track of content that was used to extend items through the
# directive.
ExtraContent = NamedTuple(
    "ExtraContent",
    [("classifiers", Set[str]), ("nodes", List[nodes.Element])])
ExtraContentDict = Dict[str, List[ExtraContent]]

CONTENT_CLASSIFIERS = {"@after", "@before", "@replace"}
MARKUP_CLASSIFIERS = {"@auto", "@rst"}
ALL_CLASSIFIERS = CONTENT_CLASSIFIERS | MARKUP_CLASSIFIERS


def _parse_definition_list(
        def_list_node: nodes.definition_list) -> ExtraContentDict:
    """Parse a definition list inside the directive.

    Args:
        def_list_node: A definition list node containing definitions for
            extending the Sphinx output.

    Raises:
        ValueError: The given classifier was unrecognized.

    Returns:

        A dict where keys are item IDs and values contain the classifiers
        and the content as lists of docutils nodes.
    """
    definitions = collections.defaultdict(lambda: None)
    for node in def_list_node:
        if not isinstance(node, nodes.definition_list_item):
            continue

        term = _get_matching_child(node, nodes.term, last=False).astext()

        classifiers = set()
        for child_node in node.children:
            if not isinstance(child_node, nodes.classifier):
                continue
                
            classifier = child_node.astext()

            if classifier not in ALL_CLASSIFIERS:
                raise ValueError("unknown classifier '{0}'".format(classifier))
            
            classifiers.add(classifier)

        if not classifiers & CONTENT_CLASSIFIERS:
            classifiers.add("@after")
        if not classifiers & MARKUP_CLASSIFIERS:
            classifiers.add("@auto")

        content = _get_matching_child(
            node, nodes.definition, last=False).children

        if not definitions[term]:
            definitions[term] = []

        definitions[term].append(ExtraContent(classifiers, content))

    return definitions


def _get_matching_child(
        parent_node: nodes.Element, child_class: nodes.Element, last=True):
    """Get the first or last child node that matches a Node subclass.

    Args:
        parent_node: The node to find the child of.
        child_class: The Node subclass to check against.
        last: If True, find the last matching child. If False, find the first
            one.

    Returns:
        The first or last child Node object that is an instance of the given
        class.
    """
    if last:
        children = reversed(parent_node.children)
    else:
        children = parent_node.children

    for child_node in children:
        if isinstance(child_node, child_class):
            return child_node


def _extend_auto(
        existing_content: str, extra_content: List[ExtraContent]) -> str:
    """Extend plain text with extra content.

    Args:
        existing_content: The content to be extended.
        extra_content: The content used to extend the existing content.

    Returns:
        The existing content with the new content added.
    """
    new_content = existing_content
    for content in extra_content:
        if "@auto" not in content.classifiers:
            continue

        extra_content_text = " ".join(
            content_node.rawsource for content_node in content.nodes)

        if "@after" in content.classifiers:
            new_content = " ".join([new_content, extra_content_text])
        elif "@before" in content.classifiers:
            new_content = " ".join([extra_content_text, new_content])
        elif "@replace" in content.classifiers:
            new_content = extra_content_text

    return new_content


def _extend_rst(
        extendable_node: nodes.Element, extra_content: List[ExtraContent]
        ) -> None:
    """Modify a node with extra content.

    Args:
        extendable_node: The node to modify with new content.
        extra_content: The new content to add to the node.
    """
    for content in extra_content:
        if "@rst" not in content.classifiers:
            continue

        if "@after" in content.classifiers:
            extendable_node += content.nodes
        elif "@before" in content.classifiers:
            # The new nodes have to be added this way. Using insert() or
            # reassigning extendable_node.children messes up the "parent"
            # attribute for each of the children.
            extendable_node.children.reverse()
            extendable_node += reversed(content.nodes)
            extendable_node.children.reverse()
        elif "@replace" in content.classifiers:
            extendable_node.children = content.nodes


def _apply_markup(text: str, positions: MarkupPositions) -> List[nodes.Node]:
    """Convert markup to a list of nodes.

    This method supports nested markup.

    Args:
        text: The text to apply markup to.
        positions: The positions of substrings to apply markup to.

    Returns:
        A list of Node objects.
    """
    # Get the start and end positions of each substring that should have
    # markup applied. These are referred to as "spans." Create a list
    # of tuples where each tuple has the format:
    # ((start, end), markup_type).
    markup_spans = []
    for markup_type in ["strong", "em"]:
        # Get the positions of each substring in the string.
        for substring, instance in getattr(positions, markup_type):
            match = list(re.finditer(re.escape(substring), text))[instance]
            markup_spans.append((match.span(), markup_type))

    # Order the spans by their start position.
    markup_spans.sort(key=lambda x: x[0][0])

    def parse_top_level(markup_spans, parent_span):
        """Parse nested spans to create Node objects.

        This function works from the outside in, parsing one level of
        nested spans at a time.

        Args:
            markup_spans: A list of spans in the form:
                ((start, end), markup_type).
            parent_span: The span containing the current list of spans in
                the form: (start, end).

        Returns:
            A list of docutils Node objects.
        """
        # Get a list of top-level spans, including spans without any
        # markup.
        prev_end = parent_span[0]
        top_level_spans = []
        for (start, end), markup_type in markup_spans:
            if start < prev_end:
                # This span is nested inside another span.
                continue

            top_level_spans.append(((prev_end, start), None))
            top_level_spans.append(((start, end), markup_type))

            prev_end = end
        top_level_spans.append(((prev_end, parent_span[1]), None))

        # Create nodes from those spans.
        top_level_nodes = []
        for (start, end), markup_type in top_level_spans:
            if markup_type is None:
                top_level_nodes.append(nodes.Text(text[start:end]))
            elif markup_type == "strong":
                top_level_nodes.append(nodes.strong())
            elif markup_type == "em":
                top_level_nodes.append(nodes.emphasis())

        # Iterate over nested spans and add those nodes to their parent
        # nodes.
        for i, ((start, end), markup_type) in enumerate(top_level_spans):
            if markup_type is None:
                continue

            nested_spans = []
            for (nested_start, nested_end), nested_type in markup_spans:
                if (nested_start in range(start, end)
                        and nested_end in range(start, end + 1)
                        and (nested_start, nested_end) != (start, end)):
                    nested_spans.append(
                        ((nested_start, nested_end), nested_type))

            top_level_nodes[i] += parse_top_level(
                nested_spans, (start, end))

        return top_level_nodes

    return parse_top_level(markup_spans, (0, len(text)))


class LinotypeDirective(Directive):
    """Convert items into docutils nodes."""
    has_content = True
    required_arguments = 0
    optional_arguments = 0
    option_spec = {
        "module": unchanged,
        "filepath": unchanged,
        "function": unchanged,
        "item_id": unchanged,
        "children": flag,
        "no_auto_markup": flag,
        "no_manual_markup": flag}

    def _retrieve_item(self) -> Item:
        """Get the Item object from the given module or filepath.

        Returns:
            The output of the specified function from the specified module or
            file.
        """
        if "module" in self.options and "function" in self.options:
            # Import from given module.
            module_name = self.options["module"]
            function_name = self.options["function"]

            try:
                given_module = importlib.import_module(module_name)
            except ImportError:
                raise self.error(
                    "failed to import module '{0}'".format(module_name))

            if not hasattr(given_module, function_name):
                raise self.error("module '{0}' has no attribute '{1}'".format(
                    module_name, function_name))

            func = getattr(given_module, function_name)

        elif "filepath" in self.options and "function" in self.options:
            # Import from given file.
            filepath = self.options["filepath"]
            function_name = self.options["function"]
            local_dict = {}

            file = open(os.path.abspath(filepath))
            code = compile(file.read(), filepath, "exec")
            exec(code, local_dict)

            func = local_dict[function_name]

        else:
            raise self.error(
                "both :function: and either :module: or :filepath: must be "
                "specified.")

        return func()

    def _parse_item(
            self, item: Item, extra_content: Optional[List[ExtraContent]]
            ) -> List[nodes.Element]:
        """Convert an Item object to a docutils Node object.

        Args:
            item: The Item object to convert to a Node object.
            extra_content: A tuple containing a list of docutils nodes to
                extend the item with and the classifier describing how they
                should be applied.

        Raises:
            ValueError: The type of the given item was not recognized.

        Returns:
            A list of docutils nodes.
        """
        root_node = nodes.section()
        
        if isinstance(item, TextItem):
            # Add a definition node after the paragraph node to act as a
            # starting point for new sub-nodes.
            text = item.content
            if extra_content:
                text = _extend_auto(text, extra_content)

            if "no_manual_markup" in self.options:
                text_positions = MarkupPositions([], [])
            else:
                text, text_positions = item.parse_manual_markup(text)

            new_node = nodes.paragraph(
                "", "", *_apply_markup(text, text_positions))
            
            root_node += new_node

            extendable_node = root_node
        elif isinstance(item, DefinitionItem):
            term, args, message = item.content
            if extra_content:
                message = _extend_auto(message, extra_content)

            if "no_manual_markup" not in self.options:
                term, term_positions = item.parse_manual_markup(term)
                args, args_positions = item.parse_manual_markup(args)
                message, message_positions = item.parse_manual_markup(message)
            else:
                term_positions = args_positions = message_positions = (
                    MarkupPositions([], []))

            if "no_auto_markup" not in self.options:
                term_positions += item.parse_term_markup(term)
                args_positions += item.parse_args_markup(args)
                message_positions += item.parse_message_markup(args, message)

            new_node = nodes.definition_list_item(
                    "", nodes.term(
                        "", "", *_apply_markup(term, term_positions),
                        nodes.Text(" "),
                        *_apply_markup(args, args_positions)),
                    nodes.definition(
                        "", nodes.paragraph(
                            "", "", *_apply_markup(message, message_positions))))
            
            root_node += new_node
            extendable_node = _get_matching_child(new_node, nodes.definition)
        else:
            raise ValueError("unrecognized item type '{0}'".format(type(item)))

        if extra_content:
            _extend_rst(extendable_node, extra_content)

        return root_node.children

    def _parse_tree(
            self, root_item: Item, extra_content: ExtraContentDict
            ) -> List[nodes.Node]:
        """Convert a tree of Item objects to a tree of Node objects.
        
        Docutils definitions are used for indentation.

        Args:
            root_item: The Item object to convert to a tree of docutils
                Node objects.
            extra_content: Extra content from the directive body that is to be
                added to the node tree.

        Returns:
            The list of Node objects that make up the root of the tree.
        """
        root_node = nodes.section()
        parent_node = root_node
        previous_level = root_item.current_level

        if type(root_item) is not Item:
            if root_item.parent:
                # The root item is to be included in the output.
                new_nodes = self._parse_item(
                    root_item, extra_content[root_item.id])
                if isinstance(root_item, DefinitionItem):
                    definition_list = nodes.definition_list()
                    definition_list += new_nodes
                    root_node += definition_list
                else:
                    root_node += new_nodes
            else:
                # The root item is not to be included in the output.
                previous_level += 1

        # This keeps track of the current indentation level by maintaining a
        # queue with the current parent node on the right and all of its
        # ancestors up the tree moving to the left.
        ancestor_nodes = collections.deque()
        
        for item in root_item.get_items():
            if item is root_item:
                continue
                
            if item.current_level > previous_level:
                # The indentation level increased.
                ancestor_nodes.append(parent_node)

                if not isinstance(parent_node[-1], nodes.definition_list):
                    # Create a new empty definition to act as a starting
                    # point for new nodes. 
                    parent_node.append(nodes.definition_list(
                        "", nodes.definition_list_item(
                            "", nodes.term(), nodes.definition())))

                if parent_node.children:
                    # Set the parent node equal to the last definition in 
                    # the last definition_list_item in the last 
                    # definition_list belonging to the current parent node. 
                    definition_list = _get_matching_child(
                        parent_node, nodes.definition_list)
                    definition_list_item = _get_matching_child(
                        definition_list, nodes.definition_list_item)
                    definition = _get_matching_child(
                        definition_list_item, nodes.definition)
                    parent_node = definition
            elif item.current_level < previous_level:
                # The indentation level decreased.
                for i in range(previous_level - item.current_level):
                    new_parent = ancestor_nodes.pop()
                parent_node = new_parent

            new_nodes = self._parse_item(item, extra_content[item.id])
            if isinstance(item, DefinitionItem):
                # Wrap definitions in a definition_list.
                if not parent_node.children or not isinstance(
                        parent_node[-1], nodes.definition_list):
                    parent_node.append(nodes.definition_list())
                parent_node[-1] += new_nodes
            else:
                parent_node += new_nodes
                
            previous_level = item.current_level

        return root_node.children

    def run(self) -> List[nodes.Node]:
        """Run the directive.

        Returns:
            A list of Node objects.
        """
        root_item = self._retrieve_item()

        if "item_id" in self.options:
            root_item = root_item.get_item_by_id(
                self.options["item_id"], raising=True)

        if "children" in self.options:
            root_item.parent = None

        # Parse directive and get content to extend items with.
        nested_nodes = nodes.paragraph()
        self.state.nested_parse(
            self.content, self.content_offset, nested_nodes)
        def_list = _get_matching_child(
            nested_nodes, nodes.definition_list, last=False)
        if def_list is not None:
            definitions = _parse_definition_list(def_list)
        else:
            definitions = collections.defaultdict(lambda: None)

        return self._parse_tree(root_item, definitions)


def setup(app) -> None:
    """Add directives to Sphinx."""
    app.add_directive("linotype", LinotypeDirective)
