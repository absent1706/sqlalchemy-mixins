"""
It's like
    python -m unittest discover sqlalchemy_mixins/

But also works for python < 2.7
"""
import sys
if sys.version_info < (2, 7):
    import unittest2 as unittest
else:
    import unittest

import os

loader = unittest.TestLoader()
tests = loader.discover(os.path.join(os.path.dirname(__file__),
                                     'sqlalchemy_mixins'))
testRunner = unittest.runner.TextTestRunner()
testRunner.run(tests)