"""
Module for code that should run during LMS startup
"""
import logging

from django.conf import settings

# Force settings to run so that the python path is modified
settings.INSTALLED_APPS  # pylint: disable=W0104

from django_startup import autostartup

from lms.xblock.mixin import LmsBlockMixin
from xmodule.modulestore.inheritance import InheritanceMixin

log = logging.getLogger(__name__)

def run():
    """
    Executed during django startup
    """
    autostartup()
    mixins = (LmsBlockMixin, InheritanceMixin)
    for store in settings.MODULESTORE.values():
        store['OPTIONS']['xblock_mixins'] = mixins

    try:
        setup_test_modulestores(mixins)
    except Exception:
        log.exception("Unable to set up test modulestores")

def setup_test_modulestores(mixins):
    from courseware.tests.modulestore_config import (
        TEST_DATA_MONGO_MODULESTORE, TEST_DATA_DRAFT_MONGO_MODULESTORE, TEST_DATA_XML_MODULESTORE, TEST_DATA_MIXED_MODULESTORE
    )

    # Update the test modulestores with the set of active mixins
    for store in TEST_DATA_MONGO_MODULESTORE.values():
        store['OPTIONS']['xblock_mixins'] = mixins
    for store in TEST_DATA_DRAFT_MONGO_MODULESTORE.values():
        store['OPTIONS']['xblock_mixins'] = mixins
    for store in TEST_DATA_XML_MODULESTORE.values():
        store['OPTIONS']['xblock_mixins'] = mixins
    for store in TEST_DATA_MIXED_MODULESTORE.values():
        for substore in store['OPTIONS']['stores'].values():
            substore['OPTIONS']['xblock_mixins'] = mixins
