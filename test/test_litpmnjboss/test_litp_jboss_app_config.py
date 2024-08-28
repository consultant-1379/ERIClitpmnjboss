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
import mock
from litpmnjboss.litp_jboss_app_config import LitpJbossAppConfig
from litpmnjboss import litp_jboss_app_config


class TestLitpJbossAppConfig(unittest.TestCase):
    def setUp(self):
        self.jboss_app_var_names = litp_jboss_app_config.jboss_app_var_names
        self.conf = {
            'LITP_JEE_DE_name': 'jeede2',
            'LITP_JEE_DE_pre_upgrade': '/jboss_app/pre_upgrade.d',
            'LITP_JEE_CONTAINER_process_user': 'user',
        }

    def tearDown(self):
        litp_jboss_app_config.jboss_app_var_names = self.jboss_app_var_names

    def test_jboss_app_config_creation(self):
        litp_jboss_app_config.jboss_app_var_names = ('name',)
        app_config = LitpJbossAppConfig(self.conf)
        expected = {
            'name': self.conf['LITP_JEE_DE_name'],
            'process_user': self.conf['LITP_JEE_CONTAINER_process_user'],
        }
        self.assertEquals(expected, app_config.config)

    def test_jboss_app_config_creation_with_defaults(self):
        litp_jboss_app_config.jboss_app_var_names = ('name',)
        conf = {
            'LITP_JEE_DE_name': 'jeede2',
        }
        app_config = LitpJbossAppConfig(conf)
        expected = {
            'name': conf['LITP_JEE_DE_name'],
            'process_user': 'root',
        }
        self.assertEquals(expected, app_config.config)

    def test_make_env_combines_containers_env_with_own(self):
        container_conf = {
            'TEST_VAR': 'test value',
        }
        container = mock.Mock(env_dict=container_conf)
        app_config = LitpJbossAppConfig(self.conf, container)
        expected = self.conf.copy()
        expected.update(container_conf)  # combined configs
        self.assertEqual(expected, app_config.make_env())

    def test_make_env_without_container(self):
        litp_jboss_app_config.jboss_app_var_names = ('name', 'pre_upgrade')
        app_config = LitpJbossAppConfig(self.conf)
        expected = self.conf.copy()
        self.assertEqual(expected, app_config.make_env())
