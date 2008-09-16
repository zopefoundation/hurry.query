# Copyright (c) 2007 Infrae. All rights reserved.
# See also LICENSE.txt
from zc.catalog.interfaces import IValueIndex
from hurry.query import query

class ValueTerm(query.IndexTerm):
    def getIndex(self):
        index = super(ValueTerm, self).getIndex()
        assert IValueIndex.providedBy(index)
        return index

class Eq(ValueTerm):
    def __init__(self, index_id, value):
        assert value is not None
        super(Eq, self).__init__(index_id)
        self.value = value

    def apply(self):
        return self.getIndex().apply({'any_of': (self.value,)})

class NotEq(ValueTerm):
    def __init__(self, index_id, not_value):
        super(NotEq, self).__init__(index_id)
        self.not_value = not_value

    def apply(self):
        index = self.getIndex()
        values = list(index.values())
        values.remove(self.not_value)
        return index.apply({'any_of': values})

class Between(ValueTerm):
    def __init__(self, index_id, min_value=None, max_value=None,
                 exclude_min=False, exclude_max=False):
        super(Between, self).__init__(index_id)
        self.min_value = min_value
        self.max_value = max_value
        self.exclude_min = exclude_min
        self.exclude_max = exclude_max

    def apply(self):
        return self.getIndex().apply(
            {'between': (self.min_value, self.max_value,
                         self.exclude_min, self.exclude_max)})

class Ge(Between):
    def __init__(self, index_id, min_value):
        super(Ge, self).__init__(index_id, min_value=min_value)

class Le(Between):
    def __init__(self, index_id, max_value):
        super(Le, self).__init__(index_id, max_value=max_value)

class In(ValueTerm):
    def __init__(self, index_id, values):
        assert None not in values
        super(In, self).__init__(index_id)
        self.values = values

    def apply(self):
        return self.getIndex().apply({'any_of': self.values})

class ExtentAny(ValueTerm):
    """Any ids in the extent that are indexed by this index.
    """
    def __init__(self, index_id, extent):
        super(ExtentAny, self).__init__(index_id)
        self.extent = extent

    def apply(self):
        return self.getIndex().apply({'any': self.extent})

class ExtentNone(ValueTerm):
    """Any ids in the extent that are not indexed by this index.
    """
    def __init__(self, index_id, extent):
        super(ExtentNone, self).__init__(index_id)
        self.extent = extent

    def apply(self):
        return self.getIndex().apply({'none': self.extent})
