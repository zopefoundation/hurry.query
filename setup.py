from setuptools import setup, find_packages

setup(
    name="hurry.query",
    version="0.9.4dev",
    packages=find_packages('src'),
    package_dir= {'':'src'},
    
    namespace_packages=['hurry'],
    package_data = {
    '': ['*.txt', '*.zcml'],
    },

    zip_safe=False,
    author='Infrae',
    author_email='faassen@startifact.com',
    description="""\
hurry.query is a higher level query system built on top of the Zope 3
catalog. It makes it easy to perform catalog queries in Zope 3 code.
""",
    license='ZPL 2.1',
    keywords="zope zope3",
    classifiers = ['Framework :: Zope3'],
    install_requires=[
    'zc.catalog >= 0.1.1',
    'setuptools'],
    )
