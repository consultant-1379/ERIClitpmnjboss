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
import os
os.environ["TESTING_FLAG"] = "1"

from litpmnjboss import litp_jboss_app, litp_jboss_cli, litp_jboss_config, \
    litp_jboss_common, litp_jboss_app_config

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
    '-Djgroups.uuid_cache.max_age=5000 -Dsun.rmi.dgc.server.gcInterval=300 '
    '-Djava.net.preferIPv4Stack=true -Dcom.ericsson.oss.sdk.node.identifier'
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
    'LITP_DE_COUNT': '1',
    'LITP_DE_0_JEE_DE_install_source':
        '/opt/ericsson/nms/litp/dummyapps/dummy-war-1.0.1.war',
    'LITP_DE_0_JEE_DE_name': 'dummy-war',
    'LITP_DE_0_JEE_DE_version': '1.0.1',
    'LITP_DE_0_JEE_DE_app_type': 'war',
    'LITP_DE_0_JEE_DE_pre_deploy':
        '/opt/ericsson/nms/litp/etc/jboss/jboss_app/pre_deploy.d/',
    'LITP_DE_0_JEE_DE_post_deploy':
        '/opt/ericsson/nms/litp/etc/jboss/jboss_app/post_deploy.d/',
    'LITP_DE_0_JEE_DE_pre_undeploy':
        '/opt/ericsson/nms/litp/etc/jboss/jboss_app/pre_undeploy.d',
    'LITP_DE_0_JEE_DE_post_undeploy':
        '/opt/ericsson/nms/litp/etc/jboss/jboss_app/post_undeploy.d',
    'LITP_DE_0_JEE_DE_pre_start':
        '/opt/ericsson/nms/litp/etc/jboss/jboss_app/pre_start.d/',
    'LITP_DE_0_JEE_DE_post_start':
        '/opt/ericsson/nms/litp/etc/jboss/jboss_app/post_start.d/',
    'LITP_DE_0_JEE_DE_pre_shutdown':
        '/opt/ericsson/nms/litp/etc/jboss/jboss_app/pre_shutdown.d/',
    'LITP_DE_0_JEE_DE_post_shutdown':
        '/opt/ericsson/nms/litp/etc/jboss/jboss_app/post_shutdown.d/',
    'LITP_DE_0_JEE_DE_pre_upgrade':
        '/opt/ericsson/nms/litp/etc/jboss/jboss_app/pre_upgrade.d/',
    'LITP_DE_0_JEE_DE_post_upgrade':
        '/opt/ericsson/nms/litp/etc/jboss/jboss_app/post_upgrade.d',
}

# upgrade test env
new_env = test_env.copy()
new_env['LITP_DE_0_JEE_DE_version'] = '1.1.1'


class MockLitpJbossCliNegative(litp_jboss_cli.LitpJbossCli):

    def run(self, cmd):
        if cmd == "ls deployment":
            return (0, [], [])
        elif cmd == "ls deployment=dummy-war-1.0.1.war":
            return (0, ["status=STOPPED"], [])
        elif cmd == "deploy " + \
                    "/opt/ericsson/nms/litp/dummyapps/dummy-war-1.0.1.war " + \
                    "--name=dummy-war --disabled":
            return (127, [], [])
        else:
            return (1, [], [])

class MockLitpJbossCliTimesOut(litp_jboss_cli.LitpJbossCli):

    def run(self, cmd):
        stderr = """org.jboss.as.cli.CliInitializationException: Failed to connect to the controller
    at org.jboss.as.cli.impl.CliLauncher.initCommandContext(CliLauncher.java:264)
    at org.jboss.as.cli.impl.CliLauncher.main(CliLauncher.java:230)
    at org.jboss.as.cli.CommandLineMain.main(CommandLineMain.java:34)
    at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
    at sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:57)
    at sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
    at java.lang.reflect.Method.invoke(Method.java:601)
    at org.jboss.modules.Module.run(Module.java:270)
    at org.jboss.modules.Main.main(Main.java:294)
Caused by: org.jboss.as.cli.CommandLineException: The controller is not available at 10.46.23.51:9999
    at org.jboss.as.cli.impl.CommandContextImpl.tryConnection(CommandContextImpl.java:888)
    at org.jboss.as.cli.impl.CommandContextImpl.connectController(CommandContextImpl.java:727)
    at org.jboss.as.cli.impl.CommandContextImpl.connectController(CommandContextImpl.java:704)
    at org.jboss.as.cli.impl.CliLauncher.initCommandContext(CliLauncher.java:262)
    ... 8 more
Caused by: java.io.IOException: java.net.ConnectException: JBAS012144: Could not connect to remote://10.46.23.51:9999. The connection timed out
    at org.jboss.as.controller.client.impl.AbstractModelControllerClient.executeForResult(AbstractModelControllerClient.java:129)
    at org.jboss.as.controller.client.impl.AbstractModelControllerClient.execute(AbstractModelControllerClient.java:71)
    at org.jboss.as.cli.impl.CommandContextImpl.tryConnection(CommandContextImpl.java:866)
    ... 11 more
Caused by: java.net.ConnectException: JBAS012144: Could not connect to remote://10.46.23.51:9999. The connection timed out
    at org.jboss.as.protocol.ProtocolConnectionUtils.connectSync(ProtocolConnectionUtils.java:120)
    at org.jboss.as.protocol.ProtocolConnectionManager$EstablishingConnection.connect(ProtocolConnectionManager.java:247)
    at org.jboss.as.protocol.ProtocolConnectionManager.connect(ProtocolConnectionManager.java:70)
    at org.jboss.as.protocol.mgmt.FutureManagementChannel$Establishing.getChannel(FutureManagementChannel.java:176)
    at org.jboss.as.controller.client.impl.RemotingModelControllerClient.getOrCreateChannel(RemotingModelControllerClient.java:146)
    at org.jboss.as.controller.client.impl.RemotingModelControllerClient$1.getChannel(RemotingModelControllerClient.java:67)
    at org.jboss.as.protocol.mgmt.ManagementChannelHandler.executeRequest(ManagementChannelHandler.java:115)
    at org.jboss.as.protocol.mgmt.ManagementChannelHandler.executeRequest(ManagementChannelHandler.java:98)
    at org.jboss.as.controller.client.impl.AbstractModelControllerClient.executeRequest(AbstractModelControllerClient.java:236)
    at org.jboss.as.controller.client.impl.AbstractModelControllerClient.execute(AbstractModelControllerClient.java:141)
    at org.jboss.as.controller.client.impl.AbstractModelControllerClient.executeForResult(AbstractModelControllerClient.java:127)
    ... 13 more
        """
        return (1, [], stderr.split('\n'))

class MockLitpJbossCliPositive(litp_jboss_cli.LitpJbossCli):

    def run(self, cmd):
        if cmd == "ls deployment":
            return (0, ['dummy-war\n'], [])
        elif cmd == "ls deployment=dummy-war":
            return (0, ["status=OK"], [])
        else:
            return (0, [], [])


class TestLitpJbossApp(unittest.TestCase):

    def _make_raiser(self, exceptiontype):
        # A helper function to create functions that raise exceptions
        # because lambda can't raise exceptions
        def inner(*args, **kwargs):
            raise exceptiontype
        return inner

    def _make_app(self, env_dict):
        try:
            old_isfile = litp_jboss_app.LitpJbossApp._isfile
            litp_jboss_app.LitpJbossApp._isfile = lambda c, filepath: True

            config = litp_jboss_config.LitpJbossConfig(env_dict)
            return litp_jboss_app.LitpJbossApp(config.apps[0])
        except NameError as ne:
            print "Name Error: %s" % (ne)
        finally:
            litp_jboss_app.LitpJbossApp._isfile = old_isfile

    def _make_mock_cli(self, env_dict, p=True, timeout=False):
        try:
            container_config = litp_jboss_config.LitpJbossConfig(env_dict)
            config = litp_jboss_config.LitpJbossAppConfig(env_dict, \
                                                             container_config)
            if p:  # positive mock
                return MockLitpJbossCliPositive(config.get_jboss_config())
            else:
                if timeout:
                    return MockLitpJbossCliTimesOut(config.get_jboss_config())
                else:
                    return MockLitpJbossCliNegative(config.get_jboss_config())

        except NameError as ne:
            print "Name Error: %s" % (ne)

    def setUp(self):
        unittest.TestCase.setUp(self)
        self.jboss_app_1 = self._make_app(test_env)
        self._mock_jbosscli_positive = self._make_mock_cli(test_env)
        self.jboss_app_2 = self._make_app(test_env)
        self._mock_jbosscli_negative = self._make_mock_cli(test_env, p=False)
        self._mock_jbosscli_timeout = self._make_mock_cli(test_env, p=False, 
                timeout=True)

        self.save_exists = litp_jboss_app.os.path.exists
        self.save_isdir = litp_jboss_app.os.path.isdir
        self.save_isfile = litp_jboss_app.os.path.isfile

    def tearDown(self):
        unittest.TestCase.tearDown(self)
        litp_jboss_app.os.path.exists = self.save_exists
        litp_jboss_app.os.path.isdir = self.save_isdir
        litp_jboss_app.os.path.isfile = self.save_isfile

    def test_is_connection_issue_pos_01(self):
        err = self._mock_jbosscli_timeout.run("")[2]
        self.assertEqual(self.jboss_app_1._is_connection_issue(err), True)

    def test_is_connection_issue_pos_02(self):
        err = "JBOSS CLI command timed out: mock result" 
        self.assertEqual(self.jboss_app_1._is_connection_issue(err), True)

    def test_is_connection_issue_pos_03(self):
        err = "No handler for command ls-deployment"
        self.assertEqual(self.jboss_app_1._is_connection_issue(err), False)

    def test_is_connection_issue_pos_04(self):
        err = ["No handler for command ls-deployment"]
        self.assertEqual(self.jboss_app_1._is_connection_issue(err), False)

    def test_litp_jboss_app_properties(self):
        self.assertEqual(self.jboss_app_1.config.get('install_source'),
                "/opt/ericsson/nms/litp/dummyapps/dummy-war-1.0.1.war")
        self.assertEqual(self.jboss_app_1.config.get('name'), 'dummy-war')
        self.assertEqual(self.jboss_app_1.config.get('app_type'), 'war')
        self.assertEqual(self.jboss_app_1.config.get('version'), '1.0.1')

    def test_litp_jboss_app_install_source_construction(self):
        '''LITP-3040 install_source construction'''
        tmp1 = litp_jboss_app.os.path.isdir
        litp_jboss_app.os.path.isdir = lambda arg: True

        def _mock_is_file(arg2):
            if arg2 is self.jboss_app_1.config.config['install_source']:
                return False
            return True

        self.jboss_app_1._isfile = _mock_is_file

        # common data
        self.jboss_app_1.config.config['name'] = 'appName.war'
        self.jboss_app_1.config.config['app_type'] = 'war'
        self.jboss_app_1.config.config['version'] = '1.0.0'
        # expected candidate name
        candidate = '/opt/ericsson/appName-1.0.0.war'

        # install_source not having final slash
        self.jboss_app_1.config.config['install_source'] = '/opt/ericsson'
        self.assertEqual(self.jboss_app_1.get_install_file(), candidate)
        # install_source has final slash
        self.jboss_app_1.config.config['install_source'] = '/opt/ericsson/'
        self.assertEqual(self.jboss_app_1.get_install_file(), candidate)

        # another one
        candidate = '/opt/ericsson/apps/1.0.0/appName-1.0.0.war'
        self.jboss_app_1.config.config['install_source'] = \
                                                '/opt/ericsson/apps/1.0.0/'
        self.assertEqual(self.jboss_app_1.get_install_file(), candidate)

        litp_jboss_app.os.path.isdir = tmp1

    def test_litp_jboss_app_get_install_file(self):
        # install source could not be found
        self.assertEqual(None, self.jboss_app_1.get_install_file())

        # install source is None
        self.jboss_app_1.config.config['install_source'] = None
        self.assertEqual(None, self.jboss_app_1.get_install_file())

        # name is None
        self.jboss_app_1.config.config['install_source'] = \
                '/opt/ericsson/nms/litp/dummyapps/dummy-war-1.0.1.war'
        self.jboss_app_1.config.config['name'] = None
        self.assertEqual(None, self.jboss_app_1.get_install_file())

        # version is None
        self.jboss_app_1.config.config['name'] = 'dummy-war'
        self.jboss_app_1.config.config['version'] = None
        self.assertEqual(None, self.jboss_app_1.get_install_file())

        # app_type is None
        self.jboss_app_1.config.config['version'] = '1.0.1'
        self.jboss_app_1.config.config['app_type'] = None
        self.assertEqual(None, self.jboss_app_1.get_install_file())

        # install source exists and is a directory
        # and the constructed file does not exits
        self.jboss_app_1.config.config['app_type'] = 'war'
        old_isdir = litp_jboss_app.os.path.isdir
        old_isfile = litp_jboss_app.LitpJbossApp._isfile
        self.jboss_app_1._isfile = lambda arg: False
        try:
            litp_jboss_app.os.path.isdir = lambda arg: True
            litp_jboss_app.LitpJbossApp._isfile = lambda arg: False
            self.assertEqual(None, self.jboss_app_1.get_install_file())
        except Exception as e:
            print "Exception: %s" % (e)
        finally:
            litp_jboss_app.os.path.isdir = old_isdir
            litp_jboss_app.LitpJbossApp._isfile = old_isfile

        # install source exists and is a directory
        # and the constructed file exists
        old_isdir = litp_jboss_app.os.path.isdir
        old_isfile = litp_jboss_app.LitpJbossApp._isfile
        self.jboss_app_1._isfile = lambda arg: False
        litp_jboss_app.os.path.isdir = lambda arg: True
        litp_jboss_app.LitpJbossApp._isfile = lambda arg: False
        self.assertEqual(None, self.jboss_app_1.get_install_file())
        litp_jboss_app.os.path.isdir = old_isdir
        litp_jboss_app.LitpJbossApp._isfile = old_isfile

        # install source exists and is a file
        self.jboss_app_1._isfile = lambda arg: True
        self.assertEqual(self.jboss_app_1.get_install_file(),
                    '/opt/ericsson/nms/litp/dummyapps/dummy-war-1.0.1.war')

    def test_litp_jboss_app_is_deployed(self):
        # test not deployed 1
        self.assertEqual(self.jboss_app_1._is_deployed(), False)
        # test not deployed 2
        self.assertEqual(self.jboss_app_2._is_deployed(), False)
        # test not deployed as from jboss cli
        self.jboss_app_1.jbosscli = self._mock_jbosscli_negative
        self.assertEqual(self.jboss_app_1._is_deployed(), False)
        # test deployed as from jboss cli
        self.jboss_app_1.jbosscli = self._mock_jbosscli_positive
        self.assertEqual(self.jboss_app_1._is_deployed(), True)
        # test what happens when cli times out
        self.jboss_app_1.jbosscli = self._mock_jbosscli_timeout
        self.assertRaises(litp_jboss_app.CliConnectionException,
                self.jboss_app_1._is_deployed)

    def test_litp_jboss_app_is_started(self):
        # test not stated 1
        self.assertEqual(self.jboss_app_1._is_started(), False)
        # test not stated 2
        self.assertEqual(self.jboss_app_2._is_started(), False)
        # test not started as from jboss cli rc
        self.jboss_app_1.jbosscli = self._mock_jbosscli_negative
        self.assertEqual(self.jboss_app_1._is_started(), False)
        # test not started as from jboss cli stdout
        self.jboss_app_1.jbosscli = self._mock_jbosscli_positive
        setattr(self.jboss_app_1.jbosscli, 'run', lambda x: \
                                                (0, ["status=ERROR"], []))
        self.assertEqual(self.jboss_app_1._is_started(), False)
        # test started as from jboss cli
        setattr(self.jboss_app_1.jbosscli, 'run', lambda x: \
                                                (0, ["status=OK"], []))
        self.assertEqual(self.jboss_app_1._is_started(), True)
        # test what happens when cli times out
        self.jboss_app_1.jbosscli = self._mock_jbosscli_timeout
        self.assertRaises(litp_jboss_app.CliConnectionException,
                self.jboss_app_1._is_started)

    @mock.patch("subprocess.Popen")
    def test_litp_jboss_app_run_fragments(self, mock_popen):
        # fragment doesn't exist
        self.assertEqual(0, self.jboss_app_1._run_fragments('foo_fragment'))

        def _mock_os_method_true(self):
            return True

        litp_jboss_app.os.path.exists = _mock_os_method_true
        litp_jboss_app.os.path.isdir = _mock_os_method_true
        litp_jboss_app.os.path.isfile = _mock_os_method_true

        def _mock_os_listdir(dir):
            return ['test02', 'test02']

        def _mock_os_access(self, x):
            return True

        def _mock_os_system_0(cmd, env):
            return 0, [], []

        litp_jboss_app.os.access = _mock_os_access
        litp_jboss_app.os.listdir = _mock_os_listdir
        litp_jboss_app.os.access = _mock_os_access

        # fragment does exist
        # test successful call to scripts
        mock_popen.return_value.returncode = 0
        self.assertEqual(0, self.jboss_app_1._run_fragments('post_upgrade'))

        # fragment does exist
        # test on failed call to script
        mock_popen.return_value.returncode = 1
        self.assertEqual(1, self.jboss_app_1._run_fragments('post_upgrade'))

    def test_litp_jboss_app_start(self):
        # test cli times out in _is_deployed
        setattr(self.jboss_app_1, '_is_deployed', self._make_raiser(
            litp_jboss_app.CliConnectionException))
        self.assertEqual(self.jboss_app_1.start(), 2)
        # test failed deploy
        setattr(self.jboss_app_1, '_run_fragments', lambda f: 0)
        setattr(self.jboss_app_1, '_is_deployed', lambda: False)
        self.assertEqual(self.jboss_app_1.start(), 1)
        # test successful deploy, fail on  do start
        setattr(self.jboss_app_1, 'deploy', lambda: 0)
        self.assertEqual(self.jboss_app_1.start(), 127)
        # test fail on jboss cli start
        self.jboss_app_1.jbosscli = self._mock_jbosscli_negative
        self.assertEqual(self.jboss_app_1.start(), 1)
        # test fail on jboss cli timeout
        self.jboss_app_1.jbosscli = self._mock_jbosscli_timeout
        self.assertEqual(self.jboss_app_1.start(), 2)
        # test successful  jboss cli start
        self.jboss_app_1.jbosscli = self._mock_jbosscli_positive
        self.assertEqual(self.jboss_app_1.start(), 0)
        # test fail on upgrade
        setattr(self.jboss_app_1, '_is_deployed', lambda: True)
        setattr(self.jboss_app_1, '_is_started', lambda: False)
        setattr(self.jboss_app_1, 'upgrade', lambda start: 1)
        new_config = litp_jboss_app_config.LitpJbossAppConfig(new_env)
        self.assertEqual(self.jboss_app_1.start(new_config), 1)
        # test success when no change in config
        same_config = self.jboss_app_1.config
        setattr(self.jboss_app_1, '_is_started', lambda: True)
        self.assertEqual(self.jboss_app_1.start(same_config), 0)
        # test fail on post start fragment
        setattr(self.jboss_app_1, '_run_fragments', lambda f: 1 \
                                        if f == 'post_start' else 0)
        self.assertEqual(self.jboss_app_1._do_start(), 1)
        # test when cli times out in _is_started
        setattr(self.jboss_app_1, '_is_started', self._make_raiser(
            litp_jboss_app.CliConnectionException))
        self.assertEqual(self.jboss_app_1.start(same_config), 2)
        # test when on failed start
        setattr(self.jboss_app_1, '_is_started', lambda: False)
        self.jboss_app_1.jbosscli = self._mock_jbosscli_negative
        self.assertEqual(self.jboss_app_1.start(same_config), 1)
        # test failed pre start run fragment
        setattr(self.jboss_app_1, '_is_started', lambda: True)
        setattr(self.jboss_app_1, '_run_fragments', lambda f: 1)
        self.assertEqual(self.jboss_app_1._do_start(), 1)

    def test_litp_jboss_app_stop(self):
        # test fail on not deployed
        setattr(self.jboss_app_1, '_is_deployed', lambda: False)
        self.assertEqual(self.jboss_app_1.stop(), 1)
        # test correct return code on cli timeout on _is_deployed
        setattr(self.jboss_app_1, '_is_deployed', self._make_raiser(
            litp_jboss_app.CliConnectionException))
        self.assertEqual(self.jboss_app_1.stop(), 2)
        # test sucess already stop (and is deployed)
        setattr(self.jboss_app_1, '_is_deployed', lambda: True)
        setattr(self.jboss_app_1, '_is_started', lambda: False)
        self.assertEqual(self.jboss_app_1.stop(), 0)
        # test failure when _is_started times out
        setattr(self.jboss_app_1, '_is_started', self._make_raiser(
            litp_jboss_app.CliConnectionException))
        self.assertEqual(self.jboss_app_1.stop(), 2)
        # test fail on stop using jboss cli
        setattr(self.jboss_app_1, '_is_started', lambda: True)
        setattr(self.jboss_app_1, '_run_fragments', lambda x: 0)
        self.jboss_app_1.jbosscli = self._mock_jbosscli_negative
        self.assertEqual(self.jboss_app_1.stop(), 1)
        # test fail on stop when jboss cli times out
        self.jboss_app_1.jbosscli = self._mock_jbosscli_timeout
        self.assertEqual(self.jboss_app_1.stop(), 2)
        # test successfully stop
        self.jboss_app_1.jbosscli = self._mock_jbosscli_positive
        self.assertEqual(self.jboss_app_1.stop(), 0)
        # test failed pre shutdown run fragment
        setattr(self.jboss_app_1, '_run_fragments', lambda f: 1)
        self.assertEqual(self.jboss_app_1.stop(), 1)
        # test fail on post shutdown fragment
        setattr(self.jboss_app_1, '_run_fragments', lambda f: 1 \
                                        if f == 'post_shutdown' else 0)
        self.assertEqual(self.jboss_app_1.stop(), 1)

    def test_litp_jboss_app_status(self):
        # test fail on not deployed
        setattr(self.jboss_app_1, '_is_deployed', lambda: False)
        self.assertEqual(self.jboss_app_1.status(), 1)
        # test fail on cli timeout
        setattr(self.jboss_app_1, '_is_deployed', self._make_raiser(
            litp_jboss_app.CliConnectionException))
        self.assertEqual(self.jboss_app_1.status(), 2)
        # test fail on is not started
        setattr(self.jboss_app_1, '_is_deployed', lambda: True)
        self.assertEqual(self.jboss_app_1.status(), 1)
        # test successful status
        setattr(self.jboss_app_1, '_is_started', lambda: True)
        self.assertEqual(self.jboss_app_1.status(), 0)
        # test fail on cli timeout
        setattr(self.jboss_app_1, '_is_started', self._make_raiser(
            litp_jboss_app.CliConnectionException))
        self.assertEqual(self.jboss_app_1.status(), 2)

    def test_litp_jboss_app_restart(self):
        # test failed on stop
        setattr(self.jboss_app_1, 'stop', lambda: 1)
        self.assertEqual(self.jboss_app_1.restart(), 1)
        # test failed on start
        setattr(self.jboss_app_1, 'stop', lambda: 0)
        setattr(self.jboss_app_1, 'start', lambda: 1)
        self.assertEqual(self.jboss_app_1.restart(), 1)
        # test successful restart
        setattr(self.jboss_app_1, 'start', lambda: 0)
        self.assertEqual(self.jboss_app_1.restart(), 0)

    def test_litp_jboss_app_deploy(self):
        # test already deployed
        setattr(self.jboss_app_1, '_is_deployed', lambda: True)
        self.assertEqual(self.jboss_app_1.deploy(), 0)
        # test cli times out
        setattr(self.jboss_app_1, '_is_deployed', self._make_raiser(
            litp_jboss_app.CliConnectionException))
        self.assertEqual(self.jboss_app_1.deploy(), 2)
        # test failure when install file is None
        setattr(self.jboss_app_1, '_is_deployed', lambda: False)
        setattr(self.jboss_app_1, 'get_install_file', lambda: None)
        self.assertEqual(self.jboss_app_1.deploy(), 1)
        # test pre deploy run fragment fail
        setattr(self.jboss_app_1, 'get_install_file', lambda: 'test')
        setattr(self.jboss_app_1, '_run_fragments', lambda x: 1)
        self.assertEqual(self.jboss_app_1.deploy(), 1)
        # test jboss cli negative
        setattr(self.jboss_app_1, '_run_fragments', lambda x: 0)
        self.jboss_app_1.jbosscli = self._mock_jbosscli_negative
        self.assertEqual(self.jboss_app_1.deploy(), 1)
        # test jboss cli times out
        self.jboss_app_1.jbosscli = self._mock_jbosscli_timeout
        self.assertEqual(self.jboss_app_1.deploy(), 2)
        # test jboss cli positive
        self.jboss_app_1.jbosscli = self._mock_jbosscli_positive
        self.assertEqual(self.jboss_app_1.deploy(), 0)
        # test fail on post deploy fragment
        setattr(self.jboss_app_1, '_run_fragments', lambda f: 1 \
                                        if f == 'post_deploy' else 0)
        self.assertEqual(self.jboss_app_1.deploy(), 1)

    def test_litp_jboss_app_undeploy(self):
        # test not deployed
        self.assertEqual(self.jboss_app_1.undeploy(), 0)
        # test cli times out 01
        setattr(self.jboss_app_1, '_is_deployed', self._make_raiser(
            litp_jboss_app.CliConnectionException))
        self.assertEqual(self.jboss_app_1.undeploy(), 2)
        # test cli times out 02
        setattr(self.jboss_app_1, '_is_deployed', lambda: True)
        setattr(self.jboss_app_1, '_is_started', self._make_raiser(
            litp_jboss_app.CliConnectionException))
        self.assertEqual(self.jboss_app_1.undeploy(), 2)
        # test failed undeploy
        setattr(self.jboss_app_1, '_is_deployed', lambda: True)
        setattr(self.jboss_app_1, '_is_started', lambda: False)
        setattr(self.jboss_app_1, '_run_fragments', lambda x: 0)
        setattr(self.jboss_app_1, 'stop', lambda x: 0)
        self.assertEqual(self.jboss_app_1.undeploy(), 127)
        # test failed stop of app
        setattr(self.jboss_app_1, '_is_started', lambda: True)
        setattr(self.jboss_app_1, 'stop', lambda: 1)
        self.assertEqual(self.jboss_app_1.undeploy(), 1)
        # test failed successful undeploy
        setattr(self.jboss_app_1, '_is_started', lambda: False)
        setattr(self.jboss_app_1, 'stop', lambda x: 0)
        self.jboss_app_1.jbosscli = self._mock_jbosscli_positive
        self.assertEqual(self.jboss_app_1.undeploy(), 0)
        # test cli times out
        self.jboss_app_1.jbosscli = self._mock_jbosscli_timeout
        self.assertEqual(self.jboss_app_1.undeploy(), 2)
        # test failed pre undeploy run fragment
        self.jboss_app_1.jbosscli = self._mock_jbosscli_positive
        setattr(self.jboss_app_1, '_run_fragments', lambda f: 1)
        self.assertEqual(self.jboss_app_1.undeploy(), 1)
        # test failed post undeploy run fragment
        setattr(self.jboss_app_1, '_run_fragments', lambda f: 1 \
                                        if f == 'post_undeploy' else 0)
        self.assertEqual(self.jboss_app_1.undeploy(), 1)

    def test_litp_jboss_app_upgrade(self):
        # setup ald and new config for upgrade
        old_v = litp_jboss_app_config.LitpJbossAppConfig(test_env)
        new_v = litp_jboss_app_config.LitpJbossAppConfig(new_env)
        # test failed pre upgrade run fragment
        setattr(self.jboss_app_1, '_run_fragments', lambda f: 1)
        self.assertEqual(self.jboss_app_1._upgrade(old_v, new_v), 1)
        # test failed upgrade on undeploy
        setattr(self.jboss_app_1, '_is_deployed', lambda: True)
        setattr(self.jboss_app_1, '_run_fragments', lambda x: 0)
        self.assertEqual(self.jboss_app_1._upgrade(old_v, new_v), 127)
        # test failed upgrade on start
        setattr(self.jboss_app_1, 'undeploy', lambda: 0)
        setattr(self.jboss_app_1, 'deploy', lambda: 0)
        self.assertEqual(self.jboss_app_1._upgrade(old_v, new_v), 1)
        # test successful upgrade
        setattr(self.jboss_app_1, 'start', lambda: 0)
        self.assertEqual(self.jboss_app_1._upgrade(old_v, new_v), 0)
        # test failed post upgrade run fragment
        setattr(self.jboss_app_1, '_run_fragments', lambda f: 1 \
                                        if f == 'post_upgrade' else 0)
        self.assertEqual(self.jboss_app_1._upgrade(old_v, new_v), 1)

if __name__ == '__main__':
    unittest.main()
