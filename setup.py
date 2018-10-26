# -*- coding: utf-8 -*-
'''
Created on 12 gru 2015

@author: Arkadiusz Dzięgiel <arkadiusz.dziegiel@glorpen.pl>
'''

from setuptools import setup, find_packages
import re
import os
import sys

root_dir = os.path.realpath(os.path.dirname(__file__))
with open("%s/src/glorpen/di/__init__.py" % root_dir, "rt") as f:
    version = re.search(r'__version__\s*=\s*"([^"]+)"', f.read()).group(1)

with open("%s/README.rst" % root_dir, "rt") as f:
    long_description = f.read()

requires = ["funcsigs"] if sys.hexversion < 0x03030000 else []

setup (
  name = 'glorpen-di',
  version = version,
  packages = ['glorpen.di'],
  package_dir = {'': 'src'},
  install_requires = requires + ['six>=1.9'],
  dependency_links = [],
  namespace_packages  = ['glorpen'],
  author = 'Arkadiusz Dzięgiel',
  author_email = 'arkadiusz.dziegiel@glorpen.pl',
  description = 'Yet another Dependency Injection (IOC) component for Python',
  url = 'https://bitbucket.org/glorpen/glorpen-di',
  license = 'GPLv3',
  long_description= long_description,
  classifiers = [
    'Development Status :: 5 - Production/Stable',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.2',
    'Programming Language :: Python :: 3.3',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    'Topic :: Software Development :: Libraries',
  ],
  test_suite = "glorpen.di.tests.__init__",
  command_options = {
    "bdist_wheel": {
        "universal": ["setup.py", 1]
    }
  }
)
