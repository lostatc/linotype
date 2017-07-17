Usage
=====
Messages in **linotype** consist of a tree of 'items' of which there are
currently two types, *text* and *definitions*. Every item can contain zero or
more other items, and every level of nested items increases the indentation
level. The **RootItem** class is used to create a root-level item, and every
**RootItem** object has public methods for creating new sub-items which in turn
return a new **RootItem** object.

Every **RootItem** object accepts a **Formatter** instance which is used to
define how items are formatted in the text output. Items can be assigned IDs
that can be referenced in the **Sphinx** documentation. Here is an example that
prints a simple help message:

.. code-block:: python
    :linenos:

    from linotype import Formatter, RootItem

    def help_message():
        formatter = Formatter()
        help_root = RootItem(formatter)
        usage = help_root.add_text("Usage:")
        usage.add_definition(
            "zielen", "[global_options] command [command_options] [command_args]",
            "")
        return help_root

    print(help_message().format())

Line wrapping, indentation, alignment and markup are all applied automatically
according to attributes set in the **Formatter** object. Additionally, inline
'strong' and 'emphasized' markup can be applied manually using the
reStructuredText syntax::

    This text is **strong**.
    This text is *emphasized*.

----

To use **linotype** with **Sphinx**, you must first add 'linotype.ext' to the
list of **Sphinx** extensions in the *conf.py* file for your project:

.. code-block:: python

    extensions = ["linotype.ext"]

The help message can be imported into your **Sphinx** documentation using the
'linotype' directive. It accepts the following options:

\:func\:
    The name of the function which returns a **RootItem** object.

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
    Do not automatically apply **strong** and *emphasized* formatting to the
    output.

\:no_manual_markup\:
    Do not parse reStructuredText inline markup.

The options :module: and :filepath: are mutually exclusive. The options :func:
and either :module: or :filepath: are required.

Using the 'linotype' directive, you can extend or replace parts of your help
message. This allows you to add new content that appears in your **Sphinx**
documentation but not in your text output. This is done on a per-item basis
using a reStructuredText definition list, where the term is the ID of an item
and the definition is the new text to use. You can also add a classifier, which
changes how the new text is incorporated:

@before
    Insert the new text before the existing text.

@after
    Insert the new text after the existing text. This is the default.

@replace
    Replace the existing text with the new text.

Here is an example of a **Sphinx** source file using the directive:

.. code-block:: rst
    :linenos:

    .. linotype::
        :module: zielen.cli
        :func: help_message

        initialize
            This text is inserted after the existing text for the item with the
            ID 'initialize.'

        sync : @replace
            This text replaces the existing text for the item with the ID
            'sync.'
