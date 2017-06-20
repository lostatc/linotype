Recipes
=======
Split message into sections
---------------------------
Instead of having your entire help message appear together in your Sphinx
documentation, you may want to split it up into different sections. This can be
accomplished by defining different parts of your help message in different
functions and concatenating them together to be printed.

.. code-block:: python
    :linenos:

    from linotype import HelpFormatter, HelpItem

    def help_synopsis():
        """Return a HelpItem object for the usage section."""

    def help_global_opts():
        """Return a HelpItem object for the global options section."""

    def help_commands():
        """Return a HelpItem object for the commands section."""

    def help_message():
        """Print a combined help message."""
        formatter = HelpFormatter()
        help_root = HelpItem(formatter)

        synopsis = help_root.add_text("Usage:")
        synopsis += help_synopsis()
        synopsis.add_text("\n")

        global_opts = help_root.add_text("Global options:")
        global_opts += help_global_opts()
        global_opts.add_text("\n")

        commands = help_root.add_text("Commands:")
        commands += help_commands()

        print(help_root.format_help())

This is what your Sphinx source file could look like.

.. code-block:: rst
    :linenos:

    SYNOPSIS
    ========
    .. linotype::
        :module: zielen.cli
        :func: help_synopsis

    DESCRIPTION
    ===========
    zielen is a program for conserving disk space by distributing files based
    on how frequently they are accessed.

    GLOBAL OPTIONS
    ==============
    .. linotype::
        :module: zielen.cli
        :func: help_global_opts

    COMMANDS
    ========
    .. linotype::
        :module: zielen.cli
        :func: help_commands

Hide message details
--------------------
To improve readability, you may want to hide certain details in your help
message under certain circumstances. One example would be to have a global help
message that displays an overview of all subcommands and then a more specific
help message for each subcommand. This can be accomplished by limiting the
number of levels of nested items to descend into.

.. code-block:: python
    :linenos:

    from linotype import HelpFormatter, HelpItem

    def help_message(command=None):
        """Print a contextual help message based on the command given."""
        formatter = HelpFormatter()
        help_root = HelpItem(formatter)

        commands = help_root.add_text("Commands:")

        initialize_cmd = commands.add_definition(
            "initialize", "[options] name",
            "Create a new profile, called name, representing a pair of "
            "directories to sync.")
        initialize_cmd.add_definition(
            "-e, --exclude", "file",
            "Get patterns from file representing files and directories to "
            "exclude from syncing.")

        sync_cmd = commands.add_definition(
            "sync", "name|path",
            "Bring the local and remote directories in sync and redistribute "
            "files based on their priorities.")

        if not command:
            print(help_root.format_help(levels=2))
        elif command == "initialize":
            print(initialize_cmd.format_help())
        elif command == "sync":
            print(sync_cmd.format_help())
