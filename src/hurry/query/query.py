##############################################################################
#
# Copyright (c) 2005-2009 Zope Foundation and Contributors.
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
"""Basic query implementation

This module contains an IQuery utility implementation, basic query term
implementations and concrete term implementations for zope.catalog indexes.

$Id$
"""
import itertools

from BTrees.IFBTree import weightedIntersection, union, difference, IFBTree
from zope.cachedescriptors.property import Lazy
from zope.catalog.field import IFieldIndex
from zope.catalog.interfaces import ICatalog
from zope.catalog.text import ITextIndex
from zope.component import getUtility
from zope.interface import implements
from zope.intid.interfaces import IIntIds
from zope.index.interfaces import IIndexSort
from hurry.query import interfaces

# XXX look into using multiunion for performance?


class QueryResults(object):

    def __init__(self, context, all_results, selected_results):
        self.context = context
        self.__all = all_results
        self.__selected = selected_results

    @Lazy
    def get(self):
        return getUtility(IIntIds, '', self.context).getObject

    @property
    def total(self):
        return len(self.__all)

    @property
    def count(self):
        return len(self.__selected)

    def __len__(self):
        return len(self.__selected)

    def __iter__(self):
        for uid in self.__selected:
            yield self.get(uid)


class Query(object):
    implements(interfaces.IQuery)

    def searchResults(
            self, query, context=None, sort_field=None, limit=None,
            reverse=False, start=0):

        all_results = query.apply(context)
        if not all_results:
            return QueryResults(context, [], [])

        is_iterator = False
        if sort_field is not None:
            # Like in zope.catalog's searchResults we require the given
            # index to sort on to provide IIndexSort. We bail out if
            # the index does not.
            catalog_name, index_name = sort_field
            catalog = getUtility(ICatalog, catalog_name, context)
            index = catalog[index_name]
            if not IIndexSort.providedBy(index):
                raise ValueError(
                    'Index {} in catalog {} does not support '
                    'sorting.'.format(index_name, catalog_name))
            sort_limit = None
            if limit is not None:
                sort_limit = start + limit
            selected_results = index.sort(
                all_results,
                limit=sort_limit,
                reverse=reverse)
            if start:
                selected_results = itertools.islice(
                    selected_results, start, None)
            is_iterator = True
        else:
            # There's no sort_field given. We still allow to reverse
            # and/or limit the resultset. This mimics zope.catalog's
            # searchResults semantics.
            if limit or start:
                selected_results = itertools.islice(
                    all_results, start, start + limit)
                is_iterator = True
            else:
                selected_results = all_results
            if reverse:
                selected_results = reversed(selected_results)
                is_iterator = True

        if is_iterator:
            selected_results = list(selected_results)

        return QueryResults(context, all_results, selected_results)


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

    def apply(self, context=None):
        results = []
        for term in self.terms:
            r = term.apply(context)
            if not r:
                # empty results
                return r
            results.append(r)

        if not results:
            return IFBTree()

        results.sort()

        result = results.pop(0)
        for r in results:
            _, result = weightedIntersection(result, r)
        return result


class Or(Term):

    def __init__(self, *terms):
        self.terms = terms

    def apply(self, context=None):
        results = []
        for term in self.terms:
            r = term.apply(context)
            # empty results
            if not r:
                continue
            results.append(r)

        if not results:
            return IFBTree()

        result = results.pop(0)
        for r in results:
            result = union(result, r)
        return result


class Difference(Term):

    def __init__(self, *terms):
        self.terms = terms

    def apply(self, context=None):
        results = []
        for term in self.terms:
            r = term.apply(context)
            # empty results
            if not r:
                continue
            results.append(r)

        if not results:
            return IFBTree()

        result = results.pop(0)
        for r in results:
            result = difference(result, r)
        return result


class Not(Term):

    def __init__(self, term):
        self.term = term

    def apply(self, context=None):
        return difference(self._all(), self.term.apply(context))

    def _all(self):
        # XXX may not work well/be efficient with extentcatalog
        # XXX not very efficient in general, better to use internal
        # IntIds datastructure but that would break abstraction..
        intids = getUtility(IIntIds)
        result = IFBTree()
        for uid in intids:
            result.insert(uid, 0)
        return result


class Objects(Term):

    def __init__(self, objects):
        self.objects = objects

    def apply(self, context=None):
        get_uid = getUtility(IIntIds, '', context).getId
        result = IFBTree()
        for uid in {get_uid(o) for o in self.objects}:
            result.insert(uid, 0)
        return result


class IndexTerm(Term):

    def __init__(self, (catalog_name, index_name)):
        self.catalog_name = catalog_name
        self.index_name = index_name

    def getIndex(self, context):
        catalog = getUtility(ICatalog, self.catalog_name, context)
        index = catalog[self.index_name]
        return index


class Text(IndexTerm):

    def __init__(self, index_id, text):
        super(Text, self).__init__(index_id)
        self.text = text

    def getIndex(self, context):
        index = super(Text, self).getIndex(context)
        assert ITextIndex.providedBy(index)
        return index

    def apply(self, context=None):
        index = self.getIndex(context)
        return index.apply(self.text)


class FieldTerm(IndexTerm):

    def getIndex(self, context):
        index = super(FieldTerm, self).getIndex(context)
        assert IFieldIndex.providedBy(index)
        return index


class Eq(FieldTerm):

    def __init__(self, index_id, value):
        assert value is not None
        super(Eq, self).__init__(index_id)
        self.value = value

    def apply(self, context=None):
        return self.getIndex(context).apply((self.value, self.value))


class NotEq(FieldTerm):

    def __init__(self, index_id, not_value):
        super(NotEq, self).__init__(index_id)
        self.not_value = not_value

    def apply(self, context=None):
        index = self.getIndex(context)
        all = index.apply((None, None))
        r = index.apply((self.not_value, self.not_value))
        return difference(all, r)


class All(FieldTerm):

    def apply(self, context=None):
        return self.getIndex(context).apply((None, None))


class Between(FieldTerm):

    def __init__(self, index_id, min_value, max_value):
        super(Between, self).__init__(index_id)
        self.min_value = min_value
        self.max_value = max_value

    def apply(self, context=None):
        return self.getIndex(context).apply((self.min_value, self.max_value))


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

    def apply(self, context=None):
        results = []
        index = self.getIndex(context)
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
