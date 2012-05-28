
from quantumkeep.schema import PrimitiveType

__all__ = ["ValueConflict", "value_diff"]


class ValueConflict(Exception):
    pass


class NoDifference(Exception):
    pass


class BaseDiff(object):
    """
    Abstract base class of all diff implementations. This implementation
    does nothing and applies to nothing, so you can't actually use it
    as a diff strategy.
    """

    key = None

    def __init__(self, value_type, old_value, new_value):
        """
        Initialize an instance based on the provided type and old and new
        values. This is where the implementation will figure out what the
        difference is between the two. Raise :py:class:`NoDifference` if
        there is no difference between the two as far as this differ is
        concerned.
        """
        pass

    def __call__(self, apply_value):
        """
        Given a a value, apply the diff represented by this instance
        to that value, returning a new value. If the
        diff cannot be applied to the given value, raise
        :py:class:`ValueConflict` to indicate this.
        """
        return (apply_type, apply_value)

    @classmethod
    def can_derive_for_type(self, value_type):
        """
        Called to determine if a diff of this type can be derived from a pair
        of values of the given type. Return ``True`` if so, and ``False`` if
        not. A diff implementation will never be called to produce a diff
        between two values of types for which this method returns ``False``.
        """
        return False


class ReplaceDiff(object):
    """
    Represents the wholesale replacement of a value. Will raise a conflict
    on application against a value other than the source value of the diff.
    """
    def __init__(self, value_type, old_value, new_value):
        if old_value == new_value:
            raise NoDifference()
        self.old_value = old_value
        self.new_value = new_value

    def __call__(self, apply_value):
        if apply_value == self.old_value:
            return self.new_value
        else:
            raise ValueConflict("Old value does not match")

    @classmethod
    def can_derive_for_type(self, value_type):
        # This kind of diff applies to any type.
        return True

    def __repr__(self):
        return "<replace %r with %r>" % (self.old_value, self.new_value)


class NumericSumDiff(object):
    """
    Represents adding a (possibly negative) number to another number. Treats
    a ``None`` as a zero for the purposes of comparing and applying on the
    old value.
    """
    def __init__(self, value_type, old_value, new_value):
        self.diff = new_value - old_value
        if self.diff == 0:
            raise NoDifference()

    def __call__(self, apply_value):
        return apply_value + self.diff

    @classmethod
    def can_derive_for_type(self, value_type):
        return (value_type in (PrimitiveType.integer, PrimitiveType.float))

    def __repr__(self):
        if self.diff > 0:
            return "<add %r>" % self.diff
        if self.diff < 0:
            return "<subtract %r>" % -self.diff


differs = {
    "replace": ReplaceDiff,
    "numeric_sum": NumericSumDiff,
}


class value_diff(object):
    @classmethod
    def get_by_name(cls, name):
        return differs[name]


for differ_key, differ in differs.iteritems():
    setattr(differ, "key", differ_key)
    setattr(value_diff, differ_key, differ)
