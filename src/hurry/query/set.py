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
"""Query terms for zc.catalog's SetIndex

$Id$
"""
from zc.catalog.interfaces import ISetIndex

from hurry.query import query


class SetTerm(query.IndexTerm):

    def getIndex(self, context):
        index = super(SetTerm, self).getIndex(context)
        assert ISetIndex.providedBy(index)
        return index


class All(SetTerm):

    def apply(self, cache, context=None):
        return self.getIndex(context).apply({'any': None})

    def key(self, context=None):
        return ('all', self.catalog_name, self.index_name)


class AnyOf(SetTerm):

    def __init__(self, index_id, values):
        super(AnyOf, self).__init__(index_id)
        self.values = tuple(values)

    def apply(self, cache, context=None):
        return self.getIndex(context).apply({'any_of': self.values})

    def key(self, context=None):
        return ('any of', self.catalog_name, self.index_name, self.values)


class AllOf(SetTerm):

    def __init__(self, index_id, values):
        super(AllOf, self).__init__(index_id)
        self.values = tuple(values)

    def apply(self, cache, context=None):
        return self.getIndex(context).apply({'all_of': self.values})

    def key(self, context=None):
        return ('all of', self.catalog_name, self.index_name, self.values)


class SetBetween(SetTerm):

    def __init__(self, index_id,
                 minimum=None, maximum=None,
                 include_minimum=False, include_maximum=False):
        super(SetBetween, self).__init__(index_id)
        self.options = (minimum, maximum, include_minimum, include_maximum)

    def apply(self, context=None):
        return self.getIndex(context).apply({'between': self.options})

    def key(self, context=None):
        return ('between', self.catalog_name, self.index_name, self.options)


class ExtentAny(SetTerm):
    """Any ids in the extent that are indexed by this index."""

    def __init__(self, index_id, extent):
        super(ExtentAny, self).__init__(index_id)
        self.extent = extent

    def apply(self, cache, context=None):
        return self.getIndex(context).apply({'any': self.extent})


class ExtentNone(SetTerm):
    """Any ids in the extent that are not indexed by this index."""

    def __init__(self, index_id, extent):
        super(None, self).__init__(index_id)
        self.extent = extent

    def apply(self, cache, context=None):
        return self.getIndex(context).apply({'none': self.extent})
