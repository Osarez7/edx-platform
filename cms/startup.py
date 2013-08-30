"""
Module with code executed during Studio startup
"""
import logging
from django.conf import settings

# Force settings to run so that the python path is modified
settings.INSTALLED_APPS  # pylint: disable=W0104

from django_startup import autostartup
from lms.xblock.mixin import LmsBlockMixin
from cms.xmodule_namespace import CmsBlockMixin
from xmodule.modulestore.inheritance import InheritanceMixin

log = logging.getLogger(__name__)

# TODO: Remove this code once Studio/CMS runs via wsgi in all environments
INITIALIZED = False


def run():
    """
    Executed during django startup
    """
    global INITIALIZED
    if INITIALIZED:
        return

    INITIALIZED = True
    autostartup()

    mixins = (LmsBlockMixin, CmsBlockMixin, InheritanceMixin)
    for store in settings.MODULESTORE.values():
        store['OPTIONS']['xblock_mixins'] = mixins

    try:
        setup_test_modulestores(mixins)
    except Exception:
        log.exception("Unable to set up test modulestores")


def setup_test_modulestores(mixins):
    from contentstore.tests.modulestore_config import TEST_MODULESTORE
    # Update the test modulestores with the set of active mixins
    for store in TEST_MODULESTORE.values():
        store['OPTIONS']['xblock_mixins'] = mixins
