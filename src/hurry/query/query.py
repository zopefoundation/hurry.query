##############################################################################
#
# Copyright (c) 2005-2008 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

from zope.interface import implements

from zope.app import zapi
from zope.app.intid.interfaces import IIntIds
from zope.app.catalog.catalog import ResultSet
from zope.app.catalog.field import IFieldIndex
from zope.app.catalog.text import ITextIndex
from zope.app.catalog.interfaces import ICatalog

from BTrees.IFBTree import weightedIntersection, union, difference, IFBTree

from hurry.query import interfaces

# XXX look into using multiunion for performance?

class Query(object):
    implements(interfaces.IQuery)

    def searchResults(self, query):
        results = query.apply()
        if results is not None:
            uidutil = zapi.getUtility(IIntIds)
            results = ResultSet(results, uidutil)
        return results

class Term(object):
    def __and__(self, other):
        return And(self, other)

    def __rand__(self, other):
        return And(other, self)

    def __or__(self, other):
        return Or(self, other)

    def __ror__(self, other):
        return Or(other, self)

    def __invert__(self):
        return Not(self)

class And(Term):
    def __init__(self, *terms):
        self.terms = terms

    def apply(self):
        results = []
        for term in self.terms:
            r = term.apply()
            if not r:
                # empty results
                return r
            results.append((len(r), r))

        if not results:
            # no applicable terms at all
            # XXX should this be possible?
            return IFBTree()

        results.sort()

        _, result = results.pop(0)
        for _, r in results:
            _, result = weightedIntersection(result, r)
        return result

class Or(Term):
    def __init__(self, *terms):
        self.terms = terms

    def apply(self):
        results = []
        for term in self.terms:
            r = term.apply()
            # empty results
            if not r:
                continue
            results.append(r)

        if not results:
            # no applicable terms at all
            # XXX should this be possible?
            return IFBTree()

        result = results.pop(0)
        for r in results:
            result = union(result, r)
        return result

class Not(Term):
    def __init__(self, term):
        self.term = term

    def apply(self):
        return difference(self._all(), self.term.apply())

    def _all(self):
        # XXX may not work well/be efficient with extentcatalog
        # XXX not very efficient in general, better to use internal
        # IntIds datastructure but that would break abstraction..
        intids = zapi.getUtility(IIntIds)
        result = IFBTree()
        for uid in intids:
            result.insert(uid, 0)
        return result

class IndexTerm(Term):
    def __init__(self, (catalog_name, index_name)):
        self.catalog_name = catalog_name
        self.index_name = index_name

    def getIndex(self):
        catalog = zapi.getUtility(ICatalog, self.catalog_name)
        index = catalog[self.index_name]
        return index

class Text(IndexTerm):
    def __init__(self, index_id, text):
        super(Text, self).__init__(index_id)
        self.text = text

    def getIndex(self):
        index = super(Text, self).getIndex()
        assert ITextIndex.providedBy(index)
        return index

    def apply(self):
        index = self.getIndex()
        return index.apply(self.text)

class FieldTerm(IndexTerm):
    def getIndex(self):
        index = super(FieldTerm, self).getIndex()
        assert IFieldIndex.providedBy(index)
        return index

class Eq(FieldTerm):
    def __init__(self, index_id, value):
        assert value is not None
        super(Eq, self).__init__(index_id)
        self.value = value

    def apply(self):
        return self.getIndex().apply((self.value, self.value))

class NotEq(FieldTerm):
    def __init__(self, index_id, not_value):
        super(NotEq, self).__init__(index_id)
        self.not_value = not_value

    def apply(self):
        index = self.getIndex()
        all = index.apply((None, None))
        r = index.apply((self.not_value, self.not_value))
        return difference(all, r)

class Between(FieldTerm):
    def __init__(self, index_id, min_value, max_value):
        super(Between, self).__init__(index_id)
        self.min_value = min_value
        self.max_value = max_value

    def apply(self):
        return self.getIndex().apply((self.min_value, self.max_value))

class Ge(Between):
    def __init__(self, index_id, min_value):
        super(Ge, self).__init__(index_id, min_value, None)

class Le(Between):
    def __init__(self, index_id, max_value):
        super(Le, self).__init__(index_id, None, max_value)

class In(FieldTerm):
    def __init__(self, index_id, values):
        assert None not in values
        super(In, self).__init__(index_id)
        self.values = values

    def apply(self):
        results = []
        index = self.getIndex()
        for value in self.values:
            r = index.apply((value, value))
            # empty results
            if not r:
                continue
            results.append(r)

        if not results:
            # no applicable terms at all
            return IFBTree()

        result = results.pop(0)
        for r in results:
            result = union(result, r)
        return result

