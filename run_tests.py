#!/usr/bin/env python3

import sys
import unittest

runner = unittest.TextTestRunner(verbosity=1)

tests = unittest.TestLoader().discover("./test")

if not runner.run(tests).wasSuccessful():
    sys.exit(1)
