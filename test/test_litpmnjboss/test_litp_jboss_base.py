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
from litpmnjboss.litp_jboss_base import LitpJbossBase


class TestLitpJbossBase(unittest.TestCase):

    def setUp(self):
        self.conf = {
            'LITP_test_key': 'test value 1',
            'other_test_key': 'test value 2',
            'TEST_ENV_PATH': '/usr/bin',
            'TEST_ENV_VARIABLE': 'test_123'
        }
        self.jboss_base = LitpJbossBase(self.conf)

    def test_jboss_base_initiates_env_and_litp_dicts(self):
        self.assertEqual('test value 1',
                         self.jboss_base.litp_dict['LITP_test_key'])
        self.assertEqual('test value 2',
                         self.jboss_base.env_dict['other_test_key'])

    def test_make_env(self):
        self.assertEqual(self.conf, self.jboss_base.make_env())

    def test_get(self):
        self.jboss_base.config['test_key'] = 'test value'
        self.assertEqual('test value', self.jboss_base.get('test_key'))
