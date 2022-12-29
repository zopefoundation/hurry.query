import doctest
import unittest


def test_suite():
    return unittest.TestSuite((
        doctest.DocFileSuite('../query.txt'),
        ))
