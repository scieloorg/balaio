#!/usr/bin/env python
import balaio
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


setup(
    name="balaio",
    version='.'.join(balaio.__version__),
    description="Utility to support the submission and validation of packages of articles to be included in collections of the SciELO.",
    author="SciELO",
    author_email="scielo-dev@googlegroups.com",
    license="BSD 2-clause",
    url="http://docs.scielo.org",
    packages=['balaio'],
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Customer Service",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Operating System :: POSIX :: Linux",
        "Topic :: System",
        "Topic :: Utilities",
    ],
    setup_requires=["nose>=1.0", "coverage"],
    tests_require=["mocker"],
    test_suite="nose.collector",
)
