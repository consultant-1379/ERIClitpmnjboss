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
Provides common utils for litp_jboss and litp_jboss_app.
"""
import os
import shutil
import subprocess
import logging.config

logdir = '/var/log/litp/'
if not os.environ.get('TESTING_FLAG', None):
    if not os.path.exists(logdir):
        os.mkdir(logdir)
    logging.config.fileConfig('/etc/litp_jboss_logging.conf')
else:
    # Don't try reading /etc/litp_logging.conf for unit tests
    pass
logger = logging.getLogger("litp_jboss")

# ANSI codes
ANSI_MOVE_CURSOR = '\033[60G'
ANSI_FAILURE_COLOR = '\033[1;31m'
ANSI_SUCCESS_COLOR = '\033[1;32m'
ANSI_NO_COLOR = '\033[0m'

container_name = None
de_name = None


def echo_success(msg='', state='OK'):
    """
    Port of standard RHEL function, echos pretty colorized  success
    message with the following format "<msg> [  <state>  ]"
    """
    log(msg)
    if len(msg) > 59:
        msg = msg + '\n'
    print "%s%s[  %s%s%s  ]"\
             % (msg, ANSI_MOVE_CURSOR, ANSI_SUCCESS_COLOR,
                state, ANSI_NO_COLOR)


def echo_failure(msg='', state='FAILED'):
    """
    Port of standard RHEL function, echos pretty colorized failure
    message with the following format "<msg> [  <state>  ]"
    """
    log(msg, level='ERROR')
    if len(msg) > 59:
        msg = msg + '\n'
    print "%s%s[%s%s%s]"\
            % (msg, ANSI_MOVE_CURSOR, ANSI_FAILURE_COLOR,
               state, ANSI_NO_COLOR)


def log(message, level='INFO', echo=False):
    """
    Print and log the supplied message
    """
    prefix = ''
    seperator = ' - '
    if container_name is not None:
        prefix = prefix + str(container_name) + seperator
    if de_name is not None:
        prefix = prefix + str(de_name) + seperator

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


def make_directory(directory):
    """
    make supplied directory
    """
    try:
        if not os.path.isdir(directory):
            log("Creating directory %s" % directory)
            os.makedirs(directory)
    except OSError as e:
        log('Error creating directory %s: %s' % (directory, e), level='ERROR')
        raise


def remove_directory(directory):
    """
    remove supplied directory
    """
    try:
        if os.path.exists(directory) and os.path.isdir(directory):
            log("Deleting directory %s" % directory)
            shutil.rmtree(directory, ignore_errors=False)
    except Exception as ex:  # pylint: disable=W0703
        log(ex, level="DEBUG")
        msg = 'Failed to delete "%s" ' % (directory)
        echo_failure(msg)
        return 1


def exec_cmd(cmd, env, timeout=120):
    assert env is not None
    assert cmd is not None

    p = subprocess.Popen(cmd,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         shell=True,
                         env=env)
    try:
        p.wait(timeout=timeout)  # pylint: disable=E1123
    except Exception as e:   # pylint: disable=W0703
        return (1, '', "command execute timed out: %s" % e)
    return (p.returncode, p.stdout.readlines(), p.stderr.readlines())


def run_fragments(fragment, process_user, env):
    """
    @summary: Runs all executable files inside specified path.

    @param fragment: Filesystem path
    @type fragment: string
    """
    if fragment is not None:
        fragment = str(fragment)
        if not (os.path.exists(fragment) and os.path.isdir(fragment)):
            log("Path \"%s\" does not exists or " \
                           "is not a directory." % (fragment), echo=True)
            return 1

        if not os.access(fragment, os.X_OK):
            log("Path \"%s\" is not accessible, please run as root"\
                                                % (fragment), echo=True)
            return 1

        log("Running scripts in %s" % (fragment), echo=True)
        scripts = [os.path.join(fragment, a) for a in os.listdir(fragment)\
                        if os.path.exists(os.path.join(fragment, a)) \
                        and os.path.isfile(os.path.join(fragment, a)) \
                        and os.access(os.path.join(fragment, a), os.X_OK)]
        log("Scripts found:%s" % str(scripts), level="DEBUG")
        for script in scripts:
            log("Running script:%s" % str(script))
            cmd = 'sudo -E -u %s %s' % (process_user, script)
            (rc, stdout, stderr) = exec_cmd(cmd, env=env)
            log("Script results " + \
                     "rc:%s, stdout:%s, stderr:%s"
                     % (rc, stdout, stderr))
            if rc != 0:
                log("Failed to run script: %s" % script, echo=True,
                    level="ERROR")
                return rc
    return 0
