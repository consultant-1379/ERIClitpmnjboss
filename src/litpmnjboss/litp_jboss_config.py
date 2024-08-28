##############################################################################
# COPYRIGHT Ericsson AB 2013,2014
#
# The copyright to the computer program(s) herein is the property of
# Ericsson AB. The programs may be used and/or copied only with written
# permission from Ericsson AB. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
##############################################################################
"""
Provides management JBoss config class to
represent and store configuration for JBoss instances
"""
from litpmnjboss.litp_jboss_app_config import LitpJbossAppConfig
from litpmnjboss.litp_jboss_support_package_config import (
    LitpJbossSupportPackageConfig)
from litpmnjboss.litp_jboss_base import LitpJbossBase
import litpmnjboss.litp_jboss_common as common
import json
import copy
import os
import shutil
import sys
import IPy

LITP_JBOSS_DATA_DIR = "/var/lib/litp/litp_jboss/"
LITP_CONTAINER_PREFIX = "LITP_JEE_CONTAINER_"
LITP_DE_PREFIX = "LITP_DE_"

jboss_var_names = (
    'home_dir', 'log_dir', 'log_file', 'name',
    'data_dir', 'instance_name', 'process_user',
    'process_group', 'port_offset', 'install_source',
    'command_line_options', 'pre_deploy', 'post_deploy',
    'pre_undeploy', 'post_undeploy', 'pre_start',
    'post_start', 'pre_shutdown', 'post_shutdown',
    'pre_upgrade', 'post_upgrade', 'public_listener',
    'public_port_base', 'management_listener', 'internal_listener',
    'management_port_base', 'management_port_native',
    'management_user', 'management_password', 'port_offset',
    'command_line_options', 'default_multicast',
    'jgroups_multicast', 'jgroups_bind_addr',
    'jgroups_mping_mcast_addr', 'jgroups_mping_mcast_port',
    'jgroups_udp_mcast_addr', 'jgroups_udp_mcast_port',
    'messaging_group_address', 'messaging_group_port',
    'install_destination', 'Xms', 'Xmx', 'MaxPermSize',
    'version', 'java_options',
)


class LitpJbossConfig(LitpJbossBase):
    """
    LITP JBOSS Config
    """

    def __init__(self, config_dict):
        """
        @summary: init for jboss config
        """
        super(LitpJbossConfig, self).__init__(config_dict=config_dict)
        self.apps = []
        self.sp_dict = {}
        self.support_packages = []
        self.config_dir = ""
        if self.litp_dict is not None:
            self._init_config()
            self._init_config_apps()
            self._init_config_sp()
            self._init_sp_dict()

    def _init_config(self):
        """
        @summary: init config based on config_dict
        """
        for name in jboss_var_names:
            self.config[name] = self.litp_dict.get(
                'LITP_JEE_CONTAINER_%s' % name, None)

        self._set_config_dir()
        self._set_jboss_cli()

    def _init_config_apps(self):
        """
        @summary: create app configs from config_dict
        """
        app_count = int(self.litp_dict.get('LITP_DE_COUNT', 0))
        if app_count != 0:
            base_app_env = dict([el for el in self.litp_dict.items()
                                 if not el[0].startswith('LITP_DE_')])

            for idx in range(app_count):
                app_config = copy.deepcopy(base_app_env)
                prefix = 'LITP_DE_%d_' % idx
                prefix_len = len(prefix)
                elems = [el for el in self.litp_dict.items()
                         if el[0].startswith(prefix)]
                for elem in elems:
                    app_config['LITP_' + elem[0][prefix_len:]] = elem[1]
                self.apps.append(LitpJbossAppConfig(app_config,
                                                    container=self))

    def _init_config_sp(self):
        """
        @summary: create sp configs from config_dict
        """
        sp_count = int(self.litp_dict.get('LITP_SP_COUNT', 0))
        if sp_count != 0:
            base_sp_env = dict([el for el in self.litp_dict.items()
                                if not el[0].startswith('LITP_SP_')])

            for idx in range(sp_count):
                sp_config = copy.deepcopy(base_sp_env)
                prefix = 'LITP_SP_%d_' % idx
                prefix_len = len(prefix)
                elems = [el for el in self.litp_dict.items()
                         if el[0].startswith(prefix)]
                for elem in elems:
                    sp_config['LITP_' + elem[0][prefix_len:]] = elem[1]

                self.support_packages.append(
                    LitpJbossSupportPackageConfig(sp_config,
                                                  container=self))

    def _init_sp_dict(self):
        """
        @summary: init the sp dict with the supplied support packages
        """
        self.sp_dict = dict(self.litp_dict)
        for key in self.litp_dict.keys():
            if not key.startswith('LITP_SP'):
                del self.sp_dict[key]

    def is_sp_different(self, jboss_config):
        if jboss_config is None:
            return True
        return jboss_config.sp_dict != self.sp_dict

    def _get_jboss_binary(self):
        return os.path.join(str(self.get('home_dir')), 'bin/jboss-cli.sh')

    def _get_cli_port(self):
        return int(self.get('management_port_native') or 0) + \
            int(self.get('port_offset') or 0)

    def _get_mgmt_port(self):
        return int(self.get('management_port_base') or 0) + \
            int(self.get('port_offset') or 0)

    def _get_server_address(self):
        server_address = self.get('management_listener')

        if server_address is None or server_address == '0.0.0.0':
            server_address = '127.0.0.1'
        else:
            try:
                the_ip = IPy.IP(server_address)

                if the_ip._ipversion == 6:  # if ipv6, needs [ip]
                    server_address = '[' + server_address + ']'
            except ValueError:
                common.log("Ip found in 'management_listener' is not valid",
                           level="ERROR")
                # NOTE: should it really exit here???
                sys.exit(1)

        return server_address

    def _set_jboss_cli(self):
        """
        @summary: set jboss CLI in env_dict
        """
        self.env_dict['JBOSS_CLI'] = '%s controller=%s:%d' % (
            self._get_jboss_binary(),
            self._get_server_address(),
            self._get_cli_port())

    def get_jboss_management_url(self):
        url = 'http://%s:%d/management' % (
            self._get_server_address(),
            self._get_mgmt_port(),
        )
        return url

    def _set_config_dir(self, jboss_instance=None):
        """
        @summary: set save filename
        """
        if jboss_instance is not None:
            self.config_dir = LITP_JBOSS_DATA_DIR + str(jboss_instance)
        else:
            self.config_dir = LITP_JBOSS_DATA_DIR + \
                str(self.get('instance_name'))

    def _config_file(self):
        return self.config_dir + '/config.json'

    def save_config(self):
        """
        @summary: save jboss config to file
        """
        # TODO: this can throw OSError
        # do we really want to terminate the program here?
        common.make_directory(self.config_dir)
        common.log("Saving JBoss config to file: %s" % self._config_file())
        try:
            with open(self._config_file(), 'wb') as outfile:
                json.dump(self.litp_dict, outfile)
                return True
        except IOError as e:
            common.log("Failed to save config to \"%s\" - %s"
                       % (self._config_file(), e),
                       level="ERROR")
            return False

    def remove_config(self):
        os.remove(self._config_file())

    def remove_state_dir(self):
        """
        @summary: remove state directory containing saved config
        """
        try:
            shutil.rmtree(self.config_dir)
        except Exception as ex:  # pylint: disable=W0703
            common.log("Failed to remove state dir: %s. %s"
                       % (self.config_dir, ex),
                       level="ERROR")

    @staticmethod
    def _load_file(jboss_instance):
        # TODO replace str(jboss_instance) with something without spaces and
        # other funny characters
        return LITP_JBOSS_DATA_DIR + str(jboss_instance) + "/config.json"

    @staticmethod
    def load_config(jboss_instance):
        """
        @summary: load jboss config from file
        """
        load_file = LitpJbossConfig._load_file(jboss_instance)
        common.log("Loading JBoss config from file: %s" % load_file)
        try:
            with open(load_file) as infile:
                data = json.load(infile)
                return LitpJbossConfig(config_dict=data)
        except IOError:
            common.log("Unable to load config from \"%s\""
                       % (load_file),
                       level="INFO")
            return None
        except Exception as ex:
            common.log("Unable to load config from \"%s\": %s"
                       % (load_file, ex),
                       level="ERROR")
            sys.exit(1)

    def _lock_file(self):
        return self.config_dir + '/lockfile'

    def create_lock(self):
        common.make_directory(self.config_dir)
        open(self._lock_file(), 'w').close()

    def remove_lock(self):
        os.remove(self._lock_file())

    def lock_exists(self):
        return os.path.isfile(self._lock_file())
