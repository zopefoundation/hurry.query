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
import logging
import os
import time

from BTrees.IFBTree import IFSet
from BTrees.IFBTree import weightedIntersection
from BTrees.IFBTree import multiunion, difference, intersection
from zope.cachedescriptors.property import Lazy
from zope.catalog.field import IFieldIndex
from zope.catalog.interfaces import ICatalog
from zope.catalog.text import ITextIndex
from zope.component import getUtility, getSiteManager, IComponentLookup
from zope.interface import implements
from zope.intid.interfaces import IIntIds
from zope.index.interfaces import IIndexSort
from zope.index.text.parsetree import ParseError
from hurry.query import interfaces

import transaction
import threading

logger = logging.getLogger('hurry.query')
HURRY_QUERY_TIMING = False
if 'HURRY_QUERY_TIMING' in os.environ:
    try:
        HURRY_QUERY_TIMING = float(os.environ['HURRY_QUERY_TIMING'])
    except (ValueError, TypeError):
        pass


class Cache(threading.local):
    implements(transaction.interfaces.IDataManager)

    def __init__(self, manager):
        self._manager = manager
        self.reset()

    def sortKey(self):
        return 'A' * 26

    def use(self, context):
        if not self._joined:
            self._joined = True
            transaction = self._manager.get()
            transaction.join(self)
        if context is not self._context:
            # The context changed, reset the cache as we might access
            # different indexes.
            self.cache = {}
            self._context = context
        return self.cache

    def tpc_begin(self, transaction):
        pass

    def tpc_vote(self, transaction):
        pass

    def tpc_finish(self, transaction):
        self.reset()

    def tpc_abort(self, transaction):
        self.reset()

    def abort(self, transaction):
        self.reset()

    def commit(self, transaction):
        pass

    def reset(self):
        self._joined = False
        self._context = None
        self.cache = {}


transaction_cache = Cache(transaction.manager)


class Results(object):
    implements(interfaces.IQuery)

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

    def first(self):
        for uid in self.__selected:
            return self.get(uid)

    def __len__(self):
        return len(self.__selected)

    def __iter__(self):
        for uid in self.__selected:
            yield self.get(uid)



class Timing(object):

    def __init__(self, key=None, order=0):
        self.key = key
        self.start = time.clock()
        self.start_order = order
        self.end = None
        self.end_order = None

    def done(self, order=0):
        self.end = time.clock()
        self.end_order = order

    @property
    def total(self):
        if self.end is not None:
            return self.end - self.start
        return None


class TimingAwareCache(object):

    def __init__(self, cache):
        self.cache = cache
        self.timing = {}
        self.count = 0
        self.post = None

    def start_post(self):
        self.post = Timing()

    def end_post(self):
        self.post.done()

    def __setitem__(self, key, value):
        self.cache[key] = value
        timing = self.timing.get(key)
        if timing is not None:
            timing.done(self.count)
            self.count += 1

    def get(self, key):
        value = self.cache.get(key)
        if value is None:
            self.timing[key] = Timing(key, self.count)
            self.count += 1
        return value

    def report(self, over=0):
        all_timing = sorted(self.timing.values(), key=lambda t: t.start_order)
        if not len(all_timing):
            return
        total_post = 0 if self.post is None else self.post.total
        total_terms = all_timing[0].total
        if (total_terms + total_post) < over:
            return
        indent = 0
        order = [all_timing[0].end_order]
        logger.info(
            'Catalog query toke {:.4f}s for terms, {:.4f}s to finish.'.format(
                total_terms, total_post))
        for timing in all_timing:
            if timing.start_order < order[-1]:
                indent += 4
                order.append(timing.end_order)
            logger.info(
                '{} {:.4f}s: {}.'.format(
                    ' ' * indent, timing.total, str(timing.key)))
            if timing.end_order > order[-1]:
                indent -= 4
                order.pop()


class Query(object):
    implements(interfaces.IQuery)

    def searchResults(
            self, query, context=None, sort_field=None, limit=None,
            reverse=False, start=0, caching=False, timing=HURRY_QUERY_TIMING):

        if context is None:
            context = getSiteManager()
        else:
            context = IComponentLookup(context)
        if caching:
            cache = transaction_cache.use(context)
        else:
            cache = {}

        timer = None
        if timing is not False:
            timer = cache = TimingAwareCache(cache)
        all_results = query.cached_apply(cache, context)
        if not all_results:
            if timer is not None:
                timer.report(over=timing)
            return Results(context, [], [])

        if timer is not None:
            timer.start_post()

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
            selected_results = all_results
            if reverse:
                selected_results = reversed(selected_results)
                is_iterator = True
            if limit or start:
                selected_results = itertools.islice(
                    selected_results, start, start + limit)
                is_iterator = True

        if is_iterator:
            selected_results = list(selected_results)

        if timer is not None:
            timer.end_post()
            timer.report(over=timing)

        return Results(context, all_results, selected_results)


class Term(object):
    implements(interfaces.ITerm)

    def key(self, context=None):
        raise NotImplementedError()

    def apply(self, cache, context=None):
        raise NotImplementedError()

    def cached_apply(self, cache, context=None):
        try:
            key = self.key(context)
        except NotImplementedError:
            return self.apply(cache, context)
        cached = cache.get(key)
        if cached is not None:
            return cached
        result = self.apply(cache, context)
        cache[key] = result
        return result

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

    def __init__(self, *terms, **kwargs):
        self.terms = terms
        self.weighted = kwargs.get('weigthed', False)

    def apply(self, cache, context=None):
        results = []
        for term in self.terms:
            result = term.cached_apply(cache, context)
            if not result:
                # Empty results
                return result
            results.append(result)

        if len(results) == 0:
            return IFSet()

        if len(results) == 1:
            return results[0]

        # Sort results to have the smallest set first to optimize the
        # set operation.
        results.sort(key=lambda r: len(r))

        result = results.pop(0)
        for r in results:
            if self.weighted:
                _, result = weightedIntersection(result, r)
            else:
                result = intersection(result, r)
            if not result:
                # Empty results
                return result

        return result

    def key(self, context=None):
        return ('and',) + tuple(term.key(context) for term in self.terms)


class Or(Term):

    def __init__(self, *terms):
        self.terms = terms

    def apply(self, cache, context=None):
        results = []
        for term in self.terms:
            result = term.cached_apply(cache, context)
            # empty results
            if not result:
                continue
            results.append(result)

        if len(results) == 0:
            return IFSet()
        if len(results) == 1:
            return results[0]

        return multiunion(results)

    def key(self, context=None):
        return ('or',) + tuple(term.key(context) for term in self.terms)


class Difference(Term):

    def __init__(self, *terms):
        self.terms = terms

    def apply(self, cache, context=None):
        results = []
        for index, term in enumerate(self.terms):
            result = term.cached_apply(cache, context)
            # If we do not have any results for the first index, just
            # return an empty set and stop here.
            if not result:
                if not index:
                    return IFSet()
                continue
            results.append(result)

        result = results.pop(0)
        for other in results:
            result = difference(result, other)
            if not result:
                # Empty results
                return result
        return result

    def key(self, context=None):
        return ('difference',) + tuple(
            term.key(context) for term in self.terms)


class Not(Term):
    # XXX This term will load all the intids of your application
    # resulting in major and heavy performance issues. It is advised
    # not to use it.

    def __init__(self, term):
        self.term = term

    def apply(self, cache, context=None):
        return difference(self._all(), self.term.cached_apply(cache, context))

    def _all(self):
        return IFSet(uid for uid in getUtility(IIntIds))

    def key(self, context=None):
        return ('not', self.term.key(context))


class Objects(Term):

    def __init__(self, objects):
        self.objects = objects
        self._ids = None

    def ids(self, context=None):
        if self._ids is None:
            get_uid = getUtility(IIntIds, '', context).getId
            self._ids = tuple(get_uid(o) for o in self.objects)
        return self._ids

    def apply(self, cache, context=None):
        return IFSet(self.ids(context))

    def key(self, context=None):
        return ('objects', self.ids(context))


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

    def apply(self, cache, context=None):
        index = self.getIndex(context)
        try:
            return index.apply(self.text)
        except ParseError:
            logger.error(
                'search text "{}" yielded a ParseError'.format(self.text))
            return IFSet()

    def key(self, context=None):
        return ('text', self.catalog_name, self.index_name, self.text)


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

    def apply(self, cache, context=None):
        return self.getIndex(context).apply((self.value, self.value))

    def key(self, context=None):
        return ('equal', self.catalog_name, self.index_name, self.value)


class NotEq(FieldTerm):

    def __init__(self, index_id, value):
        super(NotEq, self).__init__(index_id)
        self.value = value

    def apply(self, cache, context=None):
        index = self.getIndex(context)
        values = index.apply((None, None))
        matches = index.apply((self.value, self.value))
        return difference(values, matches)

    def key(self, context=None):
        return ('not equal', self.catalog_name, self.index_name, self.value)


class All(FieldTerm):

    def apply(self, cache, context=None):
        return self.getIndex(context).apply((None, None))

    def key(self, context=None):
        return ('all', self.catalog_name, self.index_name)


class Between(FieldTerm):

    def __init__(self, index_id,
                 minimum=None, maximum=None):
        super(Between, self).__init__(index_id)
        self.options = (minimum, maximum)

    def apply(self, cache, context=None):
        return self.getIndex(context).apply(self.options)

    def key(self, context=None):
        return ('between', self.catalog_name, self.index_name, self.options)


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
        self.values = tuple(values)

    def apply(self, cache, context=None):
        results = []
        index = self.getIndex(context)
        for value in self.values:
            r = index.apply((value, value))
            # empty results
            if not r:
                continue
            results.append(r)

        if len(results) == 0:
            return IFSet()
        if len(results) == 1:
            return results[0]

        return multiunion(results)

    def key(self, context=None):
        return ('in', self.catalog_name, self.index_name, self.values)
