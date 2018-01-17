import unittest
import zope.component.testing
import zope.intid.interfaces

from BTrees.IFBTree import IFSet
from zope.catalog.catalog import Catalog
from zope.catalog.field import FieldIndex
from zope.catalog.interfaces import ICatalog
from zope.catalog.text import TextIndex
from zope.component import provideUtility, getUtility
from zope.container.contained import Contained
from zope.interface import Interface, Attribute, implements

from hurry.query import query
from hurry.query.interfaces import IQuery


"""Bring `query` testcoverage to 100% without polluting the doctest"""


class IContent(Interface):
    f1 = Attribute('f1')
    f2 = Attribute('f2')
    f3 = Attribute('f3')
    f4 = Attribute('f4')
    t1 = Attribute('t1')
    t2 = Attribute('t2')


class Content(Contained):
    implements(IContent)

    def __init__(self, id, f1='', f2='', f3='', f4='', t1='', t2=''):
        self.id = id
        self.f1 = f1
        self.f2 = f2
        self.f3 = f3
        self.f4 = f4
        self.t1 = t1
        self.t2 = t2

    def __cmp__(self, other):
        return cmp(self.id, other.id)

    def __repr__(self):
        return '<Content "{}">'.format(self.id)


class DummyIntId(object):
    implements(zope.intid.interfaces.IIntIds)
    MARKER = '__dummy_int_id__'

    def __init__(self):
        self.counter = 0
        self.data = {}

    def register(self, obj):
        intid = getattr(obj, self.MARKER, None)
        if intid is None:
            setattr(obj, self.MARKER, self.counter)
            self.data[self.counter] = obj
            intid = self.counter
            self.counter += 1
        return intid

    def getId(self, obj):
        return getattr(obj, self.MARKER)

    def getObject(self, intid):
        return self.data[intid]

    def __iter__(self):
        return iter(self.data)


class NullTerm(query.Term):

    def apply(self, cache, context=None):
        return IFSet()


class QueryTest(unittest.TestCase):

    tearDown = zope.component.testing.tearDown

    def setUp(self):
        """emulate the doctest fixtures"""
        self.intid = DummyIntId()
        provideUtility(self.intid, zope.intid.interfaces.IIntIds)
        self.catalog = Catalog()
        provideUtility(self.catalog, ICatalog, 'catalog1')
        self.catalog['f1'] = FieldIndex('f1', IContent)
        self.catalog['f2'] = FieldIndex('f2', IContent)
        self.catalog['f3'] = FieldIndex('f3', IContent)
        self.catalog['f4'] = FieldIndex('f4', IContent)
        self.catalog['t1'] = TextIndex('t1', IContent)
        self.catalog['t2'] = TextIndex('t2', IContent)
        provideUtility(query.Query(), IQuery)
        self.setup_content()

    def setup_content(self):
        content = [
            Content(1, 'a', 'b', 'd'),
            Content(2, 'a', 'c'),
            Content(3, 'X', 'c'),
            Content(4, 'a', 'b', 'e'),
            Content(5, 'X', 'b', 'e'),
            Content(6, 'Y', 'Z')]
        for entry in content:
            self.catalog.index_doc(self.intid.register(entry), entry)

    def searchResults(self, q, context=None):
        query = getUtility(IQuery)
        return query.searchResults(q, context)

    def displayQuery(self, q, context=None):
        r = self.searchResults(q, context)
        return [e.id for e in sorted(list(r))]

    def test_setup(self):
        """verify test fixtures by reproducing first doctest"""
        f1 = ('catalog1', 'f1')
        self.assertEqual(self.displayQuery(query.All(f1)),
                         [1, 2, 3, 4, 5, 6])
