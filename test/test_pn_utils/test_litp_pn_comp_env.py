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
import os
os.environ["TESTING_FLAG"] = "1"
from pn_utils.litp_pn_comp_env import CompEnvInstantiator


class TestCompEnvInstantiator(unittest.TestCase):
    def setUp(self):
        self.env = {'SA_AMF_COMPONENT_NAME':
        'safComp=vcsgrp_jee_container-CompType-0,safSu=sg1_App-SuType-0,' +
        'safSg=sg1,safApp=sg1_App'} 

    def test_allowed_properties(self):
        cEnvI = CompEnvInstantiator(self.env)
        self.assertTrue(cEnvI.parseEnvFileName() == \
            'vcsgrp_jee_container.sg1_App-SuType-0.sg1.sg1_App.env')
        cEnvI.appendEnvironment(cEnvI.parseEnvFileName())

    def test_without_SA_AMF_COMPONENT_NAME_property(self):
        self.env = {}
        cEnvI = CompEnvInstantiator(self.env)
        fileName = cEnvI.parseEnvFileName()
        self.assertEqual(None, fileName, "fileName should be None \
            as SA_AMF_COMPONENT_NAME is not present");
        returnResult = cEnvI.appendEnvironment(fileName) 
        self.assertEqual(None, returnResult, "appendEnvironment should return \
             None as fileName is not defined"); 
 
           

if __name__ == '__main__':
    unittest.main()
