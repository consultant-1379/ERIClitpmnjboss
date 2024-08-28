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
Provides base class for JBoss configuration classes
"""

LITP_PREFIX = 'LITP_'


class LitpJbossBase(object):
    """
    LITP JBOSS Base Class
    """

    def __init__(self, config_dict=None):
        """
        Init for Jboss Base
        """
        self.config = {}
        self.env_dict = {}
        self.litp_dict = {}
        if config_dict is not None:
            self._init_env_dict(config_dict)
            self._init_litp_dict(config_dict)

    def _filter_config_dict(self, config_dict, startswith=''):
        return dict([(key, value) for key, value in config_dict.items()
                    if not key.startswith(startswith)])

    def _init_env_dict(self, config_dict):
        """
        Init env dict with the blank environment
        """
        self.env_dict = self._filter_config_dict(config_dict, LITP_PREFIX)

    def _init_litp_dict(self, config_dict):
        """
        Init env dict with the blank environment
        """
        other = self._filter_config_dict(config_dict, LITP_PREFIX)
        self.litp_dict = dict([(key, val) for key, val in config_dict.items()
                               if key not in other])

    def get(self, property_name):
        """
        Returns config property
        """
        return self.config.get(property_name, None)

    def make_env(self):
        """
        Returns env dictionary with litp dictionary
        """
        return dict(self.env_dict.items() + self.litp_dict.items())
