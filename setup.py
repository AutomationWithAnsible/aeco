#!/usr/bin/env python

import os
import sys
from glob import glob

sys.path.insert(0, os.path.abspath('lib'))
from aeco import __version__, __author__
try:
    from setuptools import setup, find_packages
except ImportError:
    print("aeco now needs setuptools in order to build. Install it using"
          " your package manager (usually python-setuptools) or via pip (pip"
          " install setuptools).")
    sys.exit(1)

setup(name='aeco',
      version=__version__,
      description='apphome ecosystem tools',
      author=__author__,
      url='http://github.com/ahelal/',
      license='MIT',

      install_requires=['jenkinsapi', 'docopt', "python-dateutil", 'simplejson', 'tabulate', "rethinkdb" ],
      package_dir={'': 'lib'},
      packages=find_packages('lib'),
      package_data={},
      scripts=['bin/aeco'],
      data_files=[],
)