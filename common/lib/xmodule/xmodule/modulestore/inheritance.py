from datetime import datetime
from pytz import UTC

from xblock.fields import Scope, Boolean, String, Float
from xmodule.fields import Date, Timedelta

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
    for child in descriptor.get_children():
        inherit_metadata(
            child,
            {
                attr: descriptor._field_data.get(descriptor, attr)
                for attr in INHERITABLE_METADATA
                if descriptor._field_data.has(descriptor, attr)
            }
        )
        compute_inherited_metadata(child)


def inherit_metadata(descriptor, inherited_data):
    """
    Updates this module with metadata inherited from a containing module.
    Only metadata specified in self.inheritable_metadata will
    be inherited

    `inherited_data`: A dictionary mapping field names to the values that
        they should inherit
    """
    # The inherited values that are actually being used.
    if not hasattr(descriptor, '_inherited_metadata'):
        setattr(descriptor, '_inherited_metadata', {})

    # All inheritable metadata values (for which a value exists in field_data).
    if not hasattr(descriptor, '_inheritable_metadata'):
        setattr(descriptor, '_inheritable_metadata', {})

    # Set all inheritable metadata from kwargs that are
    # in self.inheritable_metadata and aren't already set in metadata
    for attr in INHERITABLE_METADATA:
        if attr in inherited_data:
            descriptor._inheritable_metadata[attr] = inherited_data[attr]
            if not descriptor._field_data.has(descriptor, attr):
                descriptor._inherited_metadata[attr] = inherited_data[attr]
                descriptor._field_data.set(descriptor, attr, inherited_data[attr])


def own_metadata(module):
    # IN SPLIT MONGO this is just ['metadata'] as it keeps ['_inherited_metadata'] separate!
    # FIXME move into kvs? will that work for xml mongo?
    """
    Return a dictionary that contains only non-inherited field keys,
    mapped to their values
    """
    inherited_metadata = getattr(module, '_inherited_metadata', {})
    metadata = {}
    for field in module.fields.values():
        # Only save metadata that wasn't inherited
        if field.scope != Scope.settings:
            continue

        if not module._field_data.has(module, field.name):
            continue

        if field.name in inherited_metadata and module._field_data.get(module, field.name) == inherited_metadata.get(field.name):
            continue

        try:
            metadata[field.name] = module._field_data.get(module, field.name)
        except KeyError:
            # Ignore any missing keys in _field_data
            pass

    return metadata
