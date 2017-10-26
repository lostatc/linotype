Examples
========
Add blank lines
---------------
A blank line can be added to your text output using a *text* item containing a
newline character.

.. code-block:: python
    :linenos:

    from linotype import Item

    def help_message():
        root_item = Item()

        root_item.add_text("This line comes before the break.")
        root_item.add_text("\n")
        root_item.add_text("This line comes after the break.")

        return root_item

Configure markup in text output
-------------------------------
The helper function :func:`linotype.ansi_format` can be used to generate ANSI
escape sequences to configure the style of markup in the text output.

.. code-block:: python
    :linenos:

    from linotype import ansi_format, Formatter, Item

    def help_message():
        formatter = Formatter(
            strong=ansi_format(fg="red", bold=True),
            em=ansi_format(fg="green", bold=True))
        root_item = Item(formatter)

        root_item.add_text("This text has **strong** and *emphasized* markup.")

        return root_item

    print(help_message().format())

Create two-column options lists
-------------------------------
Many programs display command-line options in a two-column list with the
options and arguments on the left and descriptions on the right. *Definition*
items with the styles ALIGNED and OVERFLOW can be used for this purpose. The
latter style is intended for options that are too long to otherwise fit.

.. code-block:: python
    :linenos:

    from linotype import DefinitionStyle, Formatter, Item

    def help_message():
        aligned_formatter = Formatter(definition_style=DefinitionStyle.ALIGNED)
        overflow_formatter = Formatter(definition_style=DefinitionStyle.OVERFLOW)

        root_item = Item(aligned_formatter)

        root_item.add_definition(
            "-q, --quiet", "", "Suppress all non-error output.")
        root_item.add_definition(
            "-v, --verbose", "", "Increase verbosity.")
        root_item.add_definition(
            "    --debug", "",
            "Print a full stack trace instead of an error message if an error "
            "occurs.")
        root_item.add_definition(
            "    --from-file", "path",
            "Use the list from the file located at path.",
            formatter=overflow_formatter)

        return root_item

    print(help_message().format())

This is what the output looks like::

    -q, --quiet    Suppress all non-error output.
    -v, --verbose  Increase verbosity.
        --debug    Print a full stack trace instead of an error message if an
                       error occurs.
        --from-file path
                   Use the list from the file located at path.

Split message into sections
---------------------------
Instead of having your entire help message appear in one place in your
**Sphinx** documentation, you may want to split it up into different sections.
This can be accomplished by assigning item IDs.

.. code-block:: python
    :linenos:

    from linotype import Item

    def help_message():
        root_item = Item()

        usage = root_item.add_text("Usage:", item_id="usage")
        usage.add_definition(
            "todo", "[global_options] command [command_args]", "")

        global_opts = root_item.add_text("Global Options:", item_id="global")
        global_opts.add_definition(
            "-q, --quiet", "", "Suppress all non-error output.")

        return root_item

    print(help_message().format())

This is what your **Sphinx** source file could look like:

.. code-block:: rst
    :linenos:

    SYNOPSIS
    ========
    .. linotype::
        :module: todo.cli
        :function: help_message
        :item_id: usage
        :children:

    GLOBAL OPTIONS
    ==============
    .. linotype::
        :module: todo.cli
        :function: help_message
        :item_id: global
        :children:

Hide message details
--------------------
To improve readability, you may want to only show certain details in your help
message under certain circumstances. One example would be to have a main help
message that displays an overview of all commands and then a separate help
message with more details for each command. This can be accomplished by:

1. Limiting the number of levels of nested items to descend into (see
   :meth:`linotype.Item.format`).
2. Conditionally making some items invisible via a :class:`linotype.Formatter`
   class.
3. Creating a separate function for the per-command help messages.

The third method is shown below.

.. code-block:: python
    :linenos:

    from linotype import Item

    def main_help_message():
        root_item = Item()

        commands = root_item.add_text("Commands:")
        commands.add_definition(
            "check", "[options] tasks...",
            "Mark one or more tasks as completed.")

        return root_item

    def command_help_message():
        root_item = Item()

        check = root_item.add_definition(
            "check", "[options] tasks...",
            "Mark one or more tasks as completed. These will appear hidden in "
            "the list.", item_id="check")
        check.add_definition(
            "-r, --remove", "", "Remove the tasks from the list.")

        return root_item

    if command:
        print(command_help_message().format(item_id=command))
    else:
        print(main_help_message().format())
