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
import copy
import os
os.environ["TESTING_FLAG"] = "1"
import tempfile
import subprocess
import mock

from litpmnjboss import litp_jboss_cli, litp_jboss_config

test_env = {
    'LITP_JEE_CONTAINER_name': 'jee1',
    'LITP_JEE_CONTAINER_instance_name': 'jee1',
    'LITP_JEE_CONTAINER_install_source':
                        '/opt/ericsson/nms/jboss/jboss-eap-6.0.tgz',
    'LITP_JEE_CONTAINER_log_dir': '/var/log/jboss/jee1/',
    'LITP_JEE_CONTAINER_data_dir': '/var/lib/jboss/jee1/',
    'LITP_JEE_CONTAINER_home_dir': '/home/jboss',
    'LITP_JEE_CONTAINER_version': '1.0.0',
    'LITP_JEE_CONTAINER_process_user': 'litp_jboss',
    'LITP_JEE_CONTAINER_process_group': 'litp_jboss',
    'LITP_JEE_CONTAINER_public_listener': '0.0.0.0',
    'LITP_JEE_CONTAINER_public_port_base': '8080',
    'LITP_JEE_CONTAINER_management_listener': '0.0.0.0',
    'LITP_JEE_CONTAINER_management_port_base': '9990',
    'LITP_JEE_CONTAINER_management_port_native': '9999',
    'LITP_JEE_CONTAINER_management_user': 'admin',
    'LITP_JEE_CONTAINER_management_password': 'passw0rd',
    'LITP_JEE_CONTAINER_port_offset': '100',
    'LITP_JEE_CONTAINER_Xms': '1024M',
    'LITP_JEE_CONTAINER_Xmx': '1024M',
    'LITP_JEE_CONTAINER_MaxPermSize': '256M',
    'LITP_JEE_CONTAINER_command_line_options':
    '-Djgroups.uuid_cache.max_age=5000 -Dsun.rmi.dgc.server.gcInterval=300'
    ' -Djava.net.preferIPv4Stack=true -Dcom.ericsson.oss.sdk.node.identifier'
    '=jee1 -Djboss.node.name=jee1',
    'LITP_JEE_CONTAINER_messaging_group_address': '231.7.7.7',
    'LITP_JEE_CONTAINER_messaging_group_port': '12342',
    'LITP_JEE_CONTAINER_default_multicast': '231.7.7.7',
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
    'LITP_JEE_DE_install_source':
            '/opt/ericsson/nms/litp/dummyapps/dummy-war-1.0.1.war',
    'LITP_JEE_DE_name': 'dummy-war',
    'LITP_JEE_DE_version': '1.0.1',
    'LITP_JEE_DE_app_type': 'war',
    'LITP_JEE_DE_pre_deploy':
            '/opt/ericsson/nms/litp/etc/jboss/jboss_app/pre_deploy.d/',
    'LITP_JEE_DE_post_deploy':
            '/opt/ericsson/nms/litp/etc/jboss/jboss_app/post_deploy.d/',
    'LITP_JEE_DE_pre_undeploy':
            '/opt/ericsson/nms/litp/etc/jboss/jboss_app/pre_undeploy.d',
    'LITP_JEE_DE_post_undeploy':
            '/opt/ericsson/nms/litp/etc/jboss/jboss_app/post_undeploy.d',
    'LITP_JEE_DE_pre_start':
            '/opt/ericsson/nms/litp/etc/jboss/jboss_app/pre_start.d/',
    'LITP_JEE_DE_post_start':
            '/opt/ericsson/nms/litp/etc/jboss/jboss_app/post_start.d/',
    'LITP_JEE_DE_pre_shutdown':
            '/opt/ericsson/nms/litp/etc/jboss/jboss_app/pre_shutdown.d/',
    'LITP_JEE_DE_post_shutdown':
            '/opt/ericsson/nms/litp/etc/jboss/jboss_app/post_shutdown.d/',
    'LITP_JEE_DE_pre_upgrade':
            '/opt/ericsson/nms/litp/etc/jboss/jboss_app/pre_upgrade.d/',
    'LITP_JEE_DE_post_upgrade':
            '/opt/ericsson/nms/litp/etc/jboss/jboss_app/post_upgrade.d',
}


class TestLitpJbossCli(unittest.TestCase):

    def _make_cli(self, env_dict):
        config = litp_jboss_config.LitpJbossConfig(env_dict)
        return litp_jboss_cli.LitpJbossCli(config)

    def setUp(self):
        self.jboss_cli_1 = self._make_cli(test_env)

        test_env2 = copy.deepcopy(test_env)
        test_env2['LITP_JEE_CONTAINER_management_listener'] = '222.222.222.222'
        test_env2['LITP_JEE_CONTAINER_port_offset'] = '200'
        self.jboss_cli_2 = self._make_cli(test_env2)

    def test_litp_jboss_cli_derived_properties(self):
        self.assertEqual(self.jboss_cli_1.jboss_cli,
            '/home/jboss/bin/jboss-cli.sh controller=127.0.0.1:10099')
        self.assertEqual(self.jboss_cli_2.jboss_cli,
            '/home/jboss/bin/jboss-cli.sh controller=222.222.222.222:10199')

    @mock.patch('subprocess.Popen')
    def test_litp_jboss_cli_run(self, mock_popen):
        mock_popen.return_value.stdout.readlines.return_value = ['dummy_app_1\n', 'dummy_app_2\n']
        mock_popen.return_value.stderr.readlines.return_value = []
        mock_popen.return_value.returncode = 0
        rc, stdout, stderr = self.jboss_cli_1.run("ls deployment")
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, ['dummy_app_1\n', 'dummy_app_2\n'])
        self.assertEqual(stderr, [])

    @mock.patch('subprocess.Popen')
    def test_litp_jboss_cli_run_commands(self, mock_popen):
        mock_popen.return_value.stdout.readlines.return_value = ['line1\n', 'line2\n']
        mock_popen.return_value.stderr.readlines.return_value = []
        mock_popen.return_value.returncode = 0
        rc, stdout, stderr = self.jboss_cli_1.run_commands("ls,ls")
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, ['line1\n', 'line2\n'])
        self.assertEqual(stderr, [])
