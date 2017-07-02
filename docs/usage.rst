Basic Usage
===========
Messages in **liotype** consist of a tree of 'items' of which there are
currently two types, *text* and *definitions*. Every item can contain zero or
more other items, and every level of nested items increases the indentation
level. The **HelpItem** class is used to create a root-level item, and it
accepts a **HelpFormatter** instance which is used to define how items are
formatted. Every **HelpItem** object has public methods for creating new
sub-items which in turn return a new **HelpItem** object. Below is an example
that prints a simple help message.

.. code-block:: python
    :linenos:

    from linotype import HelpFormatter, HelpItem

    def help_message():
        formatter = HelpFormatter()
        help_root = HelpItem(formatter)
        usage = help_root.add_text("Usage:")
        usage.add_definition(
            "zielen", "[global_options] command [command_options] [command_args]",
            "")
        return help_root

    print(help_message().format_help())

To use **linotype** with **Sphinx**, you must first add 'linotype.ext' to the
list of **Sphinx** extensions in the *conf.py* file for your project. The help
message can be imported into your **Sphinx** documentation using the 'linotype'
directive. It accepts the following options:

\:func\:
    The name of the function which returns a HelpItem object.

\:module\:
    The name of the module containing the function.

\:filepath\:
    The path of the python file containing the function.

\:item_id\:
    The ID of an item in the tree returned by the function. The output is
    restricted to just this item and its children.

\:children\:
    Display the item's children but not the item itself.

\:no_auto_markup\:
    Do not automatically apply **bold** and *emphasized* formatting to the
    output.

The options :module: and :filepath: are mutually exclusive. The options :func:
and either :module: or :filepath: are required.

Here is an example of a **Sphinx** source file using the directive:

.. code-block:: rst
    :linenos:

    SYNOPSIS
    ========
    .. linotype::
        :module: zielen.cli
        :func: help_message
