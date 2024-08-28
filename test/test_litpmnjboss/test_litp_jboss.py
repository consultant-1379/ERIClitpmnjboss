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

import os
os.environ["TESTING_FLAG"] = "1"
import sys
from cStringIO import StringIO
import pwd
import grp
import shutil
import tempfile
from test.test_support import unlink
import mock

from litpmnjboss import litp_jboss, litp_jboss_app, \
                       litp_jboss_cli, litp_jboss_config, litp_jboss_common


class TestLitpJboss(unittest.TestCase):

    class _counter_func(object):
        # Helper functor that counts the number of times its called
        def __init__(self, output_list, name=''):
            self.name = name
            self.gen = (i for i in output_list)
            self.calls = 0

        def __call__(self, *args, **kwargs):
            try:
                self.calls += 1
                return self.gen.next()
            except StopIteration:
                raise AssertionError("%s Called too many times: %d calls" %
                        (self.name, self.calls))

    def _mock__update_perms(self, path):
        return 0

    def _mock__verify_pid(self):
        self.jboss.pid = 12345

    def _mock__exec_cmd_ok(self, arg2, env=None):
        # make console logs clean of 'Exception' strings
        grep_exceptions = "grep -c 'Exception'"
        if grep_exceptions in arg2:
            return 0, ["0"], []

        # create inside home_dir
        if "tar" in arg2:
            if not os.path.exists(self._tmppath):
                os.mkdir(self._tmppath)
            if not os.path.exists(self.jboss.config.get('home_dir')):
                os.mkdir(self.jboss.config.get('home_dir'))

        # processes found
        return 0, ["1"], []

    def _mock_exec_cmd_fail(self, arg1):
        return 1, ["2"], []

    def _mock_litp_jboss_cli_not_running(self, arg1):
        return (0, [""], ['ERROR'])

    def _create_install_source(self):
        # create dummy install source
        if not os.path.exists(self._tmppath):
            os.makedirs(self._tmppath)

        if not os.path.exists(self.jboss.config.get('install_source')):
            with open(self.jboss.config.get('install_source'), 'w') as f:
                f.write('foobar')

    def _make_env_dict(self):
        """
        Create minimal valid environment to run tests.
        """

        test_process_user = pwd.getpwuid(os.getuid())
        test_process_user_name = test_process_user.pw_name

        test_process_group = grp.getgrgid(test_process_user.pw_gid)
        test_process_group_name = test_process_group.gr_name

        vars = (
            ('data_dir', os.path.join(self._tmppath, 'data_dir')),
            ('home_dir', os.path.join(self._tmppath, \
                                                'sg1_su1_jbosscomp_jboss')),
            ('log_dir', os.path.join(self._tmppath, 'log_dir')),
            ('instance_name', "sg1_su1_jbosscomp_jboss"),
            ('process_user', test_process_user_name),
            ('process_group', test_process_group_name),
            ('install_source', os.path.join(self._tmppath, 'foo-jboss.tar')),
            ('command_line_options', ""),
            ('pre_deploy', os.path.join(self._tmppath, 'pre_deploy.d')),
            ('post_deploy', os.path.join(self._tmppath, 'post_deploy.d')),
            ('pre_undeploy', os.path.join(self._tmppath, 'pre_undeploy.d')),
            ('post_undeploy', os.path.join(self._tmppath, 'post_undeploy.d')),
            ('pre_start', os.path.join(self._tmppath, 'pre_start.d')),
            ('post_start', os.path.join(self._tmppath, 'post_start.d')),
            ('pre_shutdown', os.path.join(self._tmppath, 'pre_shutdown.d')),
            ('post_shutdown', os.path.join(self._tmppath, 'post_shutdown.d')),
            ('pre_upgrade', os.path.join(self._tmppath, 'pre_upgrade.d')),
            ('post_upgrade', os.path.join(self._tmppath, 'post_upgrade.d')),
            ('public_listener', '0.0.0.0'),
            ('public_port_base', '8080'),
            ('management_listener', '0.0.0.0'),
            ('management_port_base', '9990'),  # human
            ('management_port_native', '9999'),  # cli
            ('management_user', 'mgmt87458765'),
            ('management_password', 'mgmtpass987698768'),
            ('port_offset', '0'),
            ('version', '1.0.0')
        )

        env_dict = {}
        for name, value in vars:
            env_dict['LITP_JEE_CONTAINER_' + name] = value
        return env_dict

    def _make_jboss_config(self):
        return litp_jboss_config.LitpJbossConfig(
                config_dict=self._make_env_dict())

    def _create_temp_structs(self):
        for frag in ('pre_deploy', 'post_deploy',
                     'pre_start', 'post_start',
                     'pre_undeploy', 'post_undeploy',
                     'pre_shutdown', 'post_shutdown',
                     'pre_upgrade', 'post_upgrade'):
            litp_jboss_common.make_directory(self.jboss.config.get(frag))

        litp_jboss_common.make_directory(self.jboss.config.get('home_dir'))

    def _make_jboss_with_apps_config(self, num_sps=0):
        env_dict = {
            'LITP_JEE_CONTAINER_data_dir':
                                self._tmppath + "/sg1_su1_jbosscomp_jboss",
            'LITP_JEE_CONTAINER_home_dir':
                                self._tmppath + "/sg1_su1_jbosscomp_jboss",
            'LITP_JEE_CONTAINER_log_dir':
                    self._tmppath + "/var/log/jboss/sg1_su1_jbosscomp_jboss",
            'LITP_JEE_CONTAINER_log_file':
                    self._tmppath + "/var/log/jboss/sg1_su1_jbosscomp_jboss",
            'LITP_JEE_CONTAINER_instance_name': "sg1_su1_jbosscomp_jboss",
            'LITP_JEE_CONTAINER_name': 'jee1',
            'LITP_JEE_CONTAINER_instance_name': 'jee1',
            'LITP_JEE_CONTAINER_install_source': '/tmp/jboss.tar.gz',
            'LITP_JEE_CONTAINER_version': '1.0',
            'LITP_JEE_CONTAINER_process_user': 'jee1',
            'LITP_JEE_CONTAINER_process_group': 'jee1',
            'LITP_JEE_CONTAINER_public_listener': '127.0.0.1',
            'LITP_JEE_CONTAINER_public_port_base': '8080',
            'LITP_JEE_CONTAINER_management_listener': '127.0.0.1',
            'LITP_JEE_CONTAINER_management_password': 'mgmtpass987698768',
            'LITP_JEE_CONTAINER_management_port_base': '9990',
            'LITP_JEE_CONTAINER_management_port_native': '9999',
            'LITP_JEE_CONTAINER_management_user': 'mgmt87458765',
            'LITP_JEE_CONTAINER_port_offset': '0',
            'LITP_JEE_CONTAINER_Xms': '1024M',
            'LITP_JEE_CONTAINER_Xmx': '1024M',
            'LITP_JEE_CONTAINER_MaxPermSize': '256M',
            'LITP_JEE_CONTAINER_command_line_options':
        '  -Dcom.ericsson.oss.sdk.node.identifier=jee1 -Djboss.node.name=jee1',
            'LITP_JEE_CONTAINER_pre_deploy':
        '/opt/ericsson/nms/litp/etc/jboss/jboss_instance/pre_deploy.d',
            'LITP_JEE_CONTAINER_post_deploy':
        '/opt/ericsson/nms/litp/etc/jboss/jboss_instance/post_deploy.d',
            'LITP_JEE_CONTAINER_pre_undeploy':
        '/opt/ericsson/nms/litp/etc/jboss/jboss_instance/pre_undeploy.d',
            'LITP_JEE_CONTAINER_post_undeploy':
        '/opt/ericsson/nms/litp/etc/jboss/jboss_instance/post_undeploy.d',
            'LITP_JEE_CONTAINER_pre_start':
        '/opt/ericsson/nms/litp/etc/jboss/jboss_instance/pre_start.d',
            'LITP_JEE_CONTAINER_post_start':
        '/opt/ericsson/nms/litp/etc/jboss/jboss_instance/post_start.d',
            'LITP_JEE_CONTAINER_pre_shutdown':
        '/opt/ericsson/nms/litp/etc/jboss/jboss_instance/pre_shutdown.d',
            'LITP_JEE_CONTAINER_post_shutdown':
        '/opt/ericsson/nms/litp/etc/jboss/jboss_instance/post_shutdown.d',
            'LITP_JEE_CONTAINER_pre_upgrade':
        '/opt/ericsson/nms/litp/etc/jboss/jboss_instance/pre_upgrade.d',
            'LITP_JEE_CONTAINER_post_upgrade':
        '/opt/ericsson/nms/litp/etc/jboss/jboss_instance/post_upgrade.d',
            'LITP_DE_COUNT': '3',
            'LITP_DE_0_JEE_DE_name': 'jeede1',
            'LITP_DE_0_JEE_DE_version': '1.0.1',
            'LITP_DE_0_JEE_DE_app_type': 'ear',
            'LITP_DE_0_JEE_DE_install_source': self._tmppath \
                                                        + '/jeede1-1.0.1.ear',
            'LITP_DE_0_JEE_DE_pre_deploy':
        '/opt/ericsson/nms/litp/etc/jboss/jboss_app/pre_deploy.d',
            'LITP_DE_0_JEE_DE_post_deploy':
        '/opt/ericsson/nms/litp/etc/jboss/jboss_app/post_deploy.d',
            'LITP_DE_0_JEE_DE_pre_undeploy':
        '/opt/ericsson/nms/litp/etc/jboss/jboss_app/pre_undeploy.d',
            'LITP_DE_0_JEE_DE_post_undeploy':
        '/opt/ericsson/nms/litp/etc/jboss/jboss_app/post_undeploy.d',
            'LITP_DE_0_JEE_DE_pre_start':
        '/opt/ericsson/nms/litp/etc/jboss/jboss_app/pre_start.d',
            'LITP_DE_0_JEE_DE_post_start':
        '/opt/ericsson/nms/litp/etc/jboss/jboss_app/post_start.d',
            'LITP_DE_0_JEE_DE_pre_shutdown':
        '/opt/ericsson/nms/litp/etc/jboss/jboss_app/pre_shutdown.d',
            'LITP_DE_0_JEE_DE_post_shutdown':
        '/opt/ericsson/nms/litp/etc/jboss/jboss_app/post_shutdown.d',
            'LITP_DE_0_JEE_DE_pre_upgrade':
        '/opt/ericsson/nms/litp/etc/jboss/jboss_app/pre_upgrade.d',
            'LITP_DE_0_JEE_DE_post_upgrade':
        '/opt/ericsson/nms/litp/etc/jboss/jboss_app/post_upgrade.d',
            'LITP_DE_1_JEE_DE_name': 'jeede2',
            'LITP_DE_1_JEE_DE_version': '1.0.2',
            'LITP_DE_1_JEE_DE_app_type': 'ear',
            'LITP_DE_1_JEE_DE_install_source': self._tmppath \
                                                        + '/jeede2-1.0.2.ear',
            'LITP_DE_1_JEE_DE_pre_deploy':
        '/opt/ericsson/nms/litp/etc/jboss/jboss_app/pre_deploy.d',
            'LITP_DE_1_JEE_DE_post_deploy':
        '/opt/ericsson/nms/litp/etc/jboss/jboss_app/post_deploy.d',
            'LITP_DE_1_JEE_DE_pre_undeploy':
        '/opt/ericsson/nms/litp/etc/jboss/jboss_app/pre_undeploy.d',
            'LITP_DE_1_JEE_DE_post_undeploy':
        '/opt/ericsson/nms/litp/etc/jboss/jboss_app/post_undeploy.d',
            'LITP_DE_1_JEE_DE_pre_start':
        '/opt/ericsson/nms/litp/etc/jboss/jboss_app/pre_start.d',
            'LITP_DE_1_JEE_DE_post_start':
        '/opt/ericsson/nms/litp/etc/jboss/jboss_app/post_start.d',
            'LITP_DE_1_JEE_DE_pre_shutdown':
        '/opt/ericsson/nms/litp/etc/jboss/jboss_app/pre_shutdown.d',
            'LITP_DE_1_JEE_DE_post_shutdown':
        '/opt/ericsson/nms/litp/etc/jboss/jboss_app/post_shutdown.d',
            'LITP_DE_1_JEE_DE_pre_upgrade':
        '/opt/ericsson/nms/litp/etc/jboss/jboss_app/pre_upgrade.d',
            'LITP_DE_1_JEE_DE_post_upgrade':
        '/opt/ericsson/nms/litp/etc/jboss/jboss_app/post_upgrade.d',
            'LITP_DE_1_JEE_PROPERTY_COUNT': '1',
            'LITP_DE_1_JEE_PROPERTY_0_require': '',
            'LITP_DE_1_JEE_PROPERTY_0_property': 'prop1',
            'LITP_DE_1_JEE_PROPERTY_0_value': 'val1',
            'LITP_DE_1_JEE_DS_COUNT': '1',
            'LITP_DE_1_JEE_DS_0_username': 'jimmy',
            'LITP_DE_1_JEE_DS_0_new_connection_sql':
                            "'set datestyle = ISO, European;'",
            'LITP_DE_1_JEE_DS_0_connection_url':
                            'jdbc:oracle:thin:@server1:11521:orcl',
            'LITP_DE_1_JEE_DS_0_name': 'datasource',
            'LITP_DE_1_JEE_DS_0_jndi_name': 'jboss/TestO123RCL',
            'LITP_DE_1_JEE_DS_0_require': '',
            'LITP_DE_1_JEE_DS_0_max_pool_size': '25',
            'LITP_DE_1_JEE_DS_0_driver_name': 'h2',
            'LITP_DE_1_JEE_DS_0_use_ccm': 'false',
            'LITP_DE_1_JEE_DS_0_password': 'passw0rd',
            'LITP_DE_1_JEE_DS_0_blocking_timeout_wait_millis': '5000',
            'LITP_DE_1_JMS_QUEUE_COUNT': '1',
            'LITP_DE_1_JMS_QUEUE_0_jndi': 'jdn1',
            'LITP_DE_1_JMS_QUEUE_0_require': '',
            'LITP_DE_1_JMS_QUEUE_0_name': 'queue1',
            'LITP_DE_1_JMS_TOPIC_COUNT': '1',
            'LITP_DE_1_JMS_TOPIC_0_jndi': 'jdn1',
            'LITP_DE_1_JMS_TOPIC_0_require': '',
            'LITP_DE_1_JMS_TOPIC_0_name': 'topic1',
            'LITP_DE_2_JEE_DE_name': 'jeede3',
            'LITP_DE_2_JEE_DE_version': '1.0.3',
            'LITP_DE_2_JEE_DE_app_type': 'ear',
            'LITP_DE_2_JEE_DE_install_source': self._tmppath \
                                                        + '/jeede3-1.0.3.ear',
            'LITP_DE_2_JEE_DE_pre_deploy':
        '/opt/ericsson/nms/litp/etc/jboss/jboss_app/pre_deploy.d',
            'LITP_DE_2_JEE_DE_post_deploy':
        '/opt/ericsson/nms/litp/etc/jboss/jboss_app/post_deploy.d',
            'LITP_DE_2_JEE_DE_pre_undeploy':
        '/opt/ericsson/nms/litp/etc/jboss/jboss_app/pre_undeploy.d',
            'LITP_DE_2_JEE_DE_post_undeploy':
        '/opt/ericsson/nms/litp/etc/jboss/jboss_app/post_undeploy.d',
            'LITP_DE_2_JEE_DE_pre_start':
        '/opt/ericsson/nms/litp/etc/jboss/jboss_app/pre_start.d',
            'LITP_DE_2_JEE_DE_post_start':
        '/opt/ericsson/nms/litp/etc/jboss/jboss_app/post_start.d',
            'LITP_DE_2_JEE_DE_pre_shutdown':
        '/opt/ericsson/nms/litp/etc/jboss/jboss_app/pre_shutdown.d',
            'LITP_DE_2_JEE_DE_post_shutdown':
        '/opt/ericsson/nms/litp/etc/jboss/jboss_app/post_shutdown.d',
            'LITP_DE_2_JEE_DE_pre_upgrade':
        '/opt/ericsson/nms/litp/etc/jboss/jboss_app/pre_upgrade.d',
            'LITP_DE_2_JEE_DE_post_upgrade':
        '/opt/ericsson/nms/litp/etc/jboss/jboss_app/post_upgrade.d',
            }

        env_dict['LITP_SP_COUNT'] = '%d' % num_sps
        for i in range(num_sps):
            env_dict['LITP_SP_%d_JEE_SP_name' % i] = 'sp%d' % i
            env_dict['LITP_SP_%d_JEE_SP_version' % i] = '1.0.%d' % i
            env_dict['LITP_SP_%d_JEE_SP_install_source' % i] = \
                     '/tmp/sp%d.tgz' % i

        return litp_jboss_config.LitpJbossConfig(config_dict=env_dict)

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.save_exists = litp_jboss.os.path.exists
        self.save_isdir = litp_jboss.os.path.isdir
        self.save_isfile = litp_jboss.os.path.isfile
        self.save_chown = litp_jboss.os.chown
        litp_jboss.os.chown = lambda a, b, c: None

        # temp dir for test generated data
        self._tmppath = tempfile.mkdtemp(prefix='litpjboss')

        # mock litp_jboss_config structures in tmp
        self.temp_jboss_data_dir = litp_jboss_config.LITP_JBOSS_DATA_DIR
        litp_jboss_config.LITP_JBOSS_DATA_DIR = \
                                    os.path.join(self._tmppath, 'jboss_conf/')
        # mock pidfile location and other paths
        config = self._make_jboss_config()
        self.jboss = litp_jboss.LitpJboss(config)
        self.jboss._pidfile = os.path.join(self._tmppath, 'jboss_pidfile.pid')
        self._create_temp_structs()

        def _mock_run_commands(_, cmds, timeout=120):
            out = []
            for cmd in cmds:
                out.append('{\n')
                out.append('    "outcome" => "success",\n')
                out.append('    "result" => "OK"\n')
                out.append('}\n')
            return [0, out, []]

        self.save_run_commands = litp_jboss_cli.LitpJbossCli.run_commands
        litp_jboss_cli.LitpJbossCli.run_commands = _mock_run_commands

    def tearDown(self):
        unittest.TestCase.tearDown(self)
        litp_jboss.os.path.exists = self.save_exists
        litp_jboss.os.path.isdir = self.save_isdir
        litp_jboss.os.path.isfile = self.save_isfile
        litp_jboss.os.chown = self.save_chown
        litp_jboss_cli.LitpJbossCli.run_commands = self.save_run_commands

        litp_jboss_config.LITP_JBOSS_DATA_DIR = self.temp_jboss_data_dir

        # clear temp dir
        if os.path.exists(self._tmppath) and os.path.isdir(self._tmppath):
            from shutil import rmtree
            rmtree(self._tmppath)

    def test_litp_jboss_setup_old_config(self):
        self.jboss1 = litp_jboss.LitpJboss(self._make_jboss_with_apps_config())
        self.jboss1.old_config = {'some': 'old_config'}
        self.jboss1.set_config = lambda x: {'some': 'old_config'}
        self.assertNotEqual(self.jboss1.setup_old_config(), None)

    def test_litp_jboss__get_old_app_config(self):
        self.jboss1 = litp_jboss.LitpJboss(self._make_jboss_with_apps_config())
        # test not finding an old app config
        self.jboss1.old_config = self.jboss1.config
        self.assertEqual(self.jboss1._get_old_app_config(name="test"), None)
        # test finding an old app config
        self.assertNotEqual(self.jboss1._get_old_app_config(name="jeede3"),
                            None)

    def test_litp_jboss__check_all_apps_ok(self):
        self.jboss1 = litp_jboss.LitpJboss(self._make_jboss_with_apps_config())
        # test exit status of 1 rom jboss cli
        self.jboss1.jbosscli.run_commands = lambda arg: (1, ['running'], [])
        self.assertEqual(self.jboss1._check_all_apps_ok(), 1)
        # test fail when number of apps found OK not as expected
        self.jboss1.jbosscli.run_commands = lambda arg: \
                                            (0, ['"result" => "OK"\n'], [])
        self.assertEqual(self.jboss1._check_all_apps_ok(), 1)

    def test_litp_jboss__get_current_value(self):
        self.jboss1 = litp_jboss.LitpJboss(self._make_jboss_with_apps_config())
        self.assertEqual(self.jboss1._get_current_value('version'),
                         None)
        self.assertEqual(self.jboss1._get_current_value('version'),
                         None)
        self.assertEqual(self.jboss1._get_current_value('home_dir'),
                         None)
        self.jboss1.old_config = self.jboss1.config
        self.assertEqual(self.jboss1._get_current_value('version'),
                         '1.0')
        self.assertEqual(self.jboss1._get_current_value('install_source'),
                         '/tmp/jboss.tar.gz')
        self.assertEqual(self.jboss1._get_current_value('home_dir'),
                         self.jboss1.config.get('home_dir'))

    def test_litp_jboss__get_old_config(self):
        self.jboss1 = litp_jboss.LitpJboss(self._make_jboss_with_apps_config())
        self.jboss1.old_config = self.jboss1.config
        self.assertEqual(self.jboss1._get_old_config(),
                         self.jboss1.config)

    def test_litp_jboss_extract_apps_from_env(self):
        self.jboss1 = litp_jboss.LitpJboss(self._make_jboss_with_apps_config())
        self.assertNotEqual(self.jboss1.config.apps, [])

#     def test_litp_jboss_start(self):
#          test setup
#         self.jboss._run_daemon = lambda: 0
#         self.jboss.status = lambda silent = True: 0
#         self.jboss._get_current_value = lambda x: '1.0.1' \
#                         if x == 'version' else None
#         self.jboss.deploy = lambda: 0
#         self.jboss._run_fragments = lambda f: 0
#          ignoring the configs (not first start)
#         self.jboss.setup_old_config = lambda: None
#         self.jboss.set_config = lambda arg: True
#         self.jboss.config.lock_exists = lambda: False
#         self.jboss.upgrade = lambda: 0
#         self.assertEqual(self.jboss.start(), 0)
#         # Test upgrade fails
#         self.jboss.upgrade = lambda: 2
#         self.assertEqual(self.jboss.start(), 2)
#         self.jboss.upgrade = lambda: 0
#         # Test lock exists / cleanup success
#         self.jboss.config.lock_exists = lambda: True
#         self.jboss._cleanup_failed_start = lambda: 0
#         self.assertEqual(self.jboss.start(), 0)
#         # Test lock exists / cleanup fails
#         self.jboss.config.lock_exists = lambda: True
#         self.jboss._cleanup_failed_start = lambda: 1
#         self.assertEqual(self.jboss.start(), 1)
#         # Test deploy fails
#         tmp1 = litp_jboss.os.path.isdir
#         self.jboss.config.lock_exists = lambda: False
#         self.jboss.config.create_lock = lambda: None
#         litp_jboss.os.path.isdir = lambda a: False
#         self.jboss._get_current_value = lambda prop:  None
#         self.jboss.deploy = lambda: 1
#         self.assertEqual(self.jboss.start(), 1)
#         # Test remove_old_apps fails
#         self.jboss._remove_old_apps = lambda: 1
#         self.jboss.deploy = lambda: 0
#         self.jboss.upgrade = lambda: 0
#         self.assertEqual(self.jboss.start(), 1)
#         # Test start_all_apps fails
#         self.jboss._remove_old_apps = lambda: 0
#         self.jboss._start_all_apps = lambda: 1
#         self.jboss.deploy = lambda: 0
#         self.jboss.upgrade = lambda: 0
#         self.assertEqual(self.jboss.start(), 1)
#         litp_jboss.os.path.isdir = tmp1

        def _mock_get_current_value_0(prop):
            if prop == 'version':
                return self.jboss.config.get(prop)
            elif prop == 'install_source':
                return self.jboss.config.get(prop)
            elif prop == 'home_dir':
                return '/home/asdf'
            else:
                return None
        # test redeploy when home dir has changed
        self.jboss._get_current_value = _mock_get_current_value_0
        self.jboss._redeploy = lambda: 1
        self.assertEqual(self.jboss.start(), 1)
        # test when update perms fails
        self.jboss._redeploy = lambda: 0
        self.jboss._update_perms = lambda x: 1
        self.assertEqual(self.jboss.start(), 1)

    def test_litp_jboss_start_management_user_failed(self):
        # _add_management_user fails
        self.jboss._run_daemon = lambda: 0
        self.jboss.status = lambda silent = True: 0
        self.jboss.old_config = self.jboss.config
        self.jboss._redeploy = lambda: 0

        old_config_dict = self._make_env_dict()
        old_config_dict['LITP_JEE_CONTAINER_management_user'] = "ElTioPepe"
        self.jboss.old_config = litp_jboss_config.LitpJbossConfig(
                old_config_dict)

        self.jboss._add_management_user = lambda: 1

        self.assertEqual(self.jboss.start(), 1)

    def test_litp_jboss_start_management_password_failed(self):
        # _add_management_user fails for password
        self.jboss._run_daemon = lambda: 0
        self.jboss.status = lambda silent = True: 0
        self.jboss.old_config = self.jboss.config
        self.jboss._redeploy = lambda: 0

        old_config_dict = self._make_env_dict()
        old_config_dict['LITP_JEE_CONTAINER_management_password'] = \
                "imapassword"
        self.jboss.old_config = litp_jboss_config.LitpJbossConfig(
                old_config_dict)

        self.jboss._add_management_user = lambda: 1

        self.assertEqual(self.jboss.start(), 1)

    def test_litp_jboss_start_with_failed_status(self):
        self.jboss._run_daemon = lambda: 0
        self.jboss.status = lambda silent = True: 1
        self.assertEqual(self.jboss.start(), 1)

    def test_litp_jboss_start_with_failed_create_pid_dir(self):
        self.jboss._run_daemon = lambda: 0
        self.jboss.status = lambda silent = True: 0
        self.jboss.old_config = self.jboss.config
        self.jboss._redeploy = lambda: 0
        self.jboss._create_piddir = lambda: 1
        self.assertEqual(self.jboss.start(), 1)

    def test_litp_jboss_start_with_changed_data_dir(self):
        self.jboss._run_daemon = lambda: 0
        self.jboss.status = lambda silent = True: 0
        self.jboss.old_config = self.jboss.config
        self.jboss._redeploy = lambda: 0
        self.jboss._create_piddir = lambda: 0

        def _mock_get_current_value_log(prop):
            if prop == 'version':
                return self.jboss.config.get(prop)
            elif prop == 'install_source':
                return self.jboss.config.get(prop)
            elif prop == 'data_dir':
                return ''
            else:
                return None
        self.jboss._get_current_value = _mock_get_current_value_log
        self.jboss.config.config['data_dir'] = '/asas'
        self.assertEqual(self.jboss.start(), 1)

    def test_litp_jboss_start_with_changed_log_dir(self):
        self.jboss._run_daemon = lambda: 0
        self.jboss.status = lambda silent = True: 0
        self.jboss.old_config = self.jboss.config
        self.jboss._redeploy = lambda: 0
        self.jboss._create_piddir = lambda: 0

        def _mock_get_current_value_log(prop):
            if prop == 'version':
                return self.jboss.config.get(prop)
            elif prop == 'install_source':
                return self.jboss.config.get(prop)
            elif prop == 'log_dir':
                return ''
            else:
                return None
        self.jboss._get_current_value = _mock_get_current_value_log
        self.jboss.config.config['log_dir'] = '/asas'
        self.assertEqual(self.jboss.start(), 1)
        self.jboss._update_perms = lambda x: 1 \
                        if x == '/asas' else 0

#     def test_litp_jboss_start_with_scripts(self):
#         try:
#             self.jboss._run_daemon = lambda: 0
#             self.jboss.status = lambda silent = True: 0
#             self.jboss._get_current_value = lambda x: '1.0.0' \
#                         if x == 'version' else None
#             self.jboss.deploy = lambda: 0
#
#             # Generate pre_start and post_start scripts that
#             # create files in /tmp. and assert that those files
#             # don't already exist.
#             # Set the pre_start and post_start attributes of the
#             # jboss object to the paths of the directories where
#             # these scripts live.
#             for frag in ('pre_start', 'post_start'):
#                 frag_dir = self.jboss.config.get(frag)
#                 if not os.path.exists(frag_dir):
#                     os.makedirs(frag_dir)
#                 script = os.path.join(frag_dir, 'test.sh')
#                 f = open(script, 'w')
#                 f.write('#!/bin/sh\n')
#                 f.write('touch /tmp/%s_run\n' % frag)
#                 f.close()
#                 os.chmod(script, 0777)
#                 self.assertFalse(os.path.exists('/tmp/%s_run' % frag))
#
#             # ignoring the configs (not first start)
#             self.jboss.setup_old_config = lambda: None
#             self.jboss.set_config = lambda arg: True
#             self.jboss.upgrade = lambda: 0
#             self.assertEqual(self.jboss.start(), 0)
#             for frag in ('pre_start', 'post_start'):
#                 self.assertTrue(os.path.exists('/tmp/%s_run' % frag))
#         finally:
#             for frag in ('pre_start', 'post_start'):
#                 f = '/tmp/%s_run' % frag
#                 if os.path.exists(f):
#                     os.unlink(f)

    def test_litp_jboss_start_already_running(self):
        self.jboss._verify_pid = self._mock__verify_pid
        self.jboss._update_perms = self._mock__update_perms
        self.jboss._get_current_version = lambda: '1.0.0'
        self.jboss._run_daemon = lambda: 0
        self.jboss.deploy = lambda: 0
        self.assertEqual(self.jboss.start(), 0)

    def test_litp_jboss_start_current_version_empty(self):
        self.jboss.upgrade = lambda: 1  # we want upgrade to fail
        self.jboss.deploy = lambda: 0
        self.assertEqual(self.jboss.start(), 1)

#    def test_litp_jboss_start_log_dir_exception(self):
#        os.makedirs(self.jboss.home_dir)
#        self.jboss._get_current_value = lambda prop: \
#                            self.jboss.config.get(prop)
#        def _mock_makedirs(name, mode=None):
#            raise OSError
#        orig = litp_jboss.os.makedirs
#        litp_jboss.os.makedirs = _mock_makedirs
#        result = self.jboss.start()
#        self.assertEqual(result, 1)
#        litp_jboss.os.makedirs = orig

    def test_litp_jboss__update_perms_no_path(self):
        foo_path = '/tmp/123124234235'
        self.assertEqual(self.jboss._update_perms(foo_path), 1)

    def test_litp_jboss__update_perms_chown_error(self):
        self.jboss._exec_cmd = lambda cmd: (1, [''], [''])
        self.assertEqual(self.jboss._update_perms(self._tmppath), 1)

    def test_litp_jboss_start_update_perms_data_dir_failed(self):
        # don't upgrade / update
        self.jboss._get_current_value = lambda prop: \
                                    self.jboss.config.get(prop)

        def _mock_update_perms_data_dir_fails(arg):
            if arg == self.jboss.config.get('data_dir'):
                return 1
            else:
                return 0
        self.jboss._update_perms = _mock_update_perms_data_dir_fails
        # ignoring the configs (not first start)
        self.jboss.setup_old_config = lambda: None
        self.jboss.set_config = lambda arg: True
        self.assertEqual(1, self.jboss.start())

    def test_litp_jboss__create_piddir(self):
        tmp1 = litp_jboss.os.path.exists
        litp_jboss.os.path.exists = lambda a: False
        tmp2 = litp_jboss.os.makedirs
        litp_jboss.os.makedirs = lambda a: None

        # positive
        self.assertEqual(self.jboss._create_piddir(), 0)

        # negative
        def _mock_raise(self):
            raise OSError()
        litp_jboss.os.makedirs = _mock_raise
        self.assertEqual(self.jboss._create_piddir(), 1)
        # cleanup
        litp_jboss.os.path.exists = tmp1
        litp_jboss.os.makedirs = tmp2

#    def test_litp_jboss_start_update_perms__pidfile_failed(self):
#        if not os.path.exists(self.jboss._pidfile):
#            cleanup = True
#            with open(self.jboss._pidfile, 'w') as p:
#                p.write('12345')
#
#        # don't upgrade / update
#        self.jboss._get_current_value = lambda prop: \
#                                    self.jboss.config.get(prop)
#
# #        def _mock_update_perms__pidfile_fails(arg):
# #            if arg == self.jboss._pidfile:
# #                return 1
# #            else:
# #                return 0
# #        self.jboss._update_perms = _mock_update_perms__pidfile_fails
# #
# #        result = self.jboss.start()
# #        self.assertEqual(result, 1)
# #        # only delete file if it was not there.
# #        if cleanup and os.path.exists(self.jboss._pidfile) and \
# #            os.path.isfile(self.jboss._pidfile):
# #            os.unlink(self.jboss._pidfile)

    def test_litp_jboss_start_update_perms_log_dir_failed(self):

        # don't upgrade / update
        self.jboss._get_current_value = lambda prop: \
                                    self.jboss.config.get(prop)

        self.jboss._update_perms = lambda args: 1
        # ignoring the configs (not first start)
        self.jboss.setup_old_config = lambda: None
        self.jboss.set_config = lambda arg: True
        self.assertEqual(self.jboss.start(), 1)

    def test_litp_jboss_start_versions_differ_upgrade_fails(self):
        self.jboss._get_current_value = lambda x: '2.0.0' \
                                    if x == 'verison' else None
        self.jboss.version = '1.0.0'
        self.jboss.deploy = lambda: 0
        self.jboss.upgrade = lambda: 1
        self.assertEqual(self.jboss.start(), 1)

    def test_litp_jboss_stop(self):
        self.jboss._verify_pid = self._mock__verify_pid
        self.jboss._run_fragments = lambda f: 0
        self.jboss._kill_pid = lambda proc, sig: 0
        self.jboss._sleep = lambda arg: True
        # no processes found: 1, ['0\n'], []
        # process found:      0, ['1\n'], []
        self.jboss._exec_cmd = lambda arg1, silent=False: (1, ['0\n'], [])
        # ignoring the configs (not first start)
        self.jboss.setup_old_config = lambda: None
        self.jboss.set_config = lambda arg: True
        self.assertEqual(self.jboss.stop(), 0)
        # test when ERR is stdout
        self.jboss._exec_cmd = lambda arg1, silent=False: (1, ['0'], ['ERR'])
        self.assertEqual(self.jboss.stop(), 0)
        # test post shutdown hook failure 1
        self.jboss._run_fragments = lambda f: 1 \
                                    if f == 'post_shutdown' else 0
        self.assertEqual(self.jboss.stop(), 1)
        # test post shutdown hook failure 2
        self.jboss._exec_cmd = lambda arg1, silent=False: (1, ['0'], [])
        self.assertEqual(self.jboss.stop(), 1)

    def test__kill_pid_pos_01(self):
        try:
            self.old_kill = litp_jboss.os.kill
            litp_jboss.os.kill = lambda proc, sig: 0
            self.assertEqual(self.jboss._kill_pid(0, 9), 0)
        finally:
            litp_jboss.os.kill = self.old_kill

    def test__kill_pid_neg_01(self):
        try:
            def _mock_os_kill_raises(arg1, arg2):
                raise OSError()
            self.old_kill = litp_jboss.os.kill
            litp_jboss.os.kill = _mock_os_kill_raises
            self.assertEqual(self.jboss._kill_pid(0, 9), 1)
        finally:
            litp_jboss.os.kill = self.old_kill

    def test_litp_jboss_stop_kill_fails(self):
        def _mock_kill_always_fail(pid, sig):
            e = OSError()
            e.errno = 1
            e.strerror = 'Permission denied'
            raise e

        self.jboss._kill_pid = _mock_kill_always_fail
        self.jboss._verify_pid = self._mock__verify_pid
        self.jboss._stop_all_apps = lambda: None
        self.jboss._run_fragments = lambda f: None
        # ignoring the configs (not first start)
        self.jboss.setup_old_config = lambda: None
        self.jboss.set_config = lambda arg: True
        self.assertEqual(1, self.jboss.stop())

    def test_litp_jboss_stop_stopped(self):
        def _mock__verify_pid_none():
            return None
        self.jboss._verify_pid = _mock__verify_pid_none
        # ignoring the configs (not first start)
        self.jboss.setup_old_config = lambda: None
        self.jboss.set_config = lambda arg: True
        result = self.jboss.stop()
        self.assertEqual(result, 0)

    def test_litp_jboss_force_stop(self):
        class _mock__verify_pid_counting(object):
            def __init__(slf, max, pid):
                slf.max = max
                slf.pid = pid
                slf.calls = 0
                slf.nonecalls = 0

            def __call__(slf):
                if slf.calls < slf.max:
                    self.jboss.pid = slf.pid
                else:
                    self.jboss.pid = None
                    slf.nonecalls += 1
                slf.calls += 1
        self.jboss._verify_pid = _mock__verify_pid_counting(max=5, pid=12345)

        def _mock_kill(arg1, arg2):
            return None

        self.jboss._kill_pid = _mock_kill
        self.jboss._sleep = lambda seconds: None
        # ignoring the configs (not first start)
        self.jboss.setup_old_config = lambda: None
        self.jboss.set_config = lambda arg: True
        result = self.jboss.force_stop()
        self.assertEqual(0, result)

        self.jboss._kill_pid = lambda *args: 1
        self.jboss._verify_pid = _mock__verify_pid_counting(max=1, \
                pid=12345)
        self.assertEqual(self.jboss._force_stop(), 1)

    def _mock_run_jboss_http_cmd(self, attrs, max_time=None):
        return 0, {'outcome': 'success', 'result': 'running'}

    def _mock_run_jboss_http_cmd_not_running(self, attrs, max_time=None):
        return 7, 7

    def test_litp_jboss_status_silent_pos_01(self):
        # Check status(silent=True) passes when curl succeeds
        self.jboss._check_jboss_is_running = lambda silent: (0, 0)
        self.jboss._verify_pid = self._mock__verify_pid
        self.assertEqual(self.jboss.status(silent=True), 0)

    def test_litp_jboss_status_silent_neg_01(self):
        # Check status(silent=True) fails when no pid
        self.jboss._verify_pid = lambda: None
        self.jboss.pid = None
        self.assertEqual(self.jboss.status(silent=True), 1)

    def test_litp_jboss_status_silent_neg_02(self):
        # Check status(silent=True) fails when curl fails
        self.jboss._sleep = lambda: None
        self.jboss._check_jboss_is_running = \
                self._mock_run_jboss_http_cmd_not_running
        self.jboss._verify_pid = self._mock__verify_pid
        self.assertEqual(self.jboss.status(silent=True), 1)

    def test_litp_jboss_status_silent_neg_03(self):
        # Check status(silent=True) fails when curl succeeds,
        # but gets a result it doesn't like
        self.jboss._check_jboss_is_running = lambda silent: (0,
                {'outcome': 'success',
                 'status': 'not running'})
        self.jboss._verify_pid = self._mock__verify_pid
        self.assertEqual(self.jboss.status(silent=True), 1)

    def test_litp_jboss_status_not_silent_pos_01(self):
        # Check status(silent=False) succeeds when curl req fails
        self.jboss._verify_pid = self._mock__verify_pid
        self.jboss._check_jboss_is_running = \
                self._mock_run_jboss_http_cmd_not_running
        self.assertEqual(self.jboss.status(silent=False), 0)

    def test_litp_jboss_status_not_silent_pos_02(self):
        # Check status(silent=False) succeeds when curl succeeds,
        # but gets a result it doesn't like
        self.jboss._verify_pid = self._mock__verify_pid
        self.jboss._check_jboss_is_running = lambda silent: (0,
                {'outcome': 'success',
                 'status': 'not running'})
        self.assertEqual(self.jboss.status(silent=False), 0)

    def test_litp_jboss_status_not_silent_pos_03(self):
        # Check status(silent=False) succeeds when curl succeeds
        self.jboss._verify_pid = self._mock__verify_pid
        self.jboss._check_jboss_is_running = self._mock_run_jboss_http_cmd
        self.assertEqual(self.jboss.status(silent=False), 0)

    def test_litp_jboss_status_not_silent_neg_01(self):
        # Check status(silent=False) fails when no pid
        self.jboss._verify_pid = lambda: None
        self.jboss.pid = None
        self.assertEqual(self.jboss.status(silent=False), 1)

    def test_litp_jboss_status_jboss_cli(self):
        silent = False
        # 'running' in cli response
        res = (0, 0)
        self.jboss.jbosscli.run = lambda arg: (0, ['running'], [])
        self.assertEqual(self.jboss._check_jboss_via_cli(silent), res)

        # no 'running' string in cli response
        res = (0, 1)
        self.jboss.jbosscli.run = lambda arg: (0, [], [])
        self.assertEqual(self.jboss._check_jboss_via_cli(silent), res)

    def test_litp_jboss__check_jboss_is_running_pos_01(self):
        self.jboss._have_management_account = lambda: True
        self.jboss._check_jboss_via_http = lambda: (0, 0)
        self.jboss._check_jboss_via_cli = lambda silent: self.fail(
                "Wrong method chosen")
        res = self.jboss._check_jboss_is_running(silent=True)
        self.assertEqual(res, (0, 0))

    def test_litp_jboss__check_jboss_is_running_pos_02(self):
        self.jboss._have_management_account = lambda: False
        self.jboss._check_jboss_via_http = lambda: self.fail(
                "Wrong method chosen")
        self.jboss._check_jboss_via_cli = lambda silent: (0, 0)
        res = self.jboss._check_jboss_is_running(silent=True)
        self.assertEqual(res, (0, 0))

    def test_litp_jboss__have_management_account_pos_01(self):
        # Management user and password already specified in setUp
        self.assertTrue(self.jboss._have_management_account())

    def test_litp_jboss__have_management_account_pos_02(self):
        del self.jboss.config.config['management_user']
        self.assertFalse(self.jboss._have_management_account())

    def test_litp_jboss__have_management_account_pos_03(self):
        del self.jboss.config.config['management_password']
        self.assertFalse(self.jboss._have_management_account())

    def _mock_json_dumps(self, obj):
        # Helper function for test_litp_jboss__make_jboss_http_cmd_* tests
        self.assertEqual(['json.pretty', 'name', 'operation'],
                sorted(obj.keys()))
        self.assertEqual(obj['operation'], 'read-attribute')
        self.assertEqual(obj['name'], 'server-state')
        # Check that make_jboss_http_cmd injects 'json.pretty = 1'
        self.assertEqual(obj['json.pretty'], 1)
        return '{"operation": "read-attribute", "name": "server-state", ' \
               '"json.pretty": 1}'

    def test_litp_jboss__make_jboss_http_cmd_pos_01(self):
        _old_dumps = litp_jboss.json.dumps
        try:
            litp_jboss.json.dumps = self._mock_json_dumps
            self.jboss.config.get_jboss_management_url = lambda: \
                    "http://127.0.0.1:9990/console"
            args = {'operation': 'read-attribute', 'name': 'server-state'}
            res = self.jboss._make_jboss_http_cmd(args, max_time=None)
            self.assertTrue("-u mgmt87458765:mgmtpass987698768" in res)
            self.assertTrue("-L 'http://127.0.0.1:9990/console'" in res)
            self.assertTrue("--header \"Content-Type: application/json\""
                            in res)
            self.assertTrue("-d '{\"operation\": \"read-attribute\", "\
                            "\"name\": \"server-state\", \"json.pretty\": 1}'"\
                            in res)
            # We did not pass max_time so make sure it's not included
            self.assertTrue("--max-time" not in res)
        finally:
            litp_jboss.json.dumps = _old_dumps

    def test_litp_jboss__make_jboss_http_cmd_pos_02(self):
        _old_dumps = litp_jboss.json.dumps
        try:
            litp_jboss.json.dumps = self._mock_json_dumps
            self.jboss.config.get_jboss_management_url = lambda: \
                    "http://127.0.0.1:9990/console"
            args = {'operation': 'read-attribute', 'name': 'server-state'}
            res = self.jboss._make_jboss_http_cmd(args, max_time=5)
            self.assertTrue("-u mgmt87458765:mgmtpass987698768" in res)
            self.assertTrue("-L 'http://127.0.0.1:9990/console'" in res)
            self.assertTrue("--header \"Content-Type: application/json\""
                            in res)
            self.assertTrue("-d '{\"operation\": \"read-attribute\", "\
                            "\"name\": \"server-state\", \"json.pretty\": 1}'"\
                            in res, msg="Json query not in http message")
            self.assertTrue("--max-time 5" in res)
        finally:
            litp_jboss.json.dumps = _old_dumps

    def test_litp_jboss__make_jboss_http_cmd_pos_03_ipv6(self):
        _old_dumps = litp_jboss.json.dumps
        try:
            litp_jboss.json.dumps = self._mock_json_dumps
            self.jboss.config.get_jboss_management_url = lambda: \
                    "http://[fc00::ada]:9990/console"
            args = {'operation': 'read-attribute', 'name': 'server-state'}
            res = self.jboss._make_jboss_http_cmd(args, max_time=5)
            self.assertTrue("-u mgmt87458765:mgmtpass987698768" in res)
            self.assertTrue("-L 'http://[fc00::ada]:9990/console'" in res)
            self.assertTrue("--header \"Content-Type: application/json\""
                            in res)
            self.assertTrue("-d '{\"operation\": \"read-attribute\", "\
                            "\"name\": \"server-state\", \"json.pretty\": 1}'"\
                            in res, msg="Json query not in http message")
            self.assertTrue("--max-time 5" in res)
        finally:
            litp_jboss.json.dumps = _old_dumps

    def test_litp_jboss__run_jboss_http_cmd_pos_01(self):
        _old_loads = litp_jboss.json.loads
        try:
            litp_jboss.json.loads = lambda obj: {
                        "outcome": "success",
                        "result": "running"
                    }
            self.jboss._exec_cmd = lambda cmd, silent: (0, [], [])
            rc, output = self.jboss._run_jboss_http_cmd({}, None)
            self.assertEqual(rc, 0)
            self.assertEqual(output,
                    {"outcome": "success", "result": "running"})
        finally:
            litp_jboss.json.loads = _old_loads

    def test_litp_jboss__run_jboss_http_cmd_neg_01(self):
        _old_loads = litp_jboss.json.loads
        try:
            def loads_raises(obj):
                raise ValueError("mock error")
            litp_jboss.json.loads = loads_raises
            self.jboss._exec_cmd = lambda cmd, silent: (0, [], [])
            rc, output = self.jboss._run_jboss_http_cmd({}, None)
            self.assertEqual(rc, 1)
            self.assertEqual(output, None)
        finally:
            litp_jboss.json.loads = _old_loads

    def test_litp_jboss__run_jboss_http_cmd_neg_02(self):
        self.jboss._exec_cmd = lambda cmd, silent: (5, [], ["No route to host"])
        rc, output = self.jboss._run_jboss_http_cmd({}, None)
        self.assertEqual(rc, 5)
        self.assertEqual(output, "No route to host")

    def test_litp_jboss__run_jboss_http_cmd_neg_03(self):
        self.jboss._exec_cmd = lambda cmd, silent: (0, [], ["Intermittant connection"])
        rc, output = self.jboss._run_jboss_http_cmd({}, None)
        self.assertEqual(rc, 1)
        self.assertEqual(output, "Intermittant connection")

    def test_litp_jboss__check_jboss_via_http_worker_pos_01(self):
        self.jboss._run_jboss_http_cmd = lambda attrs, max_time: (0,
                {"outcome": "success", "result": "running"})
        self.assertEqual(self.jboss._check_jboss_via_http_worker(2), (0, 0))

    def test_litp_jboss__check_jboss_via_http_worker_neg_01(self):
        self.jboss._run_jboss_http_cmd = lambda attrs, max_time: (0, {})
        self.assertEqual(self.jboss._check_jboss_via_http_worker(2), (0, 1))

    def test_litp_jboss__check_jboss_via_http_worker_neg_02(self):
        self.jboss._run_jboss_http_cmd = lambda attrs, max_time: (0,
                {"outcome": "failure"})
        self.assertEqual(self.jboss._check_jboss_via_http_worker(2), (0, 1))

    def test_litp_jboss__check_jboss_via_http_worker_neg_03(self):
        self.jboss._run_jboss_http_cmd = lambda attrs, max_time: (0,
                {"outcome": "success", "res": "running"})
        self.assertEqual(self.jboss._check_jboss_via_http_worker(2), (0, 1))

    def test_litp_jboss__check_jboss_via_http_worker_neg_04(self):
        self.jboss._run_jboss_http_cmd = lambda attrs, max_time: (0,
                {"outcome": "success", "result": "stopped"})
        self.assertEqual(self.jboss._check_jboss_via_http_worker(2), (0, 1))

    def test_litp_jboss__check_jboss_via_http_worker_neg_05(self):
        self.jboss._run_jboss_http_cmd = lambda attrs, max_time: (5,
                "No route to host")
        rc, output = self.jboss._check_jboss_via_http_worker(max_time=2)
        self.assertEqual(rc, 5)
        self.assertEqual(output, "No route to host")

    def test_litp_jboss__check_jboss_via_http_pos_01(self):
        self.jboss._check_jboss_via_http_worker = lambda max_time: (0, 0)
        self.assertEqual(self.jboss._check_jboss_via_http(), (0, 0))

    def test_litp_jboss__check_jboss_via_http_neg_01(self):
        # This function is designed to take around 9 seconds, so we should
        # probably mock out the functions to stop waiting around too long
        #
        # Check that sleep is not called when there's no time to do so
        self.jboss._time = self._counter_func([0, 8.75, 8.75])
        self.jboss._sleep = self._counter_func([])
        self.jboss._check_jboss_via_http_worker = lambda max_time: (1,
                "error")
        self.assertEqual(self.jboss._check_jboss_via_http(),
                (1, "error"))
        # Check that we've called as many times as we expect
        self.assertRaises(AssertionError, self.jboss._sleep, 0.5)
        self.assertRaises(AssertionError, self.jboss._time)

    def test_litp_jboss__check_jboss_via_http_neg_02(self):
        # Check that sleep is called when there's time to do so
        self.jboss._time = self._counter_func([0, 8.25, 8.75],
                name='time.time')
        self.jboss._sleep = self._counter_func([None],
                name='jboss._sleep')
        self.jboss._check_jboss_via_http_worker = lambda max_time: (1,
                "error")
        self.assertEqual(self.jboss._check_jboss_via_http(),
                (1, "error"))
        # Check that we've called as many times as we expect
        self.assertRaises(AssertionError, self.jboss._sleep, 0.5)
        self.assertRaises(AssertionError, self.jboss._time)

    def test_litp_jboss__check_jboss_via_http_neg_03(self):
        # Check that function quits when there's no more time for a request
        self.jboss._time = self._counter_func([0, 8.49, 9.06],
                name='time.time')
        self.jboss._sleep = self._counter_func([None], name='jboss._sleep')
        self.jboss._check_jboss_via_http_worker = lambda max_time: (1,
                "error")
        self.assertEqual(self.jboss._check_jboss_via_http(),
                (1, "error"))
        # Check that we've called as many times as we expect
        self.assertRaises(AssertionError, self.jboss._sleep, 0.5)
        self.assertRaises(AssertionError, self.jboss._time)

    def test_litp_jboss__check_jboss_via_cli_pos_01(self):
        self.jboss.jbosscli.run = lambda cmd: (0, ["running"], [])
        self.assertEqual(self.jboss._check_jboss_via_cli(False), (0, 0))

    def test_litp_jboss__check_jboss_via_cli_neg_01(self):
        # cli cmd runs, reports 5, but says running
        self.jboss.jbosscli.run = lambda cmd: (5, ["running"], [])
        self.assertEqual(self.jboss._check_jboss_via_cli(False), (1, 5))

    def test_litp_jboss__check_jboss_via_cli_neg_02(self):
        # cli cmd runs, reports 0, but doesn't report running
        self.jboss.jbosscli.run = lambda cmd: (0, ["stopped"], [])
        self.assertEqual(self.jboss._check_jboss_via_cli(False), (0, 1))

    def test_litp_jboss__check_jboss_via_cli_neg_03(self):
        # cli cmd runs, reports 0, but returns nothing
        self.jboss.jbosscli.run = lambda cmd: (0, [], [])
        self.assertEqual(self.jboss._check_jboss_via_cli(False), (0, 1))

    def test_litp_jboss_restart(self):
        self.jboss._verify_pid = self._mock__verify_pid
        self.jboss._force_stop = lambda: 0
        self.jboss._exec_cmd = lambda cmd, silent=False: (0, [], [])
        self.jboss._kill_pid = lambda arg1, arg2: 0
        self.jboss._sleep = lambda wait_time: True
        self.jboss.deploy = lambda: 0
        self.jboss._run_fragments = lambda f: 0
        # ignoring the configs (not first start)
        self.jboss.setup_old_config = lambda: None
        self.jboss.set_config = lambda arg: True
        self.assertEqual(self.jboss.restart(), 0)

    def test_litp_jboss_restart_fail(self):
        self.jboss.stop = lambda: 0
        self.jboss.start = lambda: 1
        self.assertEqual(self.jboss.restart(), 1)

    def test_litp_jboss_force_restart(self):
        self.jboss._exec_cmd = self._mock__exec_cmd_ok
        self.jboss.deploy = lambda: 0
        # ignoring the configs (not first start)
        self.jboss.setup_old_config = lambda: None
        self.jboss.set_config = lambda arg: True
        self.assertEqual(self.jboss.force_restart(), 0)

    def test_litp_jboss__check_jboss_process_pos_01(self):
        self.jboss._exec_cmd = lambda cmd: (0, ['1'], [])
        self.assertEqual(self.jboss._check_jboss_process(silent=True), 0)

    def test_litp_jboss__check_jboss_process_pos_02(self):
        # cmd exits ok, but reports more than 1 process
        self.jboss._exec_cmd = lambda cmd: (0, ['2'], [])
        self.assertEqual(self.jboss._check_jboss_process(silent=True), 0)

    def test_litp_jboss__check_jboss_process_neg_01(self):
        # cmd exit status != 0
        self.jboss._exec_cmd = lambda cmd: (1, [], [])
        self.assertEqual(self.jboss._check_jboss_process(silent=True), 1)

    def test_litp_jboss__check_jboss_process_neg_02(self):
        # cmd exits ok, but something on stderr
        self.jboss._exec_cmd = lambda cmd: (0, '', ['2'])
        self.assertEqual(self.jboss._check_jboss_process(silent=False), 1)

    def test_litp_jboss_reload(self):
        self.jboss.start = lambda: 0
        # ignoring the configs (not first start)
        self.jboss.setup_old_config = lambda: None
        self.jboss.set_config = lambda arg: True
        self.assertEqual(self.jboss.reload(), 0)

    def test_litp_jboss_deploy(self):
        self.jboss._verify_pid = self._mock__verify_pid
        self.jboss._exec_cmd = self._mock__exec_cmd_ok
        self._create_install_source()
        self.jboss._run_fragments = lambda f: 0
        result = self.jboss.deploy()
        self.assertEqual(result, 0)

    def test_litp_jboss_deploy_success_homedir_already_exists(self):
        self.jboss._verify_pid = self._mock__verify_pid
        self.jboss._exec_cmd = self._mock__exec_cmd_ok
        self._create_install_source()
        self.assertEqual(self.jboss.deploy(), 0)

    def test_litp_jboss_deploy_fails(self):
        def _mock_path_exists(path):
            if path == self.jboss.config.get('install_source'):
                return True
            if path == self.jboss.config.get('home_dir'):
                return False

        def _mock_path_isfile(path):
            if path == self.jboss.config.get('install_source'):
                return True
            if path == self.jboss.config.get('home_dir'):
                return False

        tmp1 = litp_jboss.os.path.exists
        tmp2 = litp_jboss.os.path.isfile

        litp_jboss.os.path.exists = _mock_path_exists
        litp_jboss.os.path.isfile = _mock_path_isfile
        # run frag pre deploy fails
        self.jboss._run_fragments = lambda f: 1
        self.assertEqual(self.jboss._deploy(), 1)
        # maketempdir fails
        self.jboss._run_fragments = lambda f: 0
        self.jboss._maketempdir = lambda: (1, '/tmp/foo/bar')
        self.assertEqual(self.jboss._deploy(), 1)
        # makehomeDIR fails
        self.jboss._maketempdir = lambda: (0, '/tmp/foo/bar')
        self.jboss._makehomedir = lambda: 1
        self.assertEqual(self.jboss._deploy(), 1)
        # untar and move fails
        self.jboss._makehomedir = lambda: 0
        self.jboss._untar_and_move = lambda p: 1
        self.assertEqual(self.jboss._deploy(), 1)
        # _add_management_user fails
        self.jboss._untar_and_move = lambda p: 0
        self.jboss._add_management_user = lambda: 1
        self.assertEqual(self.jboss._deploy(), 1)
        # _untar_support_packages_fails
        self.jboss._add_management_user = lambda: 0
        self.jboss._untar_support_packages = lambda: 1
        self.assertEqual(self.jboss._deploy(), 1)

        # run frag post deploy fails
        def _mock_run_fragments_1(f):
            if f == 'post_deploy':
                return 1
            else:
                return 0
        self.jboss._update_perms = lambda p: 0
        self.jboss._run_fragments = _mock_run_fragments_1
        self.jboss._untar_support_packages = lambda: 0
        self.assertEqual(self.jboss._deploy(), 1)
        # and... utter success
        self.jboss._run_fragments = lambda f: 0
        self.assertEqual(self.jboss._deploy(), 0)
        # cleanup
        litp_jboss.os.path.exists = tmp1
        litp_jboss.os.path.isfile = tmp2

    def _do_deploy_fail_with_makedirs(self, mock_makedirs):
        self.jboss._verify_pid = self._mock__verify_pid
        self.jboss._exec_cmd = self._mock__exec_cmd_ok
        self._create_install_source()
        try:
            tmp = litp_jboss.os.path.exists
            litp_jboss.os.path.exists = lambda path: False
            old_makedirs = litp_jboss.os.makedirs
            litp_jboss.os.makedirs = mock_makedirs
            self.assertEqual(self.jboss.deploy(), 1)
        finally:
            litp_jboss.os.makedirs = old_makedirs
            litp_jboss.os.path.exists = tmp

    def _mock_makedirs_always_fail(self, path):
        e = OSError()
        e.errno = 1
        e.strerror = 'Permission denied'
        raise e

    def test_litp_jboss_deploy_fail_making_temmpath(self):
        try:
            old_exists = litp_jboss.os.path.exists

            def mock_exists(path):
                if path == '/tmp/jboss':
                    return False
                else:
                    return old_exists(path)

            litp_jboss.os.path.exists = mock_exists
            self._do_deploy_fail_with_makedirs(self._mock_makedirs_always_fail)
        finally:
            litp_jboss.os.path.exists = old_exists

    def test_litp_jboss_deploy_fail_making_homedir(self):
        real_makedirs = os.makedirs

        def mock_makedirs(path):
            if path == self.jboss.config.get('home_dir'):
                e = OSError()
                e.errno = 1
                e.strerror = 'Permission denied'
                raise e
            else:
                return real_makedirs(path)

        self._do_deploy_fail_with_makedirs(mock_makedirs)

    def test_litp_jboss_deploy_fail_untarring(self):
        self.jboss._verify_pid = self._mock__verify_pid
        self._create_install_source()
        try:
            old_exists = litp_jboss.os.path.exists
            litp_jboss.os.path.exists = lambda path: False
            old_makedirs = litp_jboss.os.makedirs
            litp_jboss.os.makedirs = lambda path: None
            self.assertEqual(self.jboss.deploy(), 1)
        finally:
            litp_jboss.os.makedirs = old_makedirs
            litp_jboss.os.path.exists = old_exists

    @mock.patch("os.path.isdir")
    @mock.patch("os.path.isfile")
    @mock.patch("os.path.exists")
    @mock.patch("shutil.rmtree")
    @mock.patch("litpmnjboss.litp_jboss_common.run_fragments")
    @mock.patch("litpmnjboss.litp_jboss_common.remove_directory")
    def test_litp_jboss_undeploy_success(self, mock_rmdir, mock_run_frag, mock_rmtree, mock_os_exists, mock_os_isfile, mock_os_isdir):
        mock_os_isdir.side_effect = lambda d: d == self.jboss.config.get("home_dir")
        mock_os_isfile.side_effect = lambda f: f == self.jboss._jboss_script
        mock_os_exists.return_value = True
        mock_rmtree.return_value = None
        mock_run_frag.return_value = 0
        mock_rmdir.return_value = 0

        self.jboss.stop = lambda silent: 0
        self.jboss._sleep = lambda wait_time: None
        self.jboss._kill_pid = lambda pid, sig: 0
        # assume we are running
        self.jboss._verify_pid = self._mock__verify_pid
        # ignoring the configs (not first start)
        self.jboss.setup_old_config = lambda: None
        self.jboss.set_config = lambda arg: True
        self.jboss.config.remove_config = lambda: None
        self.assertEqual(0, self.jboss.undeploy(\
                                remove_state_dir=False))
        self.assertEqual(0, self.jboss.undeploy())

    @mock.patch("os.path.isdir")
    @mock.patch("os.path.isfile")
    @mock.patch("os.path.exists")
    def test_litp_jboss_undeploy_already_undeployed(self, mock_os_exists, mock_os_isfile, mock_os_isdir):
        mock_os_isdir.side_effect = lambda d: d != self.jboss.config.get("home_dir")
        mock_os_exists.side_effect = lambda f: f == self.jboss.config.get("home_dir")
        mock_os_isfile.side_effect = lambda f: self.fail()

        # ignoring the configs (not first start)
        self.jboss.setup_old_config = lambda: None
        self.jboss.set_config = lambda arg: True
        self.jboss.config.remove_config = lambda: None
        #self.test_litp_jboss_undeploy_success()
        self.assertEqual(0, self.jboss.undeploy(\
                                remove_state_dir=False))
        self.assertEqual(0, self.jboss.undeploy())

    @mock.patch("os.path.isdir")
    @mock.patch("os.path.isfile")
    @mock.patch("os.path.exists")
    @mock.patch("litpmnjboss.litp_jboss_common.run_fragments")
    @mock.patch("litpmnjboss.litp_jboss_common.remove_directory")
    def test_litp_jboss_undeploy_fails(self, mock_rmdir, mock_run_frag, mock_os_exists, mock_os_isfile, mock_os_isdir):
        # ignoring the configs (not first start)
        self.jboss.setup_old_config = lambda: None
        self.jboss.set_config = lambda arg: True
        self.jboss.config.remove_config = lambda: None
        mock_os_exists.return_value = True
        mock_os_isdir.return_value = True
        # fail on check for jboss script
        mock_os_isfile.return_value = False
        self.assertEqual(1, self.jboss.undeploy())
        mock_os_isfile = lambda p: True
        self.jboss.stop = lambda silent: 0
        self.jboss._run_fragments = lambda a: 0

        def _mock_raises(self):
            raise OSError()

        self.assertEqual(1, self.jboss.undeploy())
        # test failed remove of data dir
        mock_rmdir.side_effect = lambda f: 1 if 'data' in f else 0
        self.assertEqual(1, self.jboss.undeploy())
        # test failed pre_undeploy run fragment
        self.jboss._run_fragments = lambda f: 1 \
                                        if f == 'pre_undeploy' else 0
        self.assertEqual(1, self.jboss.undeploy())
        self.jboss.config.remove_config = lambda: None
        # test failed pre_undeploy run fragment
        self.jboss._run_fragments = lambda f: 1 \
                                        if f == 'post_undeploy' else 0
        self.assertEqual(1, self.jboss.undeploy())

    def test_litp_jboss_upgrade(self):
        # set old version to different value
        self.jboss._get_current_value = lambda x: '1.0.1' \
                        if x == 'version' else  None
        self.jboss.deploy = lambda: 0  # deploy ok
        self.jboss.undeploy = lambda remove_state_dir: 0  # undeploy ok
        # ignoring the configs (not first start)
        self.jboss.setup_old_config = lambda: None
        self.jboss.set_config = lambda arg: True
        # fail when run fragments failes
        self.jboss._run_fragments = lambda f: 1
        self.assertEqual(self.jboss.upgrade(), 1)
        self.jboss._run_fragments = lambda f: 0 if f == 'pre_upgrade' else 1
        self.assertEqual(self.jboss.upgrade(), 1)
        # successfully upgrade case
        self.jboss._run_fragments = lambda f: 0
        self.assertEqual(self.jboss.upgrade(), 0)
        # test undeploy fail
        self.jboss.undeploy = lambda remove_state_dir: 1  # undeploy failed
        self.assertEqual(self.jboss.upgrade(), 1)
        # test deploy fail
        self.jboss.undeploy = lambda remove_state_dir: 0
        self.jboss.deploy = lambda: 1
        self.assertEqual(self.jboss.upgrade(), 1)
        # test empty version
        self.jboss._get_current_value = lambda x: '' \
                                if x == 'version' else None
        self.assertEqual(self.jboss.upgrade(), 1)

        self.jboss.deploy = lambda: 0  # deploy ok
        self.jboss.undeploy = lambda remove_state_dir: 1  # undeploy failed
        self.assertEqual(self.jboss.upgrade(), 1)

        # Test version already installed (version == current_version)
        self.jboss.setup_new_config()

        def _mock_get_current_value_1(prop):
            if prop == 'version':
                return self.jboss.config.get(prop)
            elif prop == 'install_source':
                return self.jboss.config.get(prop)
            else:
                return None
        self.jboss._get_current_value = _mock_get_current_value_1
        self.assertEqual(self.jboss.upgrade(), 1)

        # Test failed undeploy of old version
        self.jboss.version = '1.2.1'
        self.jboss.undeploy = lambda remove_state_dir: 1  # undeploy failed
        self.assertEqual(self.jboss.upgrade(), 1)

        # Test failed deploy of new version
        self.jboss.version = '1.2.1'

        def _mock_get_current_value_2(prop):
            if prop == '1.0.1':  # != self.version
                return self.jboss.config.get(prop)
            elif prop == 'install_source':
                return self.jboss.config.get(prop)
            else:
                return None
        self.jboss.get_current_value = _mock_get_current_value_2
        self.jboss.undeploy = lambda remove_state_dir: 0  # undeploy success
        self.jboss.deploy = lambda: 1  # deploy failed
        self.assertEqual(self.jboss.upgrade(), 1)

    def _run_command_test(self, cmd, expected_result):
        litp_jboss.sys.argv = ['litp_jboss.py', ]
        if cmd is not None:
            litp_jboss.sys.argv.append(cmd)
            setattr(self.jboss, cmd.replace('-', '_'), lambda: 0)

        try:
            self.jboss.main()
        except SystemExit, e:
            self.assertEqual(type(e), type(SystemExit()))
            self.assertEqual(e.code, expected_result)
        else:
            self.fail('SystemExit exception expected')

    def test_litp_jboss_main(self):
        # Test missing command
        self._run_command_test(None, 2)

        # Test valid commands
        for cmd in ['start', 'stop', 'force-stop', 'restart', 'force-restart',
                    'reload', 'status', 'deploy', 'undeploy', 'upgrade']:
            self._run_command_test(cmd, 0)

        # Test invalid command
        self._run_command_test('foobar', 2)

    def _do_check_vars_test(self, env_dict, message, exit_status):
        try:
            sys.stdout.flush()
            old_stdout = sys.stdout
            sys.stdout = StringIO()
            got_exit = False

            config = litp_jboss_config.LitpJbossConfig(config_dict=env_dict)
            jboss = litp_jboss.LitpJboss(config)
            jboss.start = lambda: 0
            litp_jboss.sys.argv = ['litp_jboss.py', 'start']

            jboss.main()
        except SystemExit as e:
            got_exit = True
            self.assertEqual(type(e), type(SystemExit()))
            self.assertEqual(e.code, exit_status)
        finally:
            output = sys.stdout.getvalue()
            sys.stdout.close()
            sys.stdout = old_stdout
            if message is None:
                self.assertEqual(output, "")
            else:
                self.assertEqual(output, message + "\n")

        if not got_exit:
            self.fail('SystemExit exception expected')

    def test_check_vars_no_home_dir(self):
        env_dict = self._make_env_dict()
        del env_dict['LITP_JEE_CONTAINER_home_dir']
        self._do_check_vars_test(env_dict,
                        "Please specify JBoss home-dir", 1)

    def test_check_vars_no_install_source(self):
        env_dict = self._make_env_dict()
        del env_dict['LITP_JEE_CONTAINER_install_source']
        self._do_check_vars_test(env_dict,
                        "Please specify JBoss install source", 1)

    def test_check_vars_no_version(self):
        env_dict = self._make_env_dict()
        del env_dict['LITP_JEE_CONTAINER_version']
        self._do_check_vars_test(env_dict,
                        "Please specify application version", 1)

    def test_check_vars_no_instance_name(self):
        env_dict = self._make_env_dict()
        del env_dict['LITP_JEE_CONTAINER_instance_name']
        self._do_check_vars_test(env_dict,
                        "Please specify JBoss instance-name", 1)

    def test_check_vars_no_management_listener(self):
        env_dict = self._make_env_dict()
        del env_dict['LITP_JEE_CONTAINER_management_listener']
        self._do_check_vars_test(env_dict,
                        "Please specify management listener", 1)

    def test_check_vars_no_public_listener(self):
        env_dict = self._make_env_dict()
        del env_dict['LITP_JEE_CONTAINER_public_listener']
        self._do_check_vars_test(env_dict, "Please specify public listener", 1)

    def test_check_vars_no_management_user(self):
        env_dict = self._make_env_dict()
        del env_dict['LITP_JEE_CONTAINER_management_user']
        self._do_check_vars_test(env_dict,
                        "Please specify JBoss management user", 1)

    def test_check_vars_no_management_password(self):
        env_dict = self._make_env_dict()
        del env_dict['LITP_JEE_CONTAINER_management_password']
        self._do_check_vars_test(env_dict,
                        "Please specify JBoss management password", 1)

    def test_check_vars_no_process_user(self):
        env_dict = self._make_env_dict()
        del env_dict['LITP_JEE_CONTAINER_process_user']
        self._do_check_vars_test(env_dict,
                        "Please specify process user", 1)

    def test_check_vars_no_process_group(self):
        env_dict = self._make_env_dict()
        del env_dict['LITP_JEE_CONTAINER_process_group']
        self._do_check_vars_test(env_dict,
                        "Please specify process group", 1)

    def test_check_vars_positive(self):
        env_dict = self._make_env_dict()
        self._do_check_vars_test(env_dict, None, 0)

    def test_start_all_apps_success(self):
        try:
            jboss = litp_jboss.LitpJboss(self._make_jboss_with_apps_config())
            self.assertEqual(len(jboss.config.apps), 3)
            for app in jboss.config.apps:
                # touch files
                open(app.get('install_source'), 'w').close()

            tmp1 = litp_jboss_app.LitpJbossApp.start
            tmp2 = litp_jboss_app.LitpJbossApp.stop
            litp_jboss_app.LitpJbossApp.start = lambda k, arg: 0
            litp_jboss_app.LitpJbossApp.stop = lambda k, arg: 0

            result = jboss._start_all_apps()
            self.assertEqual(result, 0)
        finally:
            litp_jboss_app.LitpJbossApp.start = tmp1
            litp_jboss_app.LitpJbossApp.stop = tmp2
            for apps in jboss.config.apps:
                f = app.get('install_source')
                if os.path.exists(f):
                    os.remove(f)

    def test_start_all_apps_failure(self):
        try:
            jboss = litp_jboss.LitpJboss(self._make_jboss_with_apps_config())
            tmp1 = litp_jboss_app.LitpJbossApp.start
            litp_jboss_app.LitpJbossApp.start = lambda arg, arg2: 1

            tmp2 = litp_jboss_app.LitpJbossApp.get_install_file
            litp_jboss_app.LitpJbossApp.get_install_file = lambda a: 'foo'

            self.assertEqual(len(jboss.config.apps), 3)
            self.assertEqual(jboss._start_all_apps(), 1)
        finally:
            litp_jboss_app.LitpJbossApp.start = tmp1
            litp_jboss_app.LitpJbossApp.get_install_file = tmp2

    def test_stop_all_apps_pos_01(self):
        tmp1 = litp_jboss_app.LitpJbossApp.stop
        tmp2 = litp_jboss_app.LitpJbossApp.get_install_file
        try:
            jboss = litp_jboss.LitpJboss(self._make_jboss_with_apps_config())
            jboss._sleep = lambda seconds: None
            jboss._time = self._counter_func([0, 150, 300, 450, 600, 750, 900]
                    * 3)
            self.assertEqual(len(jboss.config.apps), 3)

            litp_jboss_app.LitpJbossApp.stop = lambda arg: 2

            litp_jboss_app.LitpJbossApp.get_install_file = lambda a: 'foo'

            # Just make sure no exception is raised
            result = jboss._stop_all_apps()
            # Now check we've called as many times as we expected
            # the next call to jboss._time should raise an assertionError
            self.assertRaises(AssertionError, jboss._time)
        finally:
            litp_jboss_app.LitpJbossApp.stop = tmp1
            litp_jboss_app.LitpJbossApp.get_install_file = tmp2

    def test_stop_all_apps_pos_02(self):
        # Make sure stop all apps only tries to stop each app once
        tmp1 = litp_jboss_app.LitpJbossApp.stop
        tmp2 = litp_jboss_app.LitpJbossApp.get_install_file
        try:
            jboss = litp_jboss.LitpJboss(self._make_jboss_with_apps_config())
            jboss._sleep = lambda seconds: None
            jboss._time = self._counter_func([0]
                    * 3)
            self.assertEqual(len(jboss.config.apps), 3)

            litp_jboss_app.LitpJbossApp.stop = lambda arg: 0

            litp_jboss_app.LitpJbossApp.get_install_file = lambda a: 'foo'

            # Just make sure no exception is raised
            result = jboss._stop_all_apps()
            # Now check we've called as many times as we expected
            # the next call to jboss._time should raise an assertionError
            self.assertRaises(AssertionError, jboss._time)
        finally:
            litp_jboss_app.LitpJbossApp.stop = tmp1
            litp_jboss_app.LitpJbossApp.get_install_file = tmp2

    def test_stop_all_apps_pos_03(self):
        # Make sure stop_all_apps only tries to stop non-timing out apps once
        tmp1 = litp_jboss_app.LitpJbossApp.stop
        tmp2 = litp_jboss_app.LitpJbossApp.get_install_file
        try:
            jboss = litp_jboss.LitpJboss(self._make_jboss_with_apps_config())
            jboss._sleep = lambda seconds: None
            jboss._time = self._counter_func([0]
                    * 3)
            self.assertEqual(len(jboss.config.apps), 3)

            litp_jboss_app.LitpJbossApp.stop = lambda arg: 1

            litp_jboss_app.LitpJbossApp.get_install_file = lambda a: 'foo'

            # Just make sure no exception is raised
            result = jboss._stop_all_apps()
            # Now check we've called as many times as we expected
            # the next call to jboss._time should raise an assertionError
            self.assertRaises(AssertionError, jboss._time)
        finally:
            litp_jboss_app.LitpJbossApp.stop = tmp1
            litp_jboss_app.LitpJbossApp.get_install_file = tmp2

    def test_install_sps_success(self):
        num_sps = 2
        try:
            jboss = litp_jboss.LitpJboss(
                                self._make_jboss_with_apps_config(num_sps))
            self.assertEqual(len(jboss.config.support_packages), num_sps)
            for sp in jboss.config.support_packages:
                # touch files
                open(sp.get('install_source'), 'w').close()

            mocked_cmds = []

            def _mock_exec_cmd(cmd):
                mocked_cmds.append(cmd)
                return (0, [], [])

            tmp1 = jboss._exec_cmd
            jboss._exec_cmd = _mock_exec_cmd
            result = jboss._untar_support_packages()
            self.assertEqual(result, 0)

            # verify commands that were run (i.e. mocked)
            expected_cmds = []
            for i in range(num_sps):
                expected_cmds.append('tar -xzf /tmp/sp%d.tgz -C %s' % \
                                     (i, jboss.module_dir))
            self.assertEqual(mocked_cmds, expected_cmds)
        finally:
            jboss._exec_cmd = tmp1
            for sp in jboss.config.support_packages:
                f = sp.get('install_source')
                if os.path.exists(f):
                    os.remove(f)

    def test_install_sps_failure(self):
        num_sps = 2
        try:
            jboss = litp_jboss.LitpJboss(
                                self._make_jboss_with_apps_config(num_sps))
            self.assertEqual(len(jboss.config.support_packages), num_sps)
            for sp in jboss.config.support_packages:
                # touch files
                open(sp.get('install_source'), 'w').close()

            mocked_cmds = []

            def _mock_exec_cmd(cmd):
                return (1, [], ['a bad thing happened...\n'])

            tmp1 = jboss._exec_cmd
            jboss._exec_cmd = _mock_exec_cmd
            result = jboss._untar_support_packages()
            self.assertEqual(result, 1)
        finally:
            jboss._exec_cmd = tmp1
            for sp in jboss.config.support_packages:
                f = sp.get('install_source')
                if os.path.exists(f):
                    os.remove(f)

    def _pidfile_exists(self, jboss):
        return (os.path.exists(jboss._pidfile) and \
                 os.path.isfile(jboss._pidfile))

    def test_litp_jboss__run_daemon(self):
        jboss = litp_jboss.LitpJboss(self._make_jboss_with_apps_config())

        def mock_Popen(cmd, env={}, shell=True):
            class MockProcess(object):
                def __init__(self, pid):
                    self.pid = pid

            return MockProcess(1234)

        try:
            old_Popen = litp_jboss.subprocess.Popen
            litp_jboss.subprocess.Popen = mock_Popen
            result = jboss._run_daemon()
            self.assertEqual(result, 0)
        finally:
            litp_jboss.subprocess.Popen = old_Popen

    def test_litp_jboss__run_daemon_failed(self):
        def mock_Popen(cmd, env={}, shell=True):
            class MockProcess(object):
                def __init__(self, pid):
                    raise Exception()

            return MockProcess(1234)
        try:
            old_Popen = litp_jboss.subprocess.Popen
            litp_jboss.subprocess.Popen = mock_Popen

            result = self.jboss._run_daemon()
            self.assertEqual(result, 1)
        finally:
            litp_jboss.subprocess.Popen = old_Popen

#    def test_litp_jboss__run_fragments(self):
#        frag_path = os.path.join(self._tmppath, 'pre-deploy')
#        frags = ('script1', 'script2', 'script3', 'script4')
#        if not os.path.exists(frag_path):
#            os.makedirs(frag_path)
#        for f in frags:
#            f1 = os.path.join(frag_path, f)
#            if not os.path.exists(f1):
#                with open(f1, 'w') as s:
#                    s.write('echo "foo bar runnin\'..."')
#                os.chmod(f1, 0777)
#        self.jboss.config.config['pre_deploy'] = frag_path
#        result = self.jboss._run_fragments('pre_deploy')
#        self.assertEqual(result, 0)

    def test_litp_jboss__run_fragments_no_path(self):
        self.jboss.config.config['pre_deploy'] = \
                            '/t1m2p3f/4o5o6b7a8r9/f0oo1b2a3z4p5a6th'
        result = self.jboss._run_fragments('pre_deploy')
        self.assertEqual(result, 1)

    def test_litp_jboss__run_fragments_no_access(self):
        self.jboss.config.config['pre_deploy'] = self._tmppath
        if not os.path.exists(self._tmppath):
            os.makedirs(self._tmppath)

        orig = litp_jboss.os.access
        litp_jboss.os.access = lambda a1, a2: False
        result = self.jboss._run_fragments('pre_deploy')
        self.assertEqual(result, 1)
        litp_jboss.os.access = orig

    def test_old_config_none(self):
        self.jboss.old_config = None
        try:
            self.jboss.setup_old_config()
        except SystemExit as e:
            self.assertEqual(type(e), type(SystemExit()))
            self.assertEqual(e.code, 1)

    def test_cleanup_failed_start(self):
        self.jboss.config.remove_lock = lambda: None
        self.assertEqual(self.jboss._cleanup_failed_start(), 0)

    def test_cleanup_failed_start_fails(self):
        def _mock_exception(path):
            raise OSError()
        tmp1 = litp_jboss.shutil.rmtree
        try:
            litp_jboss.shutil.rmtree = _mock_exception
            self.jboss._cleanup_failed_start()
        except OSError as e:
            print e
            self.assertEqual(type(e), type(Exception()))
        finally:
            litp_jboss.shutil.rmtree = tmp1

    def test_remove_old_apps(self):
        from copy import deepcopy
        tmp1 = litp_jboss_app.LitpJbossApp.get_install_file
        litp_jboss_app.LitpJbossApp.get_install_file = lambda arg: 'foo'
        try:
            jboss = litp_jboss.LitpJboss(self._make_jboss_with_apps_config())
            jboss.old_config = deepcopy(jboss.config)
            jboss.config.apps.pop(-1)
            jboss.new_config = deepcopy(jboss.config)

            self.assertEqual(jboss._remove_old_apps(), 0)
        finally:
            litp_jboss_app.LitpJbossApp.get_install_file = tmp1

    def test_makehomedir(self):
        t1 = litp_jboss.os.path.exists
        litp_jboss.os.path.exists = lambda p: False
        t2 = litp_jboss.os.makedirs
        litp_jboss.os.makedirs = self._mock_makedirs_always_fail
        try:
            # negative
            self.assertEqual(self.jboss._makehomedir(), 1)
            # positive
            litp_jboss.os.makedirs = lambda a: None
            self.assertEqual(self.jboss._makehomedir(), 0)
            # positive 2
            litp_jboss.os.path.exists = lambda p: True
            self.assertEqual(self.jboss._makehomedir(), 0)

        finally:
            litp_jboss.os.path.exists = t1
            litp_jboss.os.makedirs = t2

    def test_maketempdir(self):
        t1 = litp_jboss.os.path.exists
        litp_jboss.os.path.exists = lambda p: False
        t2 = litp_jboss.os.makedirs
        litp_jboss.os.makedirs = self._mock_makedirs_always_fail
        try:
            # positive
            self.assertEqual(self.jboss._maketempdir(), (1, None))
            # negative
            litp_jboss.os.path.exists = lambda p: True
            self.assertEqual(self.jboss._maketempdir()[0], 0)
        finally:
            litp_jboss.os.path.exists = t1
            litp_jboss.os.makedirs = t2

    def test_add_management_user(self):
        # positive
        self.jboss._exec_cmd = lambda cmd: (0, [], [])
        self.assertEqual(self.jboss._add_management_user(), 0)
        # negative
        self.jboss._exec_cmd = lambda cmd: (1, [], [])
        self.assertEqual(self.jboss._add_management_user(), 1)

    def test_remove_management_user(self):
        (fd, temp_mgmt_user_file) = tempfile.mkstemp(prefix="mgmt_users",
                                                     dir='/tmp')
        f = open(temp_mgmt_user_file, "w")
        f.write('admin1=asdgf')
        f.write('admin1234=asdgf')
        f.close()
        self.jboss._mgmt_user_files = [temp_mgmt_user_file]
        # negative
        self.jboss._remove_management_user('admin_123')
        for filename in self.jboss._mgmt_user_files:
            f = open(filename, "r")
            self.assertTrue('admin1' in f.read())
            f.close()
        # positive
        self.jboss._remove_management_user('admin1')
        for filename in self.jboss._mgmt_user_files:
            f = open(filename, "r")
            self.assertTrue('admin1' not in f.read())
            f.close()

    def test_untar_and_move(self):
        temppath = '/foo/bar'
        # positive
        self.jboss._exec_cmd = lambda cmd: (0, [], [])
        self.assertEqual(self.jboss._untar_and_move(temppath), 0)
        # negative
        self.jboss._exec_cmd = lambda cmd: (1, [], [])
        self.assertEqual(self.jboss._untar_and_move(temppath), 1)

    def test_clean_temp(self):
        tmp1 = litp_jboss.shutil.rmtree
        temppath = '/tmp/foo/bar'
        try:
            # positive
            litp_jboss.shutil.rmtree = lambda arg: None
            self.assertEqual(self.jboss._clean_temp(temppath), None)

            # negative
            def _mock_raises(path):
                raise OSError()
            litp_jboss.shutil.rmtree = _mock_raises
            self.assertEqual(self.jboss._clean_temp(temppath), None)
        finally:
            litp_jboss.shutil.rmtree = tmp1

    def test_get_cmd_line_options__no_default_config(self):
        self.jboss._jboss_configuration_file = None
        opt_str = self.jboss._get_cmd_line_options()
        self.assertTrue('--server-config=' not in opt_str)

    def test_get_cmd_line_options__default_config(self):
        self.jboss._jboss_configuration_file = 'test.xml'
        opt_str = self.jboss._get_cmd_line_options()
        self.assertTrue('--server-config=test.xml' in opt_str)

    def test_get_cmd_line_options__user_specified_config(self):
        self.jboss._jboss_configuration_file = 'test.xml'
        self.jboss.config.config['command_line_options'] = \
                '--server-config=user.xml'
        opt_str = self.jboss._get_cmd_line_options()
        self.assertTrue('--server-config=user.xml' in opt_str)
        self.assertTrue('--server-config=test.xml' not in opt_str)

    def test_get_environment_formats_none_values_as_empty_strings(self):
        self.assertTrue(self.jboss.config.get('Xms') is None)
        self.assertTrue(self.jboss.config.get('Xmx') is None)
        self.assertTrue(self.jboss.config.get('MaxPermSize') is None)
        self.assertFalse('None' in self.jboss._get_environment())
        self.assertEqual('JAVA_OPTS=""', self.jboss._get_environment())

    def test_get_environment_returns_correctly_formatted_java_opts(self):
        xoptions = '-Xfoo -XX:foo=bar'
        self.jboss.config.config['java_options'] = xoptions
        xms = '1024M'
        self.jboss.config.config['Xms'] = xms
        xmx = '1024M'
        self.jboss.config.config['Xmx'] = xmx
        max_perm_size = '256M'
        self.jboss.config.config['MaxPermSize'] = max_perm_size

        expected = 'JAVA_OPTS="%s -Xms%s -Xmx%s -XX:MaxPermSize=%s"' % (
            xoptions, xms, xmx, max_perm_size)
        self.assertEqual(expected, self.jboss._get_environment())

    def test__get_deployable_entity_states_pos_01(self):
        # Make sure we get a dict indexed by deployed DEs with a boolean
        # telling us if its running
        curl_results = {
            "outcome" : "success",
            "result" : {
                "alice.war" : {
                    "content" : [{"hash" : {
                        "BYTES_VALUE" : "O5tXLz1wG0AUQWgtJ7j//gBlkPw="
                    }}],
                    "enabled" : False,
                    "name" : "alice.war",
                    "persistent" : True,
                    "runtime-name" : "alice.war",
                    "status" : "STOPPED",
                    "subdeployment" : None,
                    "subsystem" : None,
                },
                "bob.ear" : {
                    "content" : [{"hash" : {
                        "BYTES_VALUE" : "A2pFL3wSARwwD4JCyGq1woveA8M="
                    }}],
                    "enabled" : True,
                    "name" : "bob.ear",
                    "persistent" : True,
                    "runtime-name" : "bob.ear",
                    "status" : "OK",
                    "subsystem" : None,
                    "subdeployment" : {
                        "jbossExampleLog4jApp-war.war" : None,
                        "jbossExampleLog4jApp-ejb-1.1.jar" : None,
                    }
                }
            }
        }
        self.jboss._query_deployable_entity_states = lambda max_time: (0,
                curl_results)
        self.assertEqual(self.jboss._get_deployable_entity_states(), 
                {'alice.war': False, 'bob.ear': True}) 

        pass

    def test__get_deployable_entity_states_neg_01(self):
        # Make sure we return an empty dict if we don't get a connection
        self.jboss._query_deployable_entity_states = lambda max_time: (7,
                "Failed to connect to host")
        self.assertEqual(self.jboss._get_deployable_entity_states(), {})

    def test__query_deployable_entity_states_pos_01(self):
        # Check that we return success when we encounter it
        self.jboss._run_jboss_http_cmd = lambda *args, **kwargs: (0, 
                {"outcome": "success"})
        self.assertEqual((0, {"outcome": "success"}),
                self.jboss._query_deployable_entity_states())

    def test__query_deployable_entity_states_pos_02(self):
        # Check that we retry and return only success
        self.jboss._sleep = lambda *args: None
        self.jboss._run_jboss_http_cmd = self._counter_func([
            (7, "Failed to connect to host"), (0, {"outcome": "success"})])
        self.assertEqual((0, {"outcome": "success"}),
                self.jboss._query_deployable_entity_states())

    def test__query_deployable_entity_states_neg_01(self):
        # Make sure we return a failure after we exceed attempts
        self.jboss._sleep = lambda *args: None
        self.jboss._run_jboss_http_cmd = self._counter_func([
                (7, "Failed to connect to host") for _ in range(10)])
        self.assertEqual(self.jboss._query_deployable_entity_states(),
                (7, "Failed to connect to host"))
        # Check we've tried all 10 times
        self.assertRaises(AssertionError, self.jboss._run_jboss_http_cmd)

    def test__calculate_timeout_pos_01(self):
        running_des = ['alice.war', 'bob.ear']
        self.assertEqual(450, self.jboss._calculate_timeout(running_des))

    def test__calculate_timeout_pos_02(self):
        running_des = []
        self.assertEqual(0, self.jboss._calculate_timeout(running_des))

    def test__calculate_timeout_pos_03(self):
        running_des = ['alice.war']
        self.assertEqual(330, self.jboss._calculate_timeout(running_des))

    def test__get_running_des_pos_01(self):
        self.jboss1 = litp_jboss.LitpJboss(self._make_jboss_with_apps_config())
        self.jboss1._get_deployable_entity_states = lambda query_time=60: dict(
                [(app.get('name'), True) for app in self.jboss1.config.apps])
        res = self.jboss1._get_running_des()
        res_names = [de.get('name') for de in res]
        self.assertEqual(['jeede3', 'jeede2', 'jeede1'], res_names)

    def test__get_running_des_pos_02(self):
        self.jboss1 = litp_jboss.LitpJboss(self._make_jboss_with_apps_config())
        self.jboss1._get_deployable_entity_states = lambda query_time=60: dict(
                [(app.get('name'), False) for app in self.jboss.config.apps])
        self.assertEqual(self.jboss1._get_running_des(), [])

    def test__get_running_des_pos_03(self):
        self.jboss1 = litp_jboss.LitpJboss(self._make_jboss_with_apps_config())
        self.jboss1._get_deployable_entity_states = lambda query_time=60: {
                'jeede4': True }
        self.assertEqual(self.jboss1._get_running_des(), [])

    def test__get_running_des_pos_04(self):
        self.jboss1 = litp_jboss.LitpJboss(self._make_jboss_with_apps_config())
        self.jboss1._get_deployable_entity_states = lambda query_time=60: {}
        self.assertEqual(self.jboss1._get_running_des(), [])

    def test__get_running_des_pos_05(self):
        self.jboss1 = litp_jboss.LitpJboss(self._make_jboss_with_apps_config())
        self.jboss1._get_deployable_entity_states = lambda query_time=60: {
                'jeede1': True}
        res_names = [de.get('name') for de in self.jboss1._get_running_des()]
        self.assertEqual(res_names, ['jeede1'])

    def test__create_batch_cli_cmds_pos_01(self):
        self.assertEqual(self.jboss._create_batch_cli_commands([]), [])

    def test__create_batch_cli_cmds_pos_02(self):
        self.jboss1 = litp_jboss.LitpJboss(self._make_jboss_with_apps_config())
        self.assertEqual(
               self.jboss1._create_batch_cli_commands(self.jboss1.config.apps),
               ['undeploy --name=%s --keep-content' % app.get('name') for app 
                   in self.jboss1.config.apps])

    def test__run_app_hooks_batch_pos_01(self):
        def _(inst, fragment_name):
            self.fail("should not be called")
        old_run_frag = litp_jboss.litp_jboss_app.LitpJbossApp._run_fragments
        try:
            litp_jboss.litp_jboss_app.LitpJbossApp._run_fragments = _
            self.jboss._run_app_hooks_batch("post_shutdown", 
                self.jboss.config.apps)
        finally:
            litp_jboss.litp_jboss_app.LitpJbossApp._run_fragments = \
                    old_run_frag

    def test__run_app_hooks_batch_pos_02(self):
        self.jboss1 = litp_jboss.LitpJboss(self._make_jboss_with_apps_config())
        apps_called = []
        def _(inst, fragment_name):
            apps_called.append(inst.config.get('name'))
            
        old_run_frag = litp_jboss.litp_jboss_app.LitpJbossApp._run_fragments
        try:
            litp_jboss.litp_jboss_app.LitpJbossApp._run_fragments = _
            self.jboss._run_app_hooks_batch("post_shutdown", 
                self.jboss1.config.apps)
            self.assertEqual(apps_called, ['jeede1', 'jeede2', 'jeede3'])
        finally:
            litp_jboss.litp_jboss_app.LitpJbossApp._run_fragments = \
                    old_run_frag

    def test__stop_all_apps_batch_pos_01(self):
        # Check that _stop_all_apps_batch returns solely on the results of
        # _stop_all_apps_batch_worker
        self.jboss1 = litp_jboss.LitpJboss(self._make_jboss_with_apps_config())
        self.jboss1._get_running_des = lambda: self.jboss1.config.apps
        self.jboss1._run_app_hooks_batch = lambda stage, running_des: None
        self.jboss1._stop_all_apps_batch_worker = lambda running_des: False
        self.assertEqual(self.jboss1._stop_all_apps_batch(), False)

    def test__stop_all_apps_batch_pos_02(self):
        # Check that _stop_all_apps_batch returns solely on the results of
        # _stop_all_apps_batch_worker
        self.jboss1 = litp_jboss.LitpJboss(self._make_jboss_with_apps_config())
        self.jboss1._get_running_des = lambda: self.jboss1.config.apps
        self.jboss1._run_app_hooks_batch = lambda stage, running_des: None
        self.jboss1._stop_all_apps_batch_worker = lambda running_des: True
        self.assertEqual(self.jboss1._stop_all_apps_batch(), True)

    def test__stop_all_apps_batch__no_apps(self):
        self.jboss._get_running_des = lambda: []
        self.jboss._run_app_hooks_batch = lambda stage, running_des: self.fail(
                "should not be called")
        self.jboss._stop_all_apps_batch_worker = lambda running_des: self.fail(
                "should not be called")
        self.assertEqual(self.jboss._stop_all_apps_batch(), True)

    def test__stop_all_apps_batch_worker_pos_01(self):
        # Check _stop_all_apps_batch returns true when everything works
        # in its favour
        self.jboss1 = litp_jboss.LitpJboss(self._make_jboss_with_apps_config())
        old_run_cmds = self.jboss1.jbosscli.run_commands 
        self.jboss1.jbosscli.run_commands = self._counter_func([(0, "","")])
        self.jboss1._sleep = lambda *args: None
        try:
            running_des = self.jboss1.config.apps
            self.jboss1._sleep = lambda *args: None
            self.jboss1._create_batch_cli_commands = \
                    self._counter_func([["mock"],])
            self.jboss1._calculate_timeout = self._counter_func([330])
            self.jboss1._get_running_des = self._counter_func([])
            self.assertEqual(True, 
                    self.jboss1._stop_all_apps_batch_worker(running_des))
            # Make sure these functions were called once
            self.assertRaises(AssertionError, self.jboss1._calculate_timeout)
            self.assertRaises(AssertionError, self.jboss1._get_running_des)
            self.assertRaises(AssertionError, 
                    self.jboss1._create_batch_cli_commands)
            # Make sure this function was called 30 times
            self.assertRaises(AssertionError, self.jboss1.jbosscli.run_commands)
        finally:
            self.jboss1.jbosscli.run_commands = old_run_cmds
        
    def test__stop_all_apps_batch_worker_pos_02(self):
        # succeeds after 29 timeouts and 4 errors and a success
        self.jboss1 = litp_jboss.LitpJboss(self._make_jboss_with_apps_config())
        old_run_cmds = self.jboss1.jbosscli.run_commands 
        self.jboss1.jbosscli.run_commands = self._counter_func([(2, '', '')] 
                * 29 + [(1, '', '')] * 4 + [(0, '','')])
        try:
            running_des = self.jboss1.config.apps
            self.jboss1._sleep = lambda *args: None
            self.jboss1._create_batch_cli_commands = \
                    self._counter_func([["mock"],] * 5)
            self.jboss1._calculate_timeout = self._counter_func([330,] * 5)
            self.jboss1._get_running_des = self._counter_func(\
                    [running_des] * 4)
            self.assertEqual(True,
                    self.jboss1._stop_all_apps_batch_worker(running_des))
            # Make sure these functions were called once
            self.assertRaises(AssertionError, self.jboss1._calculate_timeout)
            self.assertRaises(AssertionError, self.jboss1._get_running_des)
            self.assertRaises(AssertionError, 
                    self.jboss1._create_batch_cli_commands)
            # Make sure this function was called 30 times
            self.assertRaises(AssertionError, self.jboss1.jbosscli.run_commands)
        finally:
            self.jboss1.jbosscli.run_commands = old_run_cmds
    
    def test__stop_all_apps_batch_worker_neg_01(self):
        # Fails after 30 timeouts
        self.jboss1 = litp_jboss.LitpJboss(self._make_jboss_with_apps_config())
        old_run_cmds = self.jboss1.jbosscli.run_commands 
        self.jboss1.jbosscli.run_commands = self._counter_func([(2, "","")] * 30)
        try:
            running_des = self.jboss1.config.apps
            self.jboss1._sleep = lambda *args: None
            self.jboss1._create_batch_cli_commands = \
                    self._counter_func([["mock"],])
            self.jboss1._calculate_timeout = self._counter_func([330])
            self.jboss1._get_running_des = self._counter_func([])
            self.assertEqual(False, 
                    self.jboss1._stop_all_apps_batch_worker(running_des))
            # Make sure these functions were called once
            self.assertRaises(AssertionError, self.jboss1._calculate_timeout)
            self.assertRaises(AssertionError, self.jboss1._get_running_des)
            self.assertRaises(AssertionError, 
                    self.jboss1._create_batch_cli_commands)
            # Make sure this function was called 30 times
            self.assertRaises(AssertionError, self.jboss1.jbosscli.run_commands)
        finally:
            self.jboss1.jbosscli.run_commands = old_run_cmds

    def test__stop_all_apps_batch_worker_neg_02(self):
        # Fails after 5 undeploy errors
        self.jboss1 = litp_jboss.LitpJboss(self._make_jboss_with_apps_config())
        old_run_cmds = self.jboss1.jbosscli.run_commands 
        self.jboss1.jbosscli.run_commands = self._counter_func([(1, "","")] * 5)
        try:
            running_des = self.jboss1.config.apps
            self.jboss1._sleep = lambda *args: None
            self.jboss1._create_batch_cli_commands = \
                    self._counter_func([["mock"],] * 5)
            self.jboss1._calculate_timeout = self._counter_func([330] * 5)
            self.jboss1._get_running_des = self._counter_func(\
                    [running_des] * 4)
            self.assertEqual(False, 
                    self.jboss1._stop_all_apps_batch_worker(running_des))
            # Make sure these functions were called once
            self.assertRaises(AssertionError, self.jboss1._calculate_timeout)
            self.assertRaises(AssertionError, self.jboss1._get_running_des)
            self.assertRaises(AssertionError, 
                    self.jboss1._create_batch_cli_commands)
            # Make sure this function was called 30 times
            self.assertRaises(AssertionError, self.jboss1.jbosscli.run_commands)
        finally:
            self.jboss1.jbosscli.run_commands = old_run_cmds
    
    def test__stop_all_apps_batch_worker__no_apps(self):
        old_run_cmds = self.jboss.jbosscli.run_commands 
        self.jboss.jbosscli.run_commands = lambda *args: self.fail(
                "should not be called")
        try:
            self.assertEqual(True, self.jboss._stop_all_apps_batch_worker([]))
        finally:
            self.jboss.jbosscli.run_commands = old_run_cmds

    def test__check_and_kill_zombie(self):
        self.jboss._get_ppid = lambda pid: 5
        self.jboss._kill_pid = lambda pid, sig: self.assertEqual(pid, 5)
        self.jboss._pid_is_zombie = lambda pid: True
        self.jboss._verify_pid = self._mock__verify_pid
        self.jboss._check_and_kill_zombie()

    def test__set_config_pos_01(self):
        # Tests that calling set_config sets up appropriate instance variables
        config = litp_jboss_config.LitpJbossConfig(
                config_dict={'LITP_JEE_CONTAINER_home_dir': '/home/jboss'})
        self.jboss.set_config(config)
        self.assertTrue(self.jboss.config is config)
        self.assertEqual(self.jboss._jboss_script, 
                "/home/jboss/bin/standalone.sh")
        self.assertEqual(self.jboss._adduser, "/home/jboss/bin/add-user.sh")
        self.assertEqual(self.jboss._mgmt_user_files,
                ['/home/jboss/domain/configuration/mgmt-users.properties',
                 '/home/jboss/standalone/configuration/mgmt-users.properties'])
        self.assertEqual(self.jboss._jboss_console_log, 
                "/home/jboss/jboss-console.log")

    def test__set_config_pos_02(self):
        # Tests that calling set_config sets up appropriate instance variables
        # Especially that _jboss_console_log is set if log_dir is present
        config = litp_jboss_config.LitpJbossConfig(
                config_dict={'LITP_JEE_CONTAINER_home_dir': '/home/jboss',
                             'LITP_JEE_CONTAINER_log_dir': '/var/log'})
        self.jboss.set_config(config)
        self.assertTrue(self.jboss.config is config)
        self.assertEqual(self.jboss._jboss_script, 
                "/home/jboss/bin/standalone.sh")
        self.assertEqual(self.jboss._adduser, "/home/jboss/bin/add-user.sh")
        self.assertEqual(self.jboss._mgmt_user_files,
                ['/home/jboss/domain/configuration/mgmt-users.properties',
                 '/home/jboss/standalone/configuration/mgmt-users.properties'])
        self.assertEqual(self.jboss._jboss_console_log, 
                "/var/log/jboss-console.log")

if __name__ == '__main__':
    unittest.main()
