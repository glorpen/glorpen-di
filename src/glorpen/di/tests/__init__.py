import sys

import unittest

from glorpen.di.tests.python2 import *
if sys.hexversion >= 0x03000000:
    from glorpen.di.tests.python3 import *

def additional_tests():
    t = unittest.TestSuite()
    return t