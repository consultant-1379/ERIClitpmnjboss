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
Provides management JBoss application config class
to represent and store a JBoss applications configuration
"""
from litpmnjboss.litp_jboss_base import LitpJbossBase

jboss_app_var_names = ('install_source', 'name', 'version', 'app_type',
                       'pre_upgrade', 'post_upgrade',
                       'pre_undeploy', 'post_undeploy',
                       'pre_deploy', 'post_deploy',
                       'pre_shutdown', 'post_shutdown',
                       'pre_start', 'post_start')


class LitpJbossAppConfig(LitpJbossBase):
    """
    LITP JBOSS App Config
    """

    def __init__(self, config_dict=None, container=None):
        """
        @summary: init for jboss app config
        """
        super(LitpJbossAppConfig, self).__init__(config_dict=config_dict)
        self.container = container
        if self.litp_dict is not None:
            self._init_config()

    def _init_config(self):
        """
        @summary: init jboss app based on config_dict
        """
        for name in jboss_app_var_names:
            self.config[name] = self.litp_dict.get('LITP_JEE_DE_' + name,
                                                   None)

        self.config['process_user'] = self.litp_dict.get(
            'LITP_JEE_CONTAINER_process_user', 'root')

    def get_jboss_config(self):
        """
        @summary: return the jboss config object
        """
        return self.container

    def make_env(self):
        """
        @summary: returns env dictionary with litp dictionary
        """
        env = self.litp_dict.copy()
        try:
            env.update(self.container.env_dict)
        except AttributeError:
            pass
        return env
