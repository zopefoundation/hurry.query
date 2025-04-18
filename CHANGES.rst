CHANGES
=======

5.1 (unreleased)
----------------

- Simplify usage of PEP-420 namespace.


5.0 (2025-02-12)
----------------

- Drop support for ``pkg_resources`` namespace and replace it with PEP 420
  native namespace.

- Add support for Python 3.12, 3.13.

- Drop support for Python 3.7, 3.8.

4.0 (2023-05-04)
----------------

- Drop support for Python 2.7, 3.5, 3.6.

- Add support for Python 3.9, 3.10, 3.11.


3.2 (2020-11-16)
----------------

- Add support for Python 3.7.

- Add support for Python 3.8.

- Drop support for Python 3.4.

- Replace `time.clock` with `time.perf_counter` and fix deprecation warnings.

3.1 (2018-08-08)
----------------

- Add ``Ids`` term that include already known intids in a query.

3.0.0 (2018-01-19)
------------------

- Support for python 3.4, 3.5 and 3.6 in addition to python 2.7

- Cleanup in preparation for python3 support:

  Bugfixes:

  - API change: fix And(weighted=) keyword argument typo

  - API change: remove utterly broken ``include_minimum`` and ``include_maximum``
    arguments to SetBetween(), provide ``exclude_min`` and ``exclude_max`` instead.

  - API change: fix broken SetBetween.apply(): introduce ``cache`` arg

  - Fix ExtentNone() super delegation bug

  - Fix TimingAwareCaching.report() edge condition bug

  Major:

  - Remove unsupported transaction_cache

  Minor:

  - Clarify HURRY_QUERY_TIMING environment and searchResults(timing=) type

  - Fix TimingAwareCaching.report() output typo

  - Clarify Query.searchResults(caching=) argument type

  - Remove unreachable code path from And()

  Dev:

  - Maximize test coverage

  - Add Travis and Tox testing configurations

  - Bypass bootstrap.py

  - Various python3 compatibility preparations


2.6 (2018-01-10)
----------------

- Update dependencies not to rely on ZODB3 anymore.

2.5 (2017-07-17)
----------------

- `sort_field` can be a index name or an object providing `IIndexSort` itself.

- `searchResults()` accepts optional parameter `locate_to` and `wrapper`. The
  `locate_to` is used as the `__parent__` for the location proxy put arround
  the resulting objects. The `wrapper` is a callable callback that should
  accept one argument for its parameter.

2.4 (2017-06-22)
----------------

- Don't throw a TypeError slicing unsorted results, fixes #6

2.3 (2017-04-26)
----------------

- Define a "no result" result object, useful for case where application code
  has an custom API for building query terms, but this application code
  decides there is no query. Callers might still expect a result-like
  object.

2.2 (2017-04-26)
----------------

- The caching option to searchResults now accepts a dict-like value and it
  will use that to allow for caching results over multiple searchResults()
  calls. The cache invalidation then is the responsibility of the caller.

2.1 (2017-02-07)
----------------

- Add the possibility to time how long a query takes. It can be
  controlled with the new ``timing`` option to ``searchResults`` or
  the ``HURRY_QUERY_TIMING`` environment variable.

2.0.1 (2016-09-08)
------------------

- Fix log line in Text term for invalid text search.

2.0 (2016-09-07)
----------------

- Add new term: Difference. It does a difference between the first and
  the following terms passed as arguments.

- Add new term: Objects. It creates a result out of the objects passed
  in arguments. It let you mix real objects with existing catalog
  queries (with And, Or or Difference for instance).

- Add an option start to searchResult to skip the first results in the
  results set.

- Extend the result from searchResult. You have addition information
  on the result, including the total number of results without
  start/limit restriction. A method called first() return only the
  first result if available or none.

- Add an option caching to searchResult to cache the result of each
  terms within a Zope transaction, speeding similar queries. If
  disabled, terms will still be cached within the same query.


1.2 (2015-12-16)
----------------

* Add support for an All query.

1.1.1 (2012-06-22)
------------------

* ExtentNone in set.py missed a parameter ``index_id``. Thanks to Danilo
  Botelho for the bug report.

1.1.0 (2010-07-12)
------------------

* Allow the searchResults method of a Query to take an additional keyword
  argument `sort_field` that defines that defines (catalog_name, index_name) to
  sort on. That index in that catalog should implement IIndexSort.

  In addition to this keyword argument, `limit` and `reverse` keyword arguments
  can be passed too, that will limit the sorted resultset and/or reverse its
  order.

* Allow the searchResults method of a Query object to take an additional
  optional context argument. This context will determine which catalog
  the search is performed on.

1.0.0 (2009-11-30)
------------------

* Refresh dependencies. Use zope.catalog and zope.intid instead of
  zope.app.catalog and zope.app.intid respectively. Don't zope.app.zapi.

* Make package description more modern.

* Clean up the code style.

0.9.3 (2008-09-29)
------------------

* BUG: NotEq query no longer fails when all values in the index
  satisfy the NotEq condition.

0.9.2 (2006-09-22)
------------------

* First release on the cheeseshop.

0.9.1 (2006-06-16)
------------------

* Make zc.catalog a dependency of hurry.query.

0.9 (2006-05-16)
----------------

* Separate hurry.query from the other hurry packages. Eggification work.

* Support for ValueIndex from zc.catalog.

0.8 (2006-05-01)
----------------

Initial public release.
