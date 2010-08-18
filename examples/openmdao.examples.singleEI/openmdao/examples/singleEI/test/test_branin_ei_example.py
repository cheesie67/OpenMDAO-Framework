"""
Test for single criteria EI example.
"""

import unittest
import random

from openmdao.main.api import set_as_top
from openmdao.examples.singleEI.branin_ei_example import Analysis, Iterator
from openmdao.lib.doegenerators.full_factorial import FullFactorial


class EITest(unittest.TestCase):
    """Test to make sure the EI sample problem works as it should"""
    
    def setUp(self):
        pass

    def tearDown(self):
        pass
    
    def test_EI(self): 
        random.seed(10)
        analysis = Analysis()
        
        set_as_top(analysis)
        analysis.DOE_trainer.DOEgenerator = FullFactorial(3, 2)
        analysis.iterations = 3
        analysis.run()
        analysis.cleanup()
        self.assertAlmostEqual(9.93,analysis.EI_driver.next_case[0].inputs[0][2],1)
        self.assertAlmostEqual(10.81,analysis.EI_driver.next_case[0].inputs[1][2],1)
        
        
if __name__=="__main__": #pragma: no cover
    unittest.main()
