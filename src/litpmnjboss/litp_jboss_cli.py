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
Provides JBoss CLI class to enable /execute JBoss CLI commands
"""
import litpmnjboss.litp_jboss_common as common


SUCCESS = 0
FAILURE = 1
TIMEOUT = 2


class JBossCLITimeoutException(Exception):
    pass


class LitpJbossCli(object):
    """
    JBOSS CLI
    """
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

    def __init__(self, config):

        self.config = config

        common.container_name = self.config.get('instance_name')

        self.jboss_cli = config.make_env()['JBOSS_CLI']

    def _exec_cmd(self, cmd, timeout=120):
        common.log("Executing JBOSS CLI command: %s" % cmd, level="DEBUG")
        env = self.config.make_env()
        rc, stdout, stderr = common.exec_cmd(cmd, env, timeout)
        common.log("JBOSS CLI command results " + \
                     "rc:%s, stdout:%s, stderr:%s"
                     % (rc, stdout, stderr), level="DEBUG")
        return (rc, stdout, stderr)

    def run(self, cmd):
        assert cmd is not None
        return self._exec_cmd(
                    cmd='%s -c --command="%s"' % (self.jboss_cli, cmd))

    def run_commands(self, cmds, timeout=120):
        assert cmds is not None
        assert len(cmds) > 0
        (rv, stdout, stderr) = self._exec_cmd(
                cmd='%s -c --commands="%s"' % (self.jboss_cli, ','.join(cmds)),
                timeout=timeout)
        if rv != 0:
            if self._is_connection_issue(stderr):
                return TIMEOUT, stdout, stderr
        return (rv, stdout, stderr)
