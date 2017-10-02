"""Extend Sphinx to allow importing items into a reStructuredText document.

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
import os
import re
import importlib
import collections
from typing import List, Dict, Tuple, NamedTuple

from docutils import nodes
from docutils.frontend import OptionParser
from docutils.parsers.rst import Directive, Parser
from docutils.parsers.rst.states import Inliner
from docutils.parsers.rst.directives import unchanged, flag

from linotype.items import (
    ARG_REGEX, Item, TextItem, DefinitionItem, MarkupPositions)


def _parse_definition_list(
        def_list_node: nodes.definition_list) -> Dict[str, Tuple[str, str]]:
    """Parse a definition list inside the directive.

    Args:
        def_list_node: A definition list node containing definitions for
            extending the Sphinx output.

    Raises:
        ValueError: The given classifier was unrecognized.

    Returns:
        A dict where keys are item IDs and values are tuples containing
        the classifier and the content as text.
    """
    definitions = {}
    for node in def_list_node:
        if not isinstance(node, nodes.definition_list_item):
            continue

        term_index = node.first_child_matching_class(nodes.term)
        term = node[term_index].astext()

        classifier_index = node.first_child_matching_class(nodes.classifier)
        if classifier_index:
            classifier = node[classifier_index].astext()
        else:
            classifier = "@after"
        if classifier not in ["@replace", "@before", "@after"]:
            raise ValueError("unknown classifier '{0}'".format(classifier))

        # Get the raw text from the Sphinx source file and then remove the
        # first line containing the term and classifier so that just the
        # content is left.
        content_index = node.first_child_matching_class(nodes.definition)
        content = "\n".join(
            node[content_index].parent.rawsource.splitlines()[1:])

        definitions[term] = (classifier, content)

    return definitions


def _extend_item_content(
        definitions: Dict[str, Tuple[str, str]], root_item: Item
        ) -> None:
    """Modify the content of the item tree based on the definitions provided.
    
    Args:
        definitions: A dict where keys are item IDs and values are tuples
            containing the classifier and the content as text.
        root_item: The Item object to be modified in-place.
    """
    for term, (classifier, new_content) in definitions.items():
        item = root_item.get_item_by_id(term, raising=True)
        if isinstance(item, TextItem):
            existing_content = item.content
        elif isinstance(item, DefinitionItem):
            existing_content = item.content[2]
        else:
            continue

        if classifier == "@replace":
            revised_content = new_content
        elif classifier == "@before":
            revised_content = " ".join([new_content, existing_content])
        elif classifier == "@after":
            revised_content = " ".join([existing_content, new_content])

        if isinstance(item, TextItem):
            item.content = revised_content
        if isinstance(item, DefinitionItem):
            item.content[2] = revised_content


def _get_last_matching_child(
        parent_node: nodes.Element, child_class: nodes.Element):
    """Get the last child node that matches a Node subclass.

    Args:
        parent_node: The node to find the child of.
        child_class: The Node subclass to check against.

    Returns:
        The last child Node object that is an instance of the given class.
    """
    for child_node in reversed(parent_node.children):
        if isinstance(child_node, child_class):
            return child_node

class LinotypeDirective(Directive):
    """Convert items into docutils nodes."""
    has_content = True
    required_arguments = 0
    optional_arguments = 0
    option_spec = {
        "module": unchanged,
        "filepath": unchanged,
        "func": unchanged,
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
        if "module" in self.options and "func" in self.options:
            # Import from given module.
            module_name = self.options["module"]
            func_name = self.options["func"]

            try:
                given_module = importlib.import_module(module_name)
            except ImportError:
                raise self.error(
                    "failed to import module '{0}'".format(module_name))

            if not hasattr(given_module, func_name):
                raise self.error("module '{0}' has no attribute '{1}'".format(
                    module_name, func_name))

            func = getattr(given_module, func_name)

        elif "filepath" in self.options and "func" in self.options:
            # Import from given file.
            filepath = self.options["filepath"]
            func_name = self.options["func"]
            local_dict = {}

            file = open(os.path.abspath(filepath))
            code = compile(file.read(), filepath, "exec")
            exec(code, local_dict)

            func = local_dict[func_name]

        else:
            raise self.error(
                "both :func: and either :module: or :filepath: must be "
                "specified.")

        return func()

    def _apply_markup(
            self, text: str, manual_positions: MarkupPositions,
            auto_positions: MarkupPositions) -> List[nodes.Node]:
        """Convert markup to a list of nodes.

        This method supports nested markup.

        Args:
            text: The text to apply markup to.
            manual_positions: The positions of substrings to apply manual
                markup to.
            auto_positions: The positions of substrings to apply auto markup
                to.

        Returns:
            A list of Node objects.
        """
        if manual_positions is None:
            manual_positions = MarkupPositions([], [])

        if auto_positions is None:
            auto_positions = MarkupPositions([], [])

        markup_spans = []
        for markup_type in ["strong", "em"]:
            combined_positions = []

            if "no_manual_markup" not in self.options:
                combined_positions += getattr(manual_positions, markup_type)
            if "no_auto_markup" not in self.options:
                combined_positions += getattr(auto_positions, markup_type)

            # Get the positions of each substring in the string.
            for substring, instance in combined_positions:
                match = list(re.finditer(re.escape(substring), text))[instance]
                markup_spans.append((match.span(), markup_type))

        # Order the spans by their start position.
        markup_spans.sort(key=lambda x: x[0][0])

        def parse_top_level(markup_spans, parent_span):
            # Get top-level spans and include spans without any markup.
            prev_end = parent_span[0]
            top_level_spans = []
            for (start, end), markup_type in markup_spans:
                if start < prev_end or (start, end) == parent_span:
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
                            and (nested_start, nested_end) != parent_span):
                        nested_spans.append(
                            ((nested_start, nested_end), nested_type))

                top_level_nodes[i] += parse_top_level(
                    nested_spans, (start, end))

            return top_level_nodes

        return parse_top_level(markup_spans, (0, len(text)))

    def _parse_item(self, item: Item) -> List[nodes.Node]:
        """Convert an Item object to a docutils Node object.

        Args:
            item: The Item object to convert to a Node object.

        Raises:
            ValueError: The type of the given item was not recognized.

        Returns:
            A Node object.
        """
        if isinstance(item, TextItem):
            # Add a definition node after the paragraph node to act as a
            # starting point for new sub-nodes.
            text = item.content
            if "no_manual_markup" in self.options:
                text_positions = None
            else:
                text, text_positions = item.parse_manual_markup(text)

            node = nodes.paragraph(
                "", "", *self._apply_markup(text, text_positions, None))
        elif isinstance(item, DefinitionItem):
            term, args, msg = item.content
            if "no_manual_markup" in self.options:
                term_positions = args_positions = msg_positions = None
            else:
                term, term_positions = item.parse_manual_markup(term)
                args, args_positions = item.parse_manual_markup(args)
                msg, msg_positions = item.parse_manual_markup(msg)

            auto_term_positions = item.parse_term_markup(term)
            auto_args_positions = item.parse_args_markup(args)
            auto_msg_positions = item.parse_msg_markup(args, msg)

            node = nodes.definition_list_item(
                    "", nodes.term(
                        "", "", *self._apply_markup(
                            term, term_positions, auto_term_positions),
                        nodes.Text(" "),
                        *self._apply_markup(
                            args, args_positions, auto_args_positions)),
                    nodes.definition(
                        "", nodes.paragraph(
                            "", "", *self._apply_markup(
                                msg, msg_positions, auto_msg_positions))))
        else:
            raise ValueError("unrecognized item type '{0}'".format(type(item)))

        return node

    def _parse_tree(self, root_item: Item) -> List[nodes.Node]:
        """Convert a tree of Item objects to a tree of Node objects.
        
        Docutils definitions are used for indentation.

        Args:
            root_item: The Item object to convert to a tree of docutils
                Node objects.

        Returns:
            The list of Node objects that make up the root of the tree.
        """
        root_node = nodes.section()
        parent_node = root_node
        previous_level = root_item.current_level

        if type(root_item) is not Item:
            if root_item.parent:
                # The root item is to be included in the output.
                if isinstance(root_item, DefinitionItem):
                    definition_list = nodes.definition_list()
                    definition_list.append(self._parse_item(root_item))
                    root_node.append(definition_list)
                else:
                    root_node.append(self._parse_item(root_item))
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
                    definition_list = _get_last_matching_child(
                        parent_node, nodes.definition_list)
                    definition_list_item = _get_last_matching_child(
                        definition_list, nodes.definition_list_item)
                    definition = _get_last_matching_child(
                        definition_list_item, nodes.definition)
                    parent_node = definition
            elif item.current_level < previous_level:
                # The indentation level decreased.
                for i in range(previous_level - item.current_level):
                    new_parent = ancestor_nodes.pop()
                parent_node = new_parent

            if isinstance(item, DefinitionItem):
                # Wrap definitions in a definition_list.
                if not parent_node.children or not isinstance(
                        parent_node[-1], nodes.definition_list):
                    parent_node.append(nodes.definition_list())
                parent_node[-1].append(self._parse_item(item))
            else:
                parent_node.append(self._parse_item(item))
                
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

        # Parse directive and extend item content.
        nested_nodes = nodes.paragraph()
        self.state.nested_parse(
            self.content, self.content_offset, nested_nodes)
        def_list_index = nested_nodes.first_child_matching_class(
            nodes.definition_list)
        if def_list_index is not None:
            definitions = _parse_definition_list(nested_nodes[def_list_index])
            _extend_item_content(definitions, root_item)

        return self._parse_tree(root_item)


def setup(app) -> None:
    """Add directives to Sphinx."""
    app.add_directive("linotype", LinotypeDirective)