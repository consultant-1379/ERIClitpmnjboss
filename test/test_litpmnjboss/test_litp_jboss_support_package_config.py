##############################################################################
# COPYRIGHT Ericsson AB 2013,2014
#
# The copyright to the computer program(s) herein is the property of
# Ericsson AB. The programs may be used and/or copied only with written
# permission from Ericsson AB. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
##############################################################################

import unittest
from litpmnjboss.litp_jboss_support_package_config import (
    LitpJbossSupportPackageConfig)
from litpmnjboss import litp_jboss_support_package_config as sp_config


class TestLitpJbossSupportPackageConfig(unittest.TestCase):
    def setUp(self):
        self.jboss_app_var_names = sp_config.jboss_app_var_names

    def tearDown(self):
        sp_config.jboss_app_var_names = self.jboss_app_var_names

    def test_jboss_app_config_creation(self):
        sp_config.jboss_app_var_names = ('name',)
        conf = {
            'LITP_JEE_DE_name': 'jeede2',
            'LITP_JEE_SP_name': 'sp_name',
            'LITP_JEE_SP_other': 'other',
        }
        app_config = LitpJbossSupportPackageConfig(conf)
        expected = {
            'name': conf['LITP_JEE_SP_name'],
        }
        self.assertEquals(expected, app_config.config)
