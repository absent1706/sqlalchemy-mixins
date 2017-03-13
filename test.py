import os
import unittest

loader = unittest.TestLoader()
tests = loader.discover(os.path.join(os.path.dirname(__file__),
                                     'sqlalchemy_mixins'))
testRunner = unittest.runner.TextTestRunner()
testRunner.run(tests)