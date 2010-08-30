import unittest

from openmdao.lib.caseiterators.listcaseiter import ListCaseIterator
from openmdao.main.api import Case
from openmdao.main.uncertain_distributions import NormalDistribution
from openmdao.main.caseiter import caseiter_to_dict

class CaseIterTestCase(unittest.TestCase):

    def setUp(self):
        cases = []
        for i in range(20):
            inputs = [('comp1.x', None, float(i)), ('comp1.y', None, i*2.)]
            outputs = [('comp1.z', None, i*1.5), ('comp2.normal', None, NormalDistribution(float(i),0.5))]
            if i < 10:
                msg = ''
            else:
                msg = 'had an error'
            cases.append(Case(inputs=inputs, outputs=outputs, ident='case%s'%i, msg=msg))
        self.caseiter = ListCaseIterator(cases)
        self.varnames = ['comp2.normal', 'comp1.x', 'comp1.z']
        
    def test_caseiter_to_dict_without_errors(self):
        dct = caseiter_to_dict(self.caseiter, self.varnames, include_errors=False)
        
        self.assertEqual(len(dct), 3)
        
        for name,value in dct.items():
            self.assertEqual(len(value), 10)
            if name == 'comp2.normal':
                self.assertTrue(isinstance(value[0], NormalDistribution))
            else:
                self.assertTrue(isinstance(value[0], float))

    def test_caseiter_to_dict_with_errors(self):
        dct = caseiter_to_dict(self.caseiter, self.varnames, include_errors=True)
        
        self.assertEqual(len(dct), 3)
        
        for name,value in dct.items():
            self.assertEqual(len(value), 20)
            if name == 'comp2.normal':
                self.assertTrue(isinstance(value[0], NormalDistribution))
            else:
                self.assertTrue(isinstance(value[0], float))

if __name__ == "__main__":
    unittest.main()


