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
"""
Provides management interface for JBoss applications (Deployable Entities)
and resources (JEEProperty, JMSQueue, JMSTopic) to litp_jboss.
"""
import os

import litpmnjboss.litp_jboss_common as common
from litpmnjboss import litp_jboss_cli


class CliConnectionException(Exception):
    pass


class LitpJbossApp(object):
    """
    LITP JBOSS App Manager
    """

    def __init__(self, config):
        """
        @summary: init for jboss app
        """

        self.config = config

        self.jbosscli = litp_jboss_cli.LitpJbossCli(
                                self.config.get_jboss_config())

        self._process_user = self.config.get('process_user')

        # app name and version used for logging
        self.app_full_name = str(self.config.get('name')) + ', ' + \
                             str(self.config.get('version'))

        # init logging prefix variables
        common.de_name = self.config.get('name')
        # Keeping pylint happy
        self.deployed_app = None

    def _is_connection_issue(self, stderr):
        """
        @summary: checks stderr to see if litp_jboss_cli timed out
        """
        if isinstance(stderr, list):
            _stderr = "\n".join(stderr)
        else:
            _stderr = stderr
        if 'java.net.ConnectException' in _stderr or \
                'JBOSS CLI command timed out' in _stderr:
            return True
        return False

    def _is_deployed(self):
        """
        @summary: Return true is the application is deployed
        """
        common.log("Checking application \"%s\" is deployed"
                    % (self.config.get('name')))
        (rc, stdout, stderr) = self.jbosscli.run("ls deployment")
        if rc is 0:
            for app_line in stdout:
                if str(app_line).rstrip('\n') == self.config.get('name'):
                    common.log(
                        "The application \"%s\" is deployed"
                         % self.config.get('name'))
                    return True
            common.log("The application \"%s\" is not deployed"
                         % self.config.get('name'))
            return False

        else:
            common.log("Error from jboss cli in _is_deployed()"
                          " check for application \"%s\""
                             % (self.config.get('name')), level="ERROR")
            if self._is_connection_issue(stderr):
                raise CliConnectionException
            return False

    def _is_started(self):
        """
        @summary: Return true is the application is started
        """
        common.log("Checking application %s is started"
                    % (self.config.get('name')))
        (rc, stdout, stderr) = self.jbosscli.run("ls deployment=" + \
                                           str(self.config.get('name')))
        if rc is 0:
            if "status=OK" in str(stdout):
                common.log("The application \"%s\" is running"
                             % (str(self.config.get('name'))))
                return True
            else:
                common.log("The application \"%s\" is not running"
                             % (str(self.config.get('name'))))
                return False
        else:
            common.log("Error from jboss cli in _is_started()"
                          " check for application \"%s\""
                             % (str(self.config.get('name'))),
                                level="ERROR")
            if self._is_connection_issue(stderr):
                raise CliConnectionException
            return False

    def _isfile(self, filepath):
        return os.path.isfile(filepath)

    def get_install_file(self):
        install_file = None
        candidate = self.config.get('install_source')

        if self.config.get('install_source') is None:
            common.log("Please specify app install source")
        elif self._isfile(self.config.get('install_source')):
            install_file = self.config.get('install_source')
        else:
            if self.config.get('name') is None:
                common.log("Please specify the application name", echo=True)
            elif self.config.get('version') is None:
                common.log("Please specify application version", echo=True)
            elif self.config.get('app_type') is None:
                common.log("Please specify application type" + \
                                          " (war/jar/ear)", echo=True)
            elif os.path.isdir(self.config.get('install_source')):
                # strip 'extension' from name
                app_name = str(self.config.get('name')).rsplit('.', 1)[0]
                # and append version and app_type
                app_name += '-' + self.config.get('version') + '.' + \
                                  self.config.get('app_type')
                candidate = os.path.join(self.config.get('install_source'),
                                         app_name)
                if self._isfile(candidate):
                    install_file = candidate

        if install_file is None:
            common.log("There is no application at the " + \
                        "install_source provided; install_source=" + \
                        str(candidate), level="ERROR", echo=True)
        return install_file

    def _run_fragments(self, fragment_name):
        fragment_dir = self.config.get(fragment_name)
        return common.run_fragments(fragment_dir, self._process_user,
                                    env=self.config.make_env())

    def _do_start(self):
        """
        @summary: Runs pre_start, start app, run post_start.

        @rtype: int
        @return: Return code (0 or non-zero integer)
        """
        try:
            if self._run_fragments('pre_start') != 0:
                return 1
            rc, _, stderr = self.jbosscli.run("deploy --name=" + \
                                                      self.config.get('name'))
            if rc is 0:
                common.echo_success(msg="\"%s\" has been started" %
                                    self.app_full_name)
                if self._run_fragments('post_start') != 0:
                    return 1
            else:
                common.echo_failure(msg="\"%s\" failed "
                    " to start" %
                    self.app_full_name)
                if self._is_connection_issue(stderr):
                    raise CliConnectionException
            return rc
        except CliConnectionException:
            return 2
        except Exception:
            raise

    def start(self, old_config=None):
        """
        @summary: start this application
        """
        try:
            if self._is_deployed():
                if old_config is None:
                    common.echo_failure(msg="\"%s\" is already deployed, " \
                                            "but its state is not known." % \
                                            self.config.get('name'))
                    return 1

                new_version = self.config.get('version')
                new_install_source = self.config.get('install_source')
                old_version = old_config.get('version')
                old_install_source = old_config.get('install_source')

                if (new_version != old_version) or \
                   (new_install_source != old_install_source):
                    return self._upgrade(old_config, self.config)

                if self._is_started():
                    common.echo_failure(msg="\"%s\" is"
                                            " already started"
                                            % self.app_full_name)
                    return 0
                else:
                    rc = self._do_start()
                    return rc
            else:
                rc = self.deploy()
                if rc != 0:
                    return rc
                rc = self._do_start()
                return rc
        except CliConnectionException:
            return 2
        except Exception:
            raise

    def stop(self):
        """
        @summary: stop this application
        """
        try:
            if self._is_deployed():
                if self._is_started():
                    if self._run_fragments('pre_shutdown') != 0:
                        return 1
                    (rc, _, stderr) = self.jbosscli.run("undeploy " \
                            "--name=" + self.config.get('name') + \
                            " --keep-content")
                    if rc is 0:
                        common.echo_success(msg="\"%s\" has"
                                        " been stopped"
                                        % self.app_full_name)
                        if self._run_fragments('post_shutdown') != 0:
                            return 1
                    else:
                        common.echo_failure(msg="\"%s\" could "
                                        "not be stopped"
                                        % self.app_full_name)
                        if self._is_connection_issue(stderr):
                            raise CliConnectionException
                    return rc
                else:
                    common.echo_failure(msg="\"%s\" is not running"
                                        % self.app_full_name)
                    return 0
            else:
                common.echo_failure(msg="\"%s\" is not deployed"
                                        % self.app_full_name)
                return 1
        except CliConnectionException:
            return 2
        except Exception:
            raise

    def status(self):
        """
        @summary: check status of this application
        """
        try:
            if self._is_deployed():
                if self._is_started():
                    common.echo_success(msg="\"%s\" is running"
                                        % self.app_full_name)
                    return 0
                else:
                    common.echo_failure(msg="\"%s\" is not running"
                                        % self.app_full_name)
                    return 1
            else:
                common.echo_failure(msg="\"%s\" is not deployed"
                                        % self.app_full_name)
                return 1
        except CliConnectionException:
            return 2
        except Exception:
            raise

    def restart(self):
        """
        @summary: restart this application
        """
        result = self.stop()
        if result is 0:
            result = self.start()
        return result

    def deploy(self):
        """
        @summary: deploy this application
        """
        try:
            if self._is_deployed():
                common.echo_failure(
                            msg="\"%s\" has already been deployed" % \
                                self.app_full_name)
                return 0
            else:
                install_file = self.get_install_file()
                if install_file is None:
                    return 1

                if self._run_fragments('pre_deploy') != 0:
                    return 1
                (rc, _, stderr) = self.jbosscli.run("deploy " + \
                                       str(install_file) + " --name=" + \
                                       self.config.get('name') + " --disabled")
                if rc is 0:
                    common.echo_success(
                            msg="\"%s\" has been deployed" % \
                                self.app_full_name)
                    if self._run_fragments('post_deploy') != 0:
                        return 1
                else:
                    common.echo_failure(
                            msg="\"%s\" failed to be deployed" % \
                                self.app_full_name)
                    if self._is_connection_issue(stderr):
                        raise CliConnectionException
                return rc
        except CliConnectionException:
            return 2
        except Exception:
            raise

    def undeploy(self):
        """
        @summary: un-deploy this application
        """
        try:
            if self._is_deployed():
                # if application is running stop it before un-deploy
                if self._is_started():
                    rc = self.stop()
                    if rc != 0:
                        return rc
                # un-deploy the deployed application
                self.deployed_app = str(self.config.get('name'))
                if self._run_fragments('pre_undeploy') != 0:
                    return 1
                (rc, _, stderr) = \
                        self.jbosscli.run("undeploy " + self.deployed_app)
                if rc is 0:
                    common.echo_success(
                            msg="\"%s\" has been un-deployed" % \
                                self.deployed_app)
                    if self._run_fragments('post_undeploy') != 0:
                        return 1
                else:
                    common.echo_failure(
                            msg="\"%s\" failed to be un-deployed" % \
                                self.deployed_app)
                    if self._is_connection_issue(stderr):
                        raise CliConnectionException
                return rc
            else:
                common.echo_failure(
                            msg="\"%s\" is not deployed" % \
                                self.app_full_name)
                return 0
        except CliConnectionException:
            return 2
        except Exception:
            raise

    def _upgrade(self, old_config, new_config):
        """
        @summary: upgrade this application
        """
        common.log('Upgrading application "%s" from version "%s" (%s) '
                   'to version "%s" (%s)' % \
                   (self.config.get('name'),
                    old_config.get('version'),
                    old_config.get('install_source'),
                    new_config.get('version'),
                    new_config.get('install_source')),
                   echo=True)

        if self._run_fragments('pre_upgrade') != 0:
            return 1

        common.log("Un-deploying old application \"%s\" version \"%s\" (%s)"
                     % (self.config.get('name'),
                        old_config.get('version'),
                        old_config.get('install_source')))
        result = self.undeploy()
        if result is 0:
            result = self.start()

            if result is 0:
                common.echo_success(
                        msg="\"%s\" has been upgraded"
                        % self.app_full_name)
                if self._run_fragments('post_upgrade') != 0:
                    return 1
            else:
                common.echo_failure(
                        msg="\"%s\" failed to upgrade"
                        % self.app_full_name)
        return result
