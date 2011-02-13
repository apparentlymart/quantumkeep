# quantumkeep #

quantumkeep is a key-value store with version control. It provides storage
of objects that consist of a heirarchy of key-value pairs, with an
ancestry associated with each object.

quantumkeep uses git to manage storage and versions. At this point it's
really just a toy, but it might be useful to store the content for
a website or blog, or whatever else.

## Data Model ##

quantumkeep has a really simple data model built around immutable dictionaries
with keys that are strings and with values that are either arbitrary strings of
bytes, nested dictionaries, or objects.

An object is a construct that combines a dictionary with authorship and a pointer
to the predecessor object. Objects are also immutable, but you can create a new
object that is a successor of a previous object.

## Short Tutorial ##

### Create and open a store ###

A quantumkeep store is really just a bare git repository, so you can create one
using the standard git command:

    git init --bare teststore

Now you can use this store fom quantumkeep.

    >>> import quantumkeep as qk
    >>> store = qk.Store("teststore")

Note that although a quantumkeep store is a git repository, there are some specific
conventions for data representation in the repository. Therefore using quantumkeep
with a "normal" git repository containing source code may produce some surprising
results and is best avoided unless you know what you're doing.

Objects have authorship information, so we must prepare an Author object to represent
the author of the objects we will subsequently create.

    >>> author = qk.Author("Example Author", "author@example.com")

### Working with objects ###

A new object is created from a dictionary. This dictionary must be a standard
Python dict with a number of additional constraints. Its values can only be dict
or str values or instances of qt.Object. Its keys can only be str values containing
non-whitespace characters. Reference cycles, where one dictionary directly or
indirectly contains itself, are not permitted.

    >>> object = store.create_object({
    ...     "name": "Example Object",
    ... }, author)

A qk object can be read as if it were a dictionary. However, it cannot be written
to because qk objects are immutable.

    >>> object["name"]
    'Example Object'

Each object has a unique identifier that is a hash of its on-disk representation.
We can see this identifier in an object's string representation:

    >>> object
    <qk Object 038d20d23fcb69e8e9a32d09c929c6e8302aefe5 {'name': 'Example Object'}>

A stored object can be looked up later by its identifier:

    >>> store.get_object("038d20d23fcb69e8e9a32d09c929c6e8302aefe5")
    <qk Object 038d20d23fcb69e8e9a32d09c929c6e8302aefe5 {'name': 'Example Object'}>

Since objects are immutable we can't edit this object, but we can create a new
object that becomes a successor of this object by passing in another dictionary:

    >>> new_object = object.create_successor({"name": "Modified Object"}, author)

An object's dictionary can contain other dictionaries or references to other objects.
However, the entire data structure in an object forms the content of the object,
so the entire structure is immutable and any change to a sub-dictionary value,
or referring to a successor of a given object, requires the creation of a successor
object. Therefore in a heirarchy of objects starting from some root object,
a change to the data structure will require a successor to be created not only
of the leaf object but also all of its ancestors.

A given object contains references to the objects from which it succeeds. Normally
this is only one object, but when object merging is implemented in future this
may become two or more objects.

    >>> new_object["name"]
    'Modified Object'
    >>> new_object.predecessors[0]["name"]
    'Example Object'

You can navigate from predecessor to predecessor until you reach the initial incarnation
of the data. Initial objects created with store.create_object do not have any
predecessors, signalling that they are the original incarnation:

    >>> new_object.predecessors[0].predecessors
    []

### Object Aliases ###

Often an application will have one or more objects that serve as entry points into
the data structures it needs. Since creating a successor to an object creates
a new identifier by which that successor is referenced, aliases provide a convenient
way to give a symbolic name to the latest successor of a particular line of objects.

    >>> store.create_object_alias("example_obj", object)
    >>> store.get_object_by_alias("example_obj")
    <qk Object 038d20d23fcb69e8e9a32d09c929c6e8302aefe5 {'name': 'Example Object'}>

Alias are mutable, so when a successor to this object is created the alias can
be updated to refer to the new object:

    >>> store.create_object_alias("example_obj", new_object
    >>> store.get_object_by_alias("example_obj")
    <qk Object ea5320e43d861c828a8463332b895923f88b8778 {'name': 'Modified Object'}>

The alias namespace is heirarchical, using slashes as the namespace delimiter.
Multiple applications sharing one datastore may wish to use this heirarchy
to separate their namespaces.

