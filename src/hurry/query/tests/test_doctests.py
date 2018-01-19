import unittest
import doctest


def test_suite():
    return unittest.TestSuite((
        doctest.DocFileSuite('../query.txt'),
        ))
