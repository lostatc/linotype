Examples
========
Create two-column options lists
-------------------------------
Many programs display command-line options in a two-column list with the
options and arguments on the left and descriptions on the right. Definition
items with the styles 'inline_aligned' and 'heading_aligned' can be used for
this purpose. The latter style is intended for options that are too long to
otherwise fit.

.. code-block:: python
    :linenos:

    from linotype import HelpFormatter, HelpItem

    def help_message():
        formatter = HelpFormatter()
        help_root = HelpItem(formatter)

        help_root.add_definition(
            "-q, --quiet", "",
            "Suppress non-error messages.",
            style="inline_aligned")
        help_root.add_definition(
            "-v, --verbose", "",
            "Increase verbosity.",
            style="inline_aligned")
        help_root.add_definition(
            "    --info", "FLAGS",
            "Fine-grained informational verbosity.",
            style="inline_aligned")
        help_root.add_definition(
            "    --only-write-batch", "FILE",
            "Like --write-batch but without updating dest.",
            style="heading_aligned")

        return help_root

    print(help_message().format_help())

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
This can be accomplished using item IDs.

.. code-block:: python
    :linenos:

    from linotype import HelpFormatter, HelpItem

    def help_message():
        formatter = HelpFormatter()
        help_root = HelpItem(formatter)

        usage = help_root.add_text("Usage:", item_id="usage")
        usage.add_definition(
            "zielen", "[global_options] command [command_options] [command_args]",
            "")

        global_opts = help_root.add_text("Global Options:", item_id="global_opts")
        global_opts.add_definition(
            "--help", "",
            "Print a usage message and exit.")
        global_opts.add_definition(
            "--version", "",
            "Print the version number and exit.")

        return help_root

    print(help_message().format_help())

This is what your **Sphinx** source file could look like:

.. code-block:: rst
    :linenos:

    SYNOPSIS
    ========
    .. linotype::
        :module: zielen.cli
        :func: help_message
        :item_id: usage
        :children:

    DESCRIPTION
    ===========
    zielen is a program for conserving disk space by distributing files based
    on how frequently they are accessed.

    GLOBAL OPTIONS
    ==============
    .. linotype::
        :module: zielen.cli
        :func: help_message
        :item_id: global_opts
        :children:

Hide message details
--------------------
To improve readability, you may want to hide certain details in your help
message under certain circumstances. One example would be to have a global help
message that displays an overview of all subcommands and then a more specific
help message for each subcommand. This can be accomplished by limiting the
number of levels of nested items to descend into or by making some items
invisible via a HelpFormatter class. The first method is shown below.

.. code-block:: python
    :linenos:

    from linotype import HelpFormatter, HelpItem

    def help_message():
        formatter = HelpFormatter()
        help_root = HelpItem(formatter)

        commands = help_root.add_text("Commands:")

        initialize_cmd = commands.add_definition(
            "initialize", "[options] name",
            "Create a new profile, called name, representing a pair of "
            "directories to sync.",
            item_id="initialize")
        initialize_cmd.add_definition(
            "-e, --exclude", "file",
            "Get patterns from file representing files and directories to "
            "exclude from syncing.")

        sync_cmd = commands.add_definition(
            "sync", "name|path",
            "Bring the local and remote directories in sync and redistribute "
            "files based on their priorities.",
            item_id="sync")

        return help_root

    if command:
        print(help_message().format_help(item_id=command))
    else:
        print(help_message().format_help(levels=2))
