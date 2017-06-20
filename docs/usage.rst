Basic Usage
===========
Your help message lives in the code and can be formatted as plain text or
imported into your Sphinx documentation. This example shows how to create a
simple usage message and print formatted output.

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
