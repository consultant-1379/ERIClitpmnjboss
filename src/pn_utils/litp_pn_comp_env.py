#!/usr/bin/python
##############################################################################
# COPYRIGHT Ericsson AB 2013,2014
#
# The copyright to the computer program(s) herein is the property of
# Ericsson AB. The programs may be used and/or copied only with written
# permission from Ericsson AB. or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the
# program(s) have been supplied.
##############################################################################
'''
Component Environment Instantiator
Created on Feb 20, 2013

'''
import os
import re
import sys
import subprocess
import logging.config

if not os.environ.get('TESTING_FLAG', None):
    logdir = '/var/log/litp/'
    if not os.path.exists(logdir):
        os.mkdir(logdir)
    logging.config.fileConfig("/etc/litp_jboss_logging.conf")
else:
    # Don't try reading /etc/litp_logging.conf for unit tests
    pass
logger = logging.getLogger("pn_utils")

PREFIX = 'litp-CompEnv-Instantiator_'

REDUNDANCY_MODEL = {
"SA_AMF_2N_REDUNDANCY_MODEL": "1",
"SA_AMF_NPM_REDUNDANCY_MODEL": "2",
"SA_AMF_N-WAY_REDUNDANCY_MODEL": "3",
"SA_AMF_N_WAY_ACTIVE_REDUNDANCY_MODEL": "4",
"SA_AMF_NO_REDUNDANCY_MODEL": "5"}


class CompEnvInstantiator(object):
    """
    Component Environment Instantiator
    A utility class that instantiates a CMW component's
    environment by using the SA_AMF_COMPONENT_NAME env var
    to indirectly discover a .env file pre-installed on the
    system (via AMF Install Campaign).
    """

    def __init__(self, env_dict=None):

        self.oldEnvLocation = "/cluster/environment/"
        self.nodeEnvLocation = "/opt/environment/"

        #logger.debug("Reading .env files from %s" % (self.nodeEnvLocation))

        if env_dict is None:
            env_dict = os.environ

        self.env_dict = env_dict
        self.command = self.env_dict.get('WRAPPER_COMMAND')
        self.sa_amf_component_name = self.env_dict.get('SA_AMF_COMPONENT_NAME')

        this_comp = ""
        if self.sa_amf_component_name:
            this_comp = self.sa_amf_component_name.split(',')[0].split('=')[1]

        self.prefix = PREFIX + str(this_comp)
        self.envFileName = None
        #self.log("Starting...")
        #if self.isNotHealthCheck():
        #    self.remove_unsupported_dependenies()

    def __run_cmd__(self, cmd):
        cmd_ret = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, shell=True)
        cmd_ret.wait()
        stdout = cmd_ret.stdout.read()
        rc = cmd_ret.returncode
        return stdout, rc

    def remove_unsupported_dependenies(self):

        sa_amf_component_name = self.env_dict.get('SA_AMF_COMPONENT_NAME')

        if sa_amf_component_name and \
           sa_amf_component_name.find("_vcsgrp_") > -1:
            safDepends = self.getDependencies()

            if safDepends:
                self.log('Found SaAmfSIDependency objects {0}'
                          .format(safDepends))

                my_safSg_obj = sa_amf_component_name.split(',', 2)[-1]
                my_safsg_App = sa_amf_component_name.split(',', 2)[-1]\
                            .split('=')[-1]
                my_redundancyModel = None

                for safDepend in safDepends:
                    sg_AppSponsor = safDepend.split(',')[1].split('=')[-1]
                    sg_App = safDepend.split(',')[-1].split('=')[-1]

                    if my_safsg_App == sg_App:

                        if not my_redundancyModel:
                            my_redundancyModel = \
                                self.getRedundancyModel(my_safSg_obj)

                        if my_redundancyModel == \
                            REDUNDANCY_MODEL["SA_AMF_2N_REDUNDANCY_MODEL"]:

                            sponsor_safSg_obj = 'safSg={0},safApp={1}'\
                                    .format(sg_AppSponsor.strip('_App'),
                                    sg_AppSponsor)

                            sponsor_redundancyModel = \
                                    self.getRedundancyModel(sponsor_safSg_obj)

                            if sponsor_redundancyModel == \
                                REDUNDANCY_MODEL["SA_AMF_2N_REDUNDANCY_MODEL"]:

                                self.log('Dependency supported {0}'
                                              .format(safDepend))
                                continue
                            else:
                                self.log('Dependency not supported {0}'
                                      ' This SG:{1} RedundancyModel:{2} '
                                      ' Sponsor SG:{3} RedundancyModel:{4}'
                                      .format(safDepend, my_safsg_App,
                                      my_redundancyModel, sg_AppSponsor,
                                      sponsor_redundancyModel))
                                self.deleteDependency(safDepend)
                        else:
                            self.log('Dependency not supported {0}'
                                ' This SG:{1} RedundancyModel:{2} '
                                .format(safDepend, my_safsg_App,
                                my_redundancyModel))
                            self.deleteDependency(safDepend)
                    else:
                        self.log('{0} is not a dependency of {1}'\
                                      .format(my_safsg_App, safDepend))

            else:
                self.log('No dependencies found')

    def getRedundancyModel(self, safSg_obj):

        cmd = "immlist {0} | grep saAmfSGType |".format(safSg_obj) + \
              " awk '{ print $3 }'| xargs immlist |" +\
              " grep saAmfSgtRedundancyModel |" + \
              " awk '{ print $3 }'"
        stdout, rc = self.__run_cmd__(cmd)
        if rc:
            self.log('Failed to find Redundancy Model'
                          ' {0}:{1}'
                          .format(rc, stdout))
            return None
        return stdout.splitlines()

    def getDependencies(self):
        safDepends = list()
        cmd = "immfind -c SaAmfSIDependency"
        stdout, rc = self.__run_cmd__(cmd)
        if rc:
            self.log('Found no SaAmfSIDependency objects {0}:{1}'
                              .format(rc, stdout), level="ERROR")
            return safDepends
        safDepends = stdout.splitlines()
        return safDepends

    def deleteDependency(self, safDepend):
        #si = safDepend.split(',', 2)[-1]
        # no need to lock when deleting apparently
        cmd = "immcfg -d '{0}'".format(safDepend)
        stdout, rc = self.__run_cmd__(cmd)
        if rc:
            self.log('Found no SaAmfSIDependency objects {0}:{1}'
                              .format(rc, stdout))

            return False
        if safDepend in self.getDependencies():
            self.log('Error {0} still exists'\
                            .format(safDepend))
        else:
            self.log('{0} deleted successfully'\
                            .format(safDepend))
        return True

    def parseEnvFileName(self):
        """
        Parse the env file name from AMF env var
        SA_AMF_COMPONENT_NAME which is composed of
        safComp=<safComp>,safSu=<safSu=>.safSg=<safSg>.safApp=<safApp>

        Env file naming convention is <safSu>.<safSg>.<safApp>.env

        """

        if self.sa_amf_component_name is None:
            self.log("SA_AMF_COMPONENT_NAME not present in Env")
            return None
        else:
            if self.isNotHealthCheck():
                self.log("SA_AMF_COMPONENT_NAME =  %s" \
                      % (self.env_dict.get('SA_AMF_COMPONENT_NAME')))

            try:
                parts = self.sa_amf_component_name.split(',')
                if len(parts) != 4:
                    return None

                nameValueParts = {}

                for nameValuePart in parts:
                    name, value = nameValuePart.split('=')
                    nameValueParts[name] = value

                comp_name = re.sub('-CompType-[0-9]*', '',
                               nameValueParts['safComp'])
                self.envFileName = "{0}.{1}.{2}.{3}.env".format(
                                                     comp_name,
                                                     nameValueParts['safSu'],
                                                     nameValueParts['safSg'],
                                                     nameValueParts['safApp']
                                                        )
            except Exception as ex:  # pylint: disable=W0703
                self.log("Failed to parse SA_AMF_COMPONENT_NAME = " +  \
                              "%s : %s" %                                   \
                              (self.env_dict.get('SA_AMF_COMPONENT_NAME'),  \
                               ex.message), level="ERROR")
                self.log(" returning  %s.env" \
                      % (self.env_dict.get('SA_AMF_COMPONENT_NAME')),\
                      level="ERROR")
                return self.sa_amf_component_name + '.env'

            if self.isNotHealthCheck():
                self.log("Env File Name = %s" % (self.envFileName))

            return self.envFileName

    def appendEnvironment(self, envFileName=None):
        """
        Add the Env variables included in the envFileName
        to os.environ
        """
        if envFileName is None:
            return
        if self.isNotHealthCheck():
            self.log("appendEnvironment  %s " % (envFileName))

        if envFileName is not None:
            self.envFileName = envFileName

        self.envFileName = os.path.join(self.nodeEnvLocation, self.envFileName)

        #logger.debug("Absolute path name %s " % (self.envFileName))

        if not os.path.exists(self.envFileName):
            self.log("File does not exist: %s " % (self.envFileName))
            return

        with open(self.envFileName, "r") as f:
            for line in f.readlines():
                (key, _, value) = line.partition("=")
                os.environ[key] = value.strip().strip('"')
                # LITP-4220 blank out sensitive fields in logs
                if self.isSensitiveField(key):
                    value = '********\n'
                if self.isNotHealthCheck():
                    self.log("Appending Env Var %s  = %s" % (key, value))

    def isNotHealthCheck(self):
        if not self.command in ['healthc', 'HEALTHC', 'status']:
            return True

    def isSensitiveField(self, key):
        if 'password' in key.lower():
            return True
        return False

    def log(self, message, level='INFO', echo=False):
        """
        Print and log the supplied message
        """
        separator = ' - '
        prefix = PREFIX + separator

        if echo:
            print str(message)

        if level == 'INFO':
            logger.info(str(prefix) + str(message))
        elif level == 'DEBUG':
            logger.debug(str(prefix) + str(message))
        elif level == 'ERROR':
            logger.error(str(prefix) + str(message))
        else:
            msg = "Invalid logging level:" + str(level) + "message:" \
                      + str(message)
            logger.error(str(prefix) + str(msg))

if __name__ == '__main__':
    arglist = sys.argv[1:]
    if len(arglist):
        _cmd = arglist[0]
        os.environ['WRAPPER_COMMAND'] = _cmd.strip().strip('"')

    env = {'SA_AMF_COMPONENT_NAME':
    'safComp=sg2_env-CompType-4,safSu=sg2_App-SuType-1,'\
    'safSg=sg2,safApp=sg2_App'}
    #'safCompvcsgrp_jee_container-CompType-0,safSu=sg1_App-SuType-0,' \
    #'safSg=sg1,safApp=sg1_App'}
    # env = None
    # env = {'WRAPPER_COMMAND': 'healthc'}
    cEnvI = CompEnvInstantiator(env)
    cEnvI.appendEnvironment(cEnvI.parseEnvFileName())
