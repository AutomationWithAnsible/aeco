
"""
aeco ansible host checks

Usage:
  aeco ansible inventory [-i=<file>] [-s=<field>] [-o=<asc>] [-f=<str>] [-v]
  aeco ansible summary [-l=<host>] [-s=<field>] [-o=<asc>] [-f=<str>] [-r=<int>] [-t] [-v]
  aeco ansible changed [-l=<host>] [-s=<field>] [-o=<asc>] [-f=<str>] [-r=<int>] [-t] [-v]
  aeco ansible failure [-l=<host>] [-s=<field>] [-o=<asc>] [-f=<str>] [-r=<int>] [-t] [-v]
  aeco ansible -h | --help

Options:
  -v, --verbose         Be more verbose.
  -f, --filter=<str>    Filter question by fields.
  -s, --sort=<field>    Sort record by field options "run|host|play|ok|changed|unreachable|failed|module|user" [default: run].
  -l, --limit=<host>    Limit query to a specific host [default: *].
  -r, --rlimit=<int>    Record limit to retrieve [default: 10].
  -o, --order=<asc>     Order ascending 'asc' or descending 'desc' [default: asc].
  -i, --ifile=<file>    Inventory file, comma separated for multi file [default: ENV]
  -t, --not-truncate    Don't truncate messages more than 25 char.
  -h, --help            Show this screen and exit.
"""

# CONFIG TODO: MAKE in config file or env var
__RETHINDB_HOST__ = "ah-control000.yetudev.com"
__RETHINDB_PORT__ = 28015
#####


from _ansible_lib.failure import AnsibleFailure
from _ansible_lib.inventory import AnsibleInventory
from _ansible_lib.summary import AnsibleSummary
from _ansible_lib.changed import AnsibleChanged
from aeco_lib.base import AecoBase


class Ansible(AecoBase):
    def __init__(self, options=None):
        super(Ansible, self).__init__(options=options, docs=__doc__)

    @staticmethod
    def print_help():
        print __doc__

    def parse(self):
        rethinkdb_host = self._get_config("rethinkdb_host")
        rethinkdb_port = self._get_config("rethinkdb_port")

        if self.arguments.get("status"):
            print "status"
        elif self.arguments.get("help"):
            self.print_help()
        elif self.arguments.get("failure"):
            host_obj = AnsibleFailure(rethinkdb_host, rethinkdb_port, docs=__doc__)
            host_obj.parse()
        elif self.arguments.get("changed"):
            host_obj = AnsibleChanged(rethinkdb_host, rethinkdb_port, docs=__doc__)
            host_obj.parse()
        elif self.arguments.get("inventory"):
            host_obj = AnsibleInventory(rethinkdb_host, rethinkdb_port, docs=__doc__)
            host_obj.parse()
        elif self.arguments.get("summary"):
            host_obj = AnsibleSummary(rethinkdb_host, rethinkdb_port, docs=__doc__)
            host_obj.parse()