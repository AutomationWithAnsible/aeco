"""
aeco version

Usage:
  aeco version
  aeco version all
  aeco version -h | --help

Options:
  -h, --help            Show this screen and exit.
"""

from docopt import docopt
from aeco.utils import info
from aeco.utils.base import AecoBase


class Version(AecoBase):
    def __init__(self, options=None):
        super(Version, self).__init__(options=options, docs=__doc__)

    @staticmethod
    def print_short():
        print info.__desc__ + " " + info.__version__

    @staticmethod
    def print_long():
        print info.__desc__ + " " + info.__version__
        print "Author(s): {}\n".format(info.__author__)
        print "Contributor(s): {}\n".format(info.__contrib__)

    @staticmethod
    def print_help():
        print __doc__

    def parse(self):
        if self.arguments.get("all"):
            self.print_long()
        elif self.arguments.get("help"):
            self.print_help()
        else:
            self.print_short()
