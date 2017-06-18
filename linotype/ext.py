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
from typing import List

from docutils import nodes
from docutils.parsers.rst import Directive
from docutils.parsers.rst.directives import unchanged, flag

from linotype.formatter import ARG_REGEX
from linotype.formatter import HelpItem


class LinotypeDirective(Directive):
    """Convert items into docutils nodes."""
    has_content = True
    required_arguments = 0
    optional_arguments = 0
    option_spec = {
        "module": unchanged,
        "filepath": unchanged,
        "func": unchanged,
        "no_auto_markup": flag}

    def _get_help_item(self) -> HelpItem:
        """Get the HelpItem object from the given module or file."""
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

    def _markup_args(self, args_string: str) -> List[nodes.Node]:
        """Make argument names in the input string emphasized.

        Returns:
            A list of 'emphasis' and 'Text' nodes.
        """
        if "no_auto_markup" in self.options:
            return [nodes.Text(args_string)]
        else:
            output_nodes = []
            for string in ARG_REGEX.split(args_string):
                if ARG_REGEX.search(string):
                    output_nodes.append(nodes.emphasis(text=string))
                else:
                    output_nodes.append(nodes.Text(string))
            return output_nodes

    def _markup_name(self, name_string: str) -> nodes.Node:
        """Make the input string strong.

        Returns:
            A 'strong' or 'Text' node.
        """
        if "no_auto_markup" in self.options:
            return nodes.Text(name_string)
        else:
            return nodes.strong(text=name_string)

    def _sub_args(self, args: str, text: str) -> List[nodes.Node]:
        """Search a string for arguments and add markup.

        This method only formats arguments surrounded by non-word characters.

        Args:
            text: The string to have markup added to.
            args: The argument string to get arguments from.

        Returns:
            The given text with markup added.
        """
        if "no_auto_markup" in self.options or not args:
            return [nodes.Text(text)]
        else:
            output_nodes = []
            arg_regex = re.compile(
                r"(?<!\w)({})(?!\w)".format("|".join(
                    re.escape(arg) for arg in ARG_REGEX.findall(args))))
            for string in arg_regex.split(text):
                if arg_regex.search(string):
                    output_nodes.append(nodes.emphasis(text=string))
                else:
                    output_nodes.append(nodes.Text(string))

            return output_nodes

    def _parse_item(self, item: HelpItem) -> nodes.Node:
        """Convert a HelpItem object to a docutils node.

        Returns:
            A node object.
        """
        if item._type == "text":
            node = nodes.paragraph(text=item._content)
        elif item._type == "definition":
            name, args, msg = item._content
            signature = [nodes.strong(text=name)] + self._markup_args(args)
            node = nodes.definition_list(
                "", nodes.definition_list_item(
                    "", nodes.term(
                        "", "", self._markup_name(name), nodes.Text(" "),
                        *self._markup_args(args)),
                    nodes.definition(
                        "", nodes.paragraph(
                            "", "", *self._sub_args(args, msg)))))
        else:
            raise ValueError("unrecognized item type '{0}'".format(item._type))

        return node

    def _parse_tree(self, help_item: HelpItem) -> nodes.Node:
        """Recursively iterate over a HelpItem object to generate nodes.

        Args:
            help_item: The HelpItem object to convert to a tree of docutils
                nodes.
        """
        node = self._parse_item(help_item)
        for item in help_item._items:
                node += self._parse_tree(item)
        return node

    def run(self) -> List[nodes.Node]:
        """Convert a HelpItem object to a docutils node tree.

        Returns:
            A list of node objects.
        """
        help_item = self._get_help_item()
        if help_item._type is None:
            # Exclude the empty root-level item.
            help_items = help_item._items
        else:
            help_items = [help_item]

        return [self._parse_tree(item) for item in help_items]


def setup(app) -> None:
    """Add directives to Sphinx."""
    app.add_directive("linotype", LinotypeDirective)
