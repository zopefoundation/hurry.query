# Copyright (c) 2007 Infrae. All rights reserved.
# See also LICENSE.txt
from zc.catalog.interfaces import ISetIndex
from hurry.query import query

class SetTerm(query.IndexTerm):
    def getIndex(self):
        index = super(SetTerm, self).getIndex()
        assert ISetIndex.providedBy(index)
        return index

class AnyOf(SetTerm):
    def __init__(self, index_id, values):
        super(AnyOf, self).__init__(index_id)
        self.values = values

    def apply(self):
        return self.getIndex().apply({'any_of': self.values})

class AllOf(SetTerm):
    def __init__(self, index_id, values):
        super(AllOf, self).__init__(index_id)
        self.values = values

    def apply(self):
        return self.getIndex().apply({'all_of': self.values})

class SetBetween(SetTerm):
    def __init__(self, index_id,
                 minimum=None, maximum=None,
                 include_minimum=False, include_maximum=False):
        super(SetBetween, self).__init__(index_id)
        self.tuple = (minimum, maximum, include_minimum, include_maximum)

    def apply(self):
        return self.getIndex().apply({'between': self.tuple})

class ExtentAny(SetTerm):
    """Any ids in the extent that are indexed by this index.
    """
    def __init__(self, index_id, extent):
        super(Any, self).__init__(index_id)
        self.extent = extent

    def apply(self):
        return self.getIndex().apply({'any': self.extent})

class ExtentNone(SetTerm):
    """Any ids in the extent that are not indexed by this index.
    """
    def __init__(self, extent):
        super(None, self).__init__(index_id)
        self.extent = extent

    def apply(self):
        return self.getIndex().apply({'none': self.extent})
