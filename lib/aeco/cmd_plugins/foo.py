
"""
aeco foo

Usage:
  aeco  foo bar   [-o=<opt>] [-f] [-v]
  aeco  foo test  [-f] [-v]
  aeco  foo -h, --help

Options:
  -o, --option=<opt>    Example of option argument
  -f, --flag            Example of flag argument
  -v, --verbose         Be more verbose.
  -h, --help            Show this screen and exit.
"""


from docopt import docopt
from aeco.utils.utils import print_table, format_last_run
from aeco.utils.base import AecoBase

class Foo(AecoBase):
    def __init__(self, options=None):
        super(Foo, self).__init__(options=options, docs=__doc__)

    def parse(self):
        print "___FOO Parse___"
        print self._get_config("option1")
