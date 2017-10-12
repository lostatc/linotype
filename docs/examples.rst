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

Configure markup in text output
-------------------------------
The helper function **ansi_format** can be used to generate ANSI escape
sequences to configure the style of markup in the text output.

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
        formatter = Formatter(definition_style=DefinitionStyle.ALIGNED)
        root_item = Item(formatter)

        root_item.add_definition(
            "-q, --quiet", "",
            "Suppress non-error messages.")
        root_item.add_definition(
            "-v, --verbose", "",
            "Increase verbosity.")
        root_item.add_definition(
            "    --info", "FLAGS",
            "Fine-grained informational verbosity.")
        root_item.formatter.definition_style = DefinitionStyle.OVERFLOW
        root_item.add_definition(
            "    --only-write-batch", "FILE",
            "Like --write-batch but without updating dest.")

        return root_item

    print(help_message().format())

This is what the output looks like::

    -q, --quiet       Suppress non-error messages.
    -v, --verbose     Increase verbosity.
        --info FLAGS  Fine-grained informational verbosity.
        --only-write-batch FILE
                      Like --write-batch but without updating dest.

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
            "codot", "[global_options] command [command_args]", "")

        global_opts = root_item.add_text("Global Options:", item_id="global")
        global_opts.add_definition(
            "--help", "", "Print a usage message and exit.")

        return root_item

    print(help_message().format())

This is what your **Sphinx** source file could look like:

.. code-block:: rst
    :linenos:

    SYNOPSIS
    ========
    .. linotype::
        :module: codot.cli
        :function: help_message
        :item_id: usage
        :children:

    DESCRIPTION
    ===========
    codot is a program for consolidating your dotfiles so that settings for
    multiple applications can be modified from one set of files.

    GLOBAL OPTIONS
    ==============
    .. linotype::
        :module: codot.cli
        :function: help_message
        :item_id: global
        :children:

Hide message details
--------------------
To improve readability, you may want to hide certain details in your help
message under certain circumstances. One example would be to have a main help
message that displays an overview of all commands and then a separate help
message with more details for each command. This can be accomplished by:

1. Limiting the number of levels of nested items to descend into.
2. Conditionally making some items invisible via a **Formatter** class.
3. Creating a separate function for the per-command help messages.

The first way is shows below.

.. code-block:: python
    :linenos:

    from linotype import Item

    def help_message():
        root_item = Item()

        commands = root_item.add_text("Commands:")

        add_template_cmd = commands.add_definition(
            "add-template", "[options] files...",
            "Open one or more source files in your editor and save them each "
            "as a template file.", item_id="add-template")
        add_template_cmd.add_definition(
            "-r, --revise", "",
            "If the template file already exists, edit it instead of "
            "creating a new one.")

        role_cmd = commands.add_definition(
            "role", "[role_name [config_name]]",
            "Make config_name the currently selected config file in the role "
            "named role_name.", item_id="role")

        return root_item

    if command:
        print(help_message().format(item_id=command))
    else:
        print(help_message().format(levels=2))
