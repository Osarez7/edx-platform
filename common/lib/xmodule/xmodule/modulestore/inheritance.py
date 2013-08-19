from datetime import datetime
from pytz import UTC

from xblock.fields import Scope, Boolean, String, Float
from xmodule.fields import Date, Timedelta
from xmodule.x_module import XModuleDescriptor
from xblock.runtime import KeyValueStore

# A list of metadata that this module can inherit from its parent module
INHERITABLE_METADATA = (
    'graded', 'start', 'due', 'graceperiod', 'showanswer', 'rerandomize',
    # TODO (ichuang): used for Fall 2012 xqa server access
    'xqa_key',
    # How many days early to show a course element to beta testers (float)
    # intended to be set per-course, but can be overridden in for specific
    # elements.  Can be a float.
    'days_early_for_beta',
    'giturl',  # for git edit link
    'static_asset_path',       # for static assets placed outside xcontent contentstore
)


class InheritanceMixin(object):
    """Field definitions for inheritable fields"""

    graded = Boolean(
        help="Whether this module contributes to the final course grade",
        default=False,
        scope=Scope.settings
    )

    start = Date(
        help="Start time when this module is visible",
        default=datetime.fromtimestamp(0, UTC),
        scope=Scope.settings
    )
    due = Date(help="Date that this problem is due by", scope=Scope.settings)
    giturl = String(help="url root for course data git repository", scope=Scope.settings)
    xqa_key = String(help="DO NOT USE", scope=Scope.settings)
    graceperiod = Timedelta(
        help="Amount of time after the due date that submissions will be accepted",
        scope=Scope.settings
    )
    showanswer = String(
        help="When to show the problem answer to the student",
        scope=Scope.settings,
        default="finished"
    )
    rerandomize = String(
        help="When to rerandomize the problem",
        default="never",
        scope=Scope.settings
    )
    days_early_for_beta = Float(
        help="Number of days early to show content to beta users",
        default=None,
        scope=Scope.settings
    )
    static_asset_path = String(help="Path to use for static assets - overrides Studio c4x://", scope=Scope.settings, default='')


def compute_inherited_metadata(descriptor):
    """Given a descriptor, traverse all of its descendants and do metadata
    inheritance.  Should be called on a CourseDescriptor after importing a
    course.

    NOTE: This means that there is no such thing as lazy loading at the
    moment--this accesses all the children."""
    if descriptor.has_children:
        parent_metadata = descriptor.xblock_kvs.inherited_settings.copy()
        # add any of descriptor's explicitly set fields to the inheriting list
        for field in INHERITABLE_METADATA:
            # pylint: disable = W0212
            if descriptor._field_data.has(field):
                parent_metadata[field] = descriptor._field_data.get(descriptor, field)

        for child in descriptor.get_children():
            inherit_metadata(child, parent_metadata)
            compute_inherited_metadata(child)


def inherit_metadata(descriptor, inherited_data):
    """
    Updates this module with metadata inherited from a containing module.
    Only metadata specified in self.inheritable_metadata will
    be inherited

    `inherited_data`: A dictionary mapping field names to the values that
        they should inherit
    """
    descriptor.xblock_kvs.inherited_settings = inherited_data

def own_metadata(module):
    """
    Return a dictionary that contains only non-inherited field keys,
    mapped to their values
    """
    return module.get_explicitly_set_fields_by_scope(Scope.settings)

class InheritanceKeyValueStore(KeyValueStore):
    """
    Common superclass for kvs's which know about inheritance of settings. Offers simple
    dict-based storage of fields and lookup of inherited values.
    """
    def __init__(self, initial_values=None, inherited_settings=None):
        super(InheritanceKeyValueStore, self).__init__()
        self._inherited_settings = inherited_settings or {}
        self._fields = initial_values or {}

    @property
    def inherited_settings(self):
        """
        Get the settings set by the ancestors (which locally set fields may override or not)
        """
        return self._inherited_settings

    @inherited_settings.setter
    def inherited_settings(self, dictvalue):
        self._inherited_settings = dictvalue

    def get(self, key):
        return self._fields[key.field_name]

    def set(self, key, value):
        # xml backed courses are read-only, but they do have some computed fields
        self._fields[key.field_name] = value

    def delete(self, key):
        del self._fields[key.field_name]

    def has(self, key):
        return key.field_name in self._fields

    def default(self, key):
        """
        Check to see if the default should be from inheritance rather than from the field's global default
        """
        return self.inherited_settings[key.field_name]
