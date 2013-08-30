"""
:class:`~xblock.fields.FieldData` subclasses used by the LMS
"""

from xblock.fields import FieldData, UNSET, Scope
from xblock.exceptions import InvalidScopeError


class SplitFieldData(FieldData):
    """
    A FieldData that uses divides particular scopes between
    several backing FieldData objects.
    """

    def __init__(self, scope_mappings):
        """
        `scope_mappings` defines :class:`~xblock.fields.FieldData` objects to use
        for each scope. If a scope is not a key in `scope_mappings`, then using
        a field of that scope will raise an :class:`~xblock.exceptions.InvalidScopeError`

        :param scope_mappings: A map from Scopes to backing FieldData instances
        :type scope_mappings: `dict` of :class:`~xblock.fields.Scope` to :class:`~xblock.fields.FieldData`
        """
        self._scope_mappings = scope_mappings

    def _field_data(self, block, name):
        scope = block.fields[name].scope

        if scope not in self._scope_mappings:
            raise InvalidScopeError(scope)

        return self._scope_mappings[scope]

    def get(self, block, name, default=UNSET):
        return self._field_data(block, name).get(block, name, default)

    def set(self, block, name, value):
        self._field_data(block, name).set(block, name, value)

    def delete(self, block, name):
        self._field_data(block, name).delete(block, name)

    def has(self, block, name):
        return self._field_data(block, name).has(block, name)


class ReadOnlyFieldData(FieldData):
    """
    A Field data that wraps another FieldData an makes all calls to set and delete
    raise :class:`~xblock.exceptions.InvalidScopeError`s
    """
    def __init__(self, source):
        self._source = source

    def get(self, block, name, default=UNSET):
        return self._source.get(block, name, default)

    def set(self, block, name, value):
        raise InvalidScopeError("{block}.{name} is read-only, cannot set".format(block=block, name=name))

    def delete(self, block, name):
        raise InvalidScopeError("{block}.{name} is read-only, cannot delete".format(block=block, name=name))

    def has(self, block, name):
        return self._source.has(block, name)


def lms_field_data(authored_data, student_data):
    """
    Returns a new :class:`~xblock.fields.FieldData` that
    reads all UserScope.ONE and UserScope.ALL fields from `student_data`
    and all UserScope.NONE fields from `authored_data`. It also prevents
    writing to `authored_data`.
    """
    authored_data = ReadOnlyFieldData(authored_data)
    return SplitFieldData({
        Scope.content: authored_data,
        Scope.settings: authored_data,
        Scope.parent: authored_data,
        Scope.children: authored_data,
        Scope.user_state_summary: student_data,
        Scope.user_state: student_data,
        Scope.user_info: student_data,
        Scope.preferences: student_data,
    })
