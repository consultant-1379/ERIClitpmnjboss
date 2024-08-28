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
from litpmnjboss.litp_jboss_config import LitpJbossConfig
from litpmnjboss import litp_jboss_config


class TestLitpJbossConfig(unittest.TestCase):
    def setUp(self):
        self.jboss_var_names = litp_jboss_config.jboss_var_names
        self.LITP_JBOSS_DATA_DIR = litp_jboss_config.LITP_JBOSS_DATA_DIR
        self.jboss_config = LitpJbossConfig({})

    def tearDown(self):
        litp_jboss_config.jboss_var_names = self.jboss_var_names
        litp_jboss_config.LITP_JBOSS_DATA_DIR = self.LITP_JBOSS_DATA_DIR

    def test_selected_vars_set_in_config(self):
        # limit vars acceptable in config to this
        litp_jboss_config.jboss_var_names = ('home_dir',)
        conf = {
            'LITP_JEE_CONTAINER_data_dir': "/tmp/jboss/sg1_su1_jboss",
            'LITP_JEE_CONTAINER_home_dir': "/tmp/jboss/sg1_su1_jboss",
        }
        jboss_config = LitpJbossConfig(conf)
        expected = {'home_dir': "/tmp/jboss/sg1_su1_jboss"}
        self.assertEquals(expected, jboss_config.config)

    def test_generating_config_dir_path(self):
        conf = {'LITP_JEE_CONTAINER_instance_name': 'jee1'}
        jboss_config = LitpJbossConfig(conf)
        expected = litp_jboss_config.LITP_JBOSS_DATA_DIR + 'jee1'
        self.assertEquals(expected, jboss_config.config_dir)

    def test_generating_jboss_cli_command_string_with_defaults(self):
        litp_jboss_config.jboss_var_names = ('home_dir',
                                             'management_listener',
                                             'management_port_native',
                                             'port_offset')
        # let jboss_config handle missing values
        conf = {
            'LITP_JEE_CONTAINER_home_dir': "/jboss",
        }
        jboss_config = LitpJbossConfig(conf)
        expected = ('/jboss/bin/jboss-cli.sh '
                    'controller=127.0.0.1:0')
        self.assertEquals(expected, jboss_config.env_dict['JBOSS_CLI'])

        # let jboss_config handle default values
        conf = {
            'LITP_JEE_CONTAINER_home_dir': "/jboss",
            'LITP_JEE_CONTAINER_management_listener': '0.0.0.0',
            'LITP_JEE_CONTAINER_management_port_native': '0',
            'LITP_JEE_CONTAINER_port_offset': '0',
        }
        jboss_config = LitpJbossConfig(conf)
        self.assertEquals(expected, jboss_config.env_dict['JBOSS_CLI'])

    @mock.patch('litpmnjboss.litp_jboss_config.IPy.IP')
    def test_generating_jboss_cli_command_string_with_non_defaults(self, IP):
        litp_jboss_config.jboss_var_names = ('home_dir',
                                             'management_listener',
                                             'management_port_native',
                                             'port_offset')
        conf = {
            'LITP_JEE_CONTAINER_home_dir': "/jboss",
            'LITP_JEE_CONTAINER_management_listener': '192.168.23.12',
            'LITP_JEE_CONTAINER_management_port_native': '1234',
            'LITP_JEE_CONTAINER_port_offset': '1',
        }
        #TODO test IPv6 as well
        IP.return_value = mock.Mock(_ipversion=4)
        jboss_config = LitpJbossConfig(conf)
        expected = ('/jboss/bin/jboss-cli.sh '
                    'controller=192.168.23.12:1235')
        self.assertEquals(expected, jboss_config.env_dict['JBOSS_CLI'])

    def test_no_apps_created_if_de_count_is_zero(self):
        conf = {'LITP_DE_COUNT': '0'}
        jboss_config = LitpJbossConfig(conf)
        self.assertEquals(0, len(jboss_config.apps))

    def test_no_apps_created_if_de_count_undefined(self):
        jboss_config = LitpJbossConfig({})
        self.assertEquals(0, len(jboss_config.apps))

    @mock.patch('litpmnjboss.litp_jboss_config.LitpJbossAppConfig')
    def test_single_app_creation(self, app_config):
        conf = {
            'LITP_DE_COUNT': '1',
            'LITP_DE_0_JEE_DE_name': 'jeede1',
        }
        jboss_config = LitpJbossConfig(conf)
        self.assertEquals(1, len(jboss_config.apps))
        expected = {
            'LITP_JEE_DE_name': 'jeede1',
        }
        app_config.assert_called_once_with(expected,
                                           container=jboss_config)
        # see if the app conf class was appended to apps list
        self.assertEquals(app_config().name, jboss_config.apps[0].name)

    #TODO test adding multiple apps

    def test_no_support_package_created_if_sp_count_is_zero(self):
        conf = {'LITP_SP_COUNT': '0'}
        jboss_config = LitpJbossConfig(conf)
        self.assertEquals(0, len(jboss_config.support_packages))

    def test_no_support_package_created_if_sp_count_is_undefined(self):
        jboss_config = LitpJbossConfig({})
        self.assertEquals(0, len(jboss_config.support_packages))

    @mock.patch('litpmnjboss.litp_jboss_config.LitpJbossSupportPackageConfig')
    def test_single_service_package_creation(self, sp_config):
        conf = {
            'LITP_SP_COUNT': '1',
            'LITP_SP_0_JEE_SP_name': 'sp1',
            'LITP_SP_0_JEE_SP_version': '1.0.1',
            'LITP_SP_0_JEE_SP_install_source': '/tmp/sp1.tgz',
            'LITP_OTHER': 'value other',
        }
        expected_sp_conf = {
            'LITP_JEE_SP_name': 'sp1',
            'LITP_JEE_SP_version': '1.0.1',
            'LITP_JEE_SP_install_source': '/tmp/sp1.tgz',
            'LITP_OTHER': 'value other',
        }
        jboss_config = LitpJbossConfig(conf)
        self.assertEquals(1, len(jboss_config.support_packages))
        sp_config.assert_called_once_with(expected_sp_conf,
                                          container=jboss_config)
        # see if the app conf class was appended to apps list
        self.assertEquals(sp_config().name,
                          jboss_config.support_packages[0].name)
        expected = {
            'LITP_SP_COUNT': '1',
            'LITP_SP_0_JEE_SP_name': 'sp1',
            'LITP_SP_0_JEE_SP_version': '1.0.1',
            'LITP_SP_0_JEE_SP_install_source': '/tmp/sp1.tgz',
        }
        # check sp_dict
        self.assertEquals(expected, jboss_config.sp_dict)

    @mock.patch('litpmnjboss.litp_jboss_config.json')
    @mock.patch('__builtin__.open')
    @mock.patch('litpmnjboss.litp_jboss_config.common')
    def test_save_config_fails_creating_config_dir_and_throws_error(
            self, jboss_common, open, json):
        jboss_common.make_directory.side_effect = OSError()
        jboss_config = LitpJbossConfig({})
        jboss_config.config_dir = '/tmp'
        self.assertRaises(OSError, jboss_config.save_config)

    @mock.patch('litpmnjboss.litp_jboss_config.json')
    @mock.patch('__builtin__.open')
    @mock.patch('litpmnjboss.litp_jboss_config.common')
    def test_save_config_fails_to_create_config_file(self, jboss_common,
                                                     _open, json):
        jboss_config = LitpJbossConfig({})
        jboss_config.config_dir = '/tmp'
        _open.side_effect = IOError('file saving error')
        self.assertFalse(jboss_config.save_config())
        self.assertEquals(
            jboss_common.log.mock_calls,
            [mock.call('Saving JBoss config to file: /tmp/config.json'),
             mock.call(('Failed to save config to "/tmp/config.json" - '
                        'file saving error'), level="ERROR")]
        )

    @mock.patch('litpmnjboss.litp_jboss_config.json')
    @mock.patch('__builtin__.open')
    @mock.patch('litpmnjboss.litp_jboss_config.common')
    def test_save_config_creates_config_file(self, jboss_common, _open, json):
        jboss_config = LitpJbossConfig({})
        jboss_config.config_dir = '/tmp'
        fhandle = mock.Mock()
        _open.return_value.__enter__.return_value = fhandle
        self.assertTrue(jboss_config.save_config())
        jboss_common.log.assert_called_once_with(
            'Saving JBoss config to file: /tmp/config.json')
        json.dump.assert_called_with(jboss_config.litp_dict, fhandle)

    @mock.patch('litpmnjboss.litp_jboss_config.sys.exit')
    @mock.patch('litpmnjboss.litp_jboss_config.json')
    @mock.patch('__builtin__.open')
    @mock.patch('litpmnjboss.litp_jboss_config.common')
    def test_load_config_fails_mysteriously_and_terminates_program(
            self, jboss_common, _open, json, exit):
        _open.side_effect = Exception('file opening error')
        litp_jboss_config.LITP_JBOSS_DATA_DIR = '/tmp/'
        jboss_config_instance = LitpJbossConfig({})
        LitpJbossConfig.load_config(jboss_config_instance)
        path = '/tmp/{0}/config.json'.format(str(jboss_config_instance))
        self.assertEquals(jboss_common.log.mock_calls, [
            mock.call('Loading JBoss config from file: {0}'.format(path)),
            mock.call(('Unable to load config from "{0}": '
                       'file opening error').format(path), level="ERROR")
        ])
        exit.assert_called_once_with(1)

    @mock.patch('litpmnjboss.litp_jboss_config.json')
    @mock.patch('__builtin__.open')
    @mock.patch('litpmnjboss.litp_jboss_config.common')
    def test_load_config_fails_to_open_config_file(
            self, jboss_common, _open, json):
        _open.side_effect = IOError('file opening error')
        litp_jboss_config.LITP_JBOSS_DATA_DIR = '/tmp/'
        jboss_config_instance = LitpJbossConfig({})
        self.assertEquals(None,
                          LitpJbossConfig.load_config(jboss_config_instance))
        path = '/tmp/{0}/config.json'.format(str(jboss_config_instance))
        self.assertEquals(jboss_common.log.mock_calls, [
            mock.call('Loading JBoss config from file: {0}'.format(path)),
            mock.call('Unable to load config from "{0}"'.format(path),
                      level="INFO")
        ])

    @mock.patch('litpmnjboss.litp_jboss_config.json')
    @mock.patch('__builtin__.open')
    @mock.patch('litpmnjboss.litp_jboss_config.common')
    def test_load_config_creates_new_instance_of_jboss_config(
            self, jboss_common, _open, json):
        fhandle = mock.Mock()
        _open.return_value.__enter__.return_value = fhandle
        json.load.return_value = {'TEST_KEY': 'TEST_VAL'}
        litp_jboss_config.LITP_JBOSS_DATA_DIR = '/tmp/'
        jboss_config_instance = LitpJbossConfig({})
        result = LitpJbossConfig.load_config(jboss_config_instance)
        self.assertTrue(isinstance(result, LitpJbossConfig))
        # test if new instance gets passed data from conf file as arg
        self.assertEquals(result.make_env()['TEST_KEY'], 'TEST_VAL')

    @mock.patch('litpmnjboss.litp_jboss_config.common')
    @mock.patch('litpmnjboss.litp_jboss_config.shutil.rmtree')
    def test_remove_state_dir_fails(self, rmtree, jboss_common):
        jboss_config = LitpJbossConfig({})
        jboss_config.config_dir = '/tmp'
        rmtree.side_effect = Exception('rmtree exception')
        jboss_config.remove_state_dir()
        jboss_common.log.assert_called_once_with(
            "Failed to remove state dir: /tmp. rmtree exception",
            level="ERROR")

    @mock.patch('litpmnjboss.litp_jboss_config.common')
    @mock.patch('litpmnjboss.litp_jboss_config.shutil.rmtree')
    def test_remove_state_dir_succeeds(self, rmtree, jboss_common):
        jboss_config = LitpJbossConfig({})
        jboss_config.config_dir = '/tmp'
        jboss_config.remove_state_dir()
        self.assertEqual(0, jboss_common.log.call_count)

    #TODO test failed lock creation
    @mock.patch('__builtin__.open')
    @mock.patch('litpmnjboss.litp_jboss_config.common')
    def test_create_lock(self, jboss_common, _open):
        jboss_config = LitpJbossConfig({})
        jboss_config.config_dir = '/tmp'
        jboss_config.create_lock()
        jboss_common.make_directory.assert_called_once_with('/tmp')
        _open.assert_called_once_with('/tmp/lockfile', 'w')
        _open.return_value.close.assert_called_once_with()

    #TODO test failed lock removal
    @mock.patch('litpmnjboss.litp_jboss_config.os')
    def test_remove_lock(self, os):
        jboss_config = LitpJbossConfig({})
        jboss_config.config_dir = '/tmp'
        jboss_config.remove_lock()
        os.remove.assert_called_with('/tmp/lockfile')

    def test_jboss_config_is_sp_different(self):
        conf = {'LITP_SP_COUNT': '1'}
        jboss_config = LitpJbossConfig(conf)
        self.assertFalse(jboss_config.is_sp_different(jboss_config))
        self.assertTrue(jboss_config.is_sp_different(None))
        new_instance = LitpJbossConfig({'a': 'b'})
        result = jboss_config.is_sp_different(new_instance)
        self.assertTrue(result)

    @mock.patch('litpmnjboss.litp_jboss_config.sys.exit')
    def test_bad_management_listener_ip_causes_program_to_terminate(self,
                                                                    exit):
        conf = {
            'LITP_JEE_CONTAINER_home_dir': "/jboss",
            'LITP_JEE_CONTAINER_management_listener': 'bahhdhh_ip!',
        }
        LitpJbossConfig(conf)
        exit.assert_called_once_with(1)
