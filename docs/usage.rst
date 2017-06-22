Basic Usage
===========
Messages in **liotype** consist of a tree of 'items' of which there are
currently two types, *text* and *definitions*. Every item can contain zero or
more other items, and every level of nested items increases the indentation
level. The **HelpItem** class is used to create a root-level item, and it
accepts a **HelpFormatter** instance which is used to define how items are
formatted. Every **HelpItem** object has public methods for creating new
sub-items which in turn return a new **HelpItem** object. Formatter objects can
be passed in whenever a new item is created, and exising items can be added to
another item using the '+=' operator. Below is an example that prints a simple
help message.

.. code-block:: python
    :linenos:

    from linotype import HelpFormatter, HelpItem

    def help_synopsis():
        formatter = HelpFormatter()
        help_root = HelpItem(formatter)
        help_root.add_definition(
            "zielen", "[global_options] command [command_options] [command_args]",
            "")
        return help_root

    print(help_synopsis().format_help())

The help message can be imported into your Sphinx documentation using the
'linotype' directive. It accepts the following options:

\:func\:
    The name of the function which returns a HelpItem object.

\:module\:
    The name of the module containing the function.

\:filepath\:
    The path of the python file containing the function.

\:no_auto_markup\:
    Do not automatically apply **bold** and *emphasized* formatting to the
    output.

The options :module: and :filepath: are mutually exclusive.

.. code-block:: rst
    :linenos:

    Usage
    =====
    .. linotype::
        :module: zielen.cli
        :func: help_synopsis
