##############################################################################
# COPYRIGHT Ericsson AB 2013,2014
#
# The copyright to the computer program(s) herein is the property of
# Ericsson AB. The programs may be used and/or copied only with written
# permission from Ericsson AB. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
##############################################################################

from litpmnjboss.litp_jboss_base import LitpJbossBase

jboss_app_var_names = ('name', 'version', 'install_source')


class LitpJbossSupportPackageConfig(LitpJbossBase):
    """
    LITP JBOSS Support Package Config
    """

    def __init__(self, config_dict=None, container=None):
        """
        @summary: init for support package config
        """
        super(LitpJbossSupportPackageConfig, self).__init__(
            config_dict=config_dict)
        self.container = container
        if self.litp_dict is not None:
            self._init_config()

    def _init_config(self):
        """
        @summary: init support package based on config_dict
        """
        for name in jboss_app_var_names:
            self.config[name] = self.litp_dict.get('LITP_JEE_SP_' + name,
                                                   None)
