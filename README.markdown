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
bytes or nested dictionaries.

An object version is a construct that combines a dictionary with authorship and a pointer
to the predecessor object. Objects versions are also immutable, but you can create a new
version that is a successor of a previous versions.

An object is an association of a persistent identifier to an object version. Objects
are mutable in that a particular identifier can be repointed at different object
versions over time. In the normal case, an object is updated to point at a successor
version of its current version, ensuring that no historical data is ever lost.

A collection is a named bucket of objects. Each collection has a distinct
object identifier namespace, and a particular object can only be in one collection.
Therefore the collection name is effectively part of the object's identifier.

A collection can have zero or more indexes defined. Each index is constructed
using a registered Python function which is called for each object in the collection,
taking the object's current version and returning a string value to record in the index.

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
results and is best avoided unless you know what you're doing. Likewise, you shouldn't
try to use the normal git tools with your quantumkeep store, as you may corrupt it.

Object versions have authorship information, so we must prepare an Author object to represent
the author of the objects we will subsequently create.

    >>> author = qk.Author("Example Author", "author@example.com")

### Selecting a collection ###

All objects exist inside collections. A collection doesn't exist on disk until
its first object is created, but we can get an object referencing it regardless
of whether it exists:

    >>> collection = store.get_collection("example")

Collection names can consist only of letters, digits and underscores.

### Working with objects ###

A new object is created from a dictionary. This dictionary must be a standard
Python dict with a a number of additional constraints: its values can only be dict
or str values, its keys can only be str values containing
non-whitespace characters, and dictionary reference cycles are not permitted.

    >>> object = collection.create_object({
    ...     "name": "Example Object",
    ... }, author)

A qk object can be read as if it were a dictionary. However, it cannot be written
directly because creating a new version is an atomic operation that requires an
explicit action.

    >>> object["name"]
    'Example Object'

Each object has a unique identifier that is a type 4 uuid.
We can see this identifier in an object's string representation:

    >>> object
    <qk Object example:d14150bec5e947e09f3957dc912da0bf {'name': 'Example Object'}>

A stored object can be looked up later by its identifier:

    >>> collection.get_object("d14150bec5e947e09f3957dc912da0bf")
    <qk Object d14150bec5e947e09f3957dc912da0bf {'name': 'Example Object'}>

We can create a new version by passing in a replacement dictionary:

    >>> object.create_new_version({"name": "Modified Object"}, author)

A given object version contains references to the versions from which it succeeds. Normally
this is only one object, but when object merging is implemented in future this
may become two or more objects.

    >>> object["name"]
    'Modified Object'
    >>> object.current_version.previous_versions[0]["name"]
    'Example Object'

You can navigate from version to version until you reach the initial incarnation
of the data. Initial objects created with collection.create_object do not have any
previous versions, signalling that they are the original incarnation:

    >>> object.current_version.previous_versions[0].previous_versions
    []

### Indices ###

QuantumKeep has basic support for indexes, currently backed by the SQLite database
engine. Indexes must be registered on a collection before any objects are created
in that collection; any objects created when the index isn't present will not
be included in the index.

    >>> collection.add_index("status", lambda v : v["status"])
    >>> collection.create_object({"status": "active", "name": "abc"}, author)
    >>> collection.create_object({"status": "inactive", "name": "123"}, author)
    >>> for obj in collection.index("status").objects_matching_value("active"):
    ...    print repr(obj["name"])
    'abc'

