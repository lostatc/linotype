Usage
=====
Documentation in **linotype** consists of a tree of 'items' of which there are
currently two types, *text* and *definitions*. Every item can contain other
items which are indented relative to the parent item. The
:class:`linotype.Item` class is used to create a root-level item, and every
:class:`linotype.Item` object has public methods for creating new sub-items
which in turn return a new :class:`linotype.Item` object.

Every :class:`linotype.Item` object accepts a :class:`linotype.Formatter`
instance which is used to define how items are formatted in the text output.
Every item can optionally be assigned an ID that can be referenced in the
**Sphinx** documentation or when formatting the text output. Here is an example
that prints a simple help message:

.. code-block:: python
    :linenos:

    from linotype import Item

    def help_message():
        root_item = Item()

        usage = root_item.add_text("Usage:")
        usage.add_definition(
            "codot", "[global_options] command [command_args]", "")

        return root_item

    print(help_message().format())

Line wrapping, indentation, alignment and markup are all applied automatically
according to attributes set in the :class:`linotype.Formatter` object, so all
text is passed into **linotype** as unformatted, single-line strings.
Additionally, inline 'strong' and 'emphasized' markup can be applied manually
using the reStructuredText syntax::

    This text is **strong**.
    This text is *emphasized*.

----

To use **linotype** with **Sphinx**, you must first add 'linotype.ext' to the
list of **Sphinx** extensions in the *conf.py* file for your project:

.. code-block:: python

    extensions = ["linotype.ext"]

The documentation can be imported into your **Sphinx** documentation using the
'linotype' directive. It accepts the following options:

\:function\:
    The name of the function which returns a :class:`linotype.Item` object.

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
    Do not automatically apply 'strong' and 'emphasized' formatting to the
    output.

\:no_manual_markup\:
    Do not parse 'strong' and 'emphasized' inline markup.

The options :module: and :filepath: are mutually exclusive. The options
:function: and either :module: or :filepath: are required.

Using the 'linotype' directive, you can extend or replace parts of your help
message. This allows you to add new content that appears in your **Sphinx**
documentation but not in your text output. This is done on a per-item basis
using a reStructuredText definition list, where the term is the ID of an item
and the definition is the new content to use. You can also add classifiers,
which change how the new content is incorporated.

These classifiers affect where the content is added:

@after
    The new content is added after the existing content. This is the default.

@before
    The new content is added before the existing content.

@replace
    The new content replaces the existing content.

These classifiers affect how markup is applied to the content:

@auto
    Markup is applied to the text automatically, and 'strong' and 'emphasized'
    inline markup can be applied manually. This is the default.

@rst
    Markup is not applied automatically, but any reStructuredText body or
    inline elements can be used. The new content starts in a separate
    paragraph.

Here is an example of a **Sphinx** source file using the directive:

.. code-block:: rst
    :linenos:

    .. linotype::
        :module: codot.cli
        :function: help_message

        add-template
            This content is added after the existing content for the item with
            the ID 'add-template.' Markup is applied automatically.

        add-template : @before : @rst
            This content is added before the existing content for the item with
            the ID 'add-template.' reStrcturedText elements can be used.

        role : @replace
            This content replaces the existing content for the item with the ID
            'role.' Markup is applied automatically.
