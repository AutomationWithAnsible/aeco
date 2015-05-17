"""
aeco elastic

Usage:
  aeco  elastic index list  [-v]
  aeco  elastic index delete  [-v]
  aeco  elastic -h, --help

Options:
  -v, --verbose         Be more verbose.
  -h, --help            Show this screen and exit.
"""

from docopt import docopt
import re
from aeco_lib.utils import print_table, format_last_run, TColors
from aeco_lib.base import AecoBase
try:
    from elasticsearch import Elasticsearch, client
except ImportError:
    elasticsearch_library_found = False
else:
    elasticsearch_library_found = True

#es_cluster = ["elastic000.yetudev.com:9200", "elastic001.yetudev.com:9200"]


class Elastic(AecoBase):
    def __init__(self, options=None):
        super(Elastic, self).__init__(options=options, docs=__doc__)
        if not elasticsearch_library_found:
            print "Cant import elasticsearch python library. use pip install elasticsearch"
            exit(1)

        if not self._get_config("cluster"):
            print "You must defined a ealstic cluster in your aeco config . i.e. cluster = server1:9200, server2:9200"
            exit(1)
        else:
            self.es_cluster = [x.strip() for x in self._get_config("cluster").split(',')]

        self.es = None
        self.indices = None

    def _connect(self):
        try:
            self.es = Elasticsearch(self.es_cluster, timeout=5)
        except Exception, e:
            print "Failed to initialized elasticSearch server '%s'. Exception = %s " % (self.es_cluster, e)
            exit(1)
        try:
            return self.es.ping()
        except Exception, e:
            print "Failed to get ping from elasticSearch server '%s'. Exception = %s " % (self.db_server, e)
            exit(1)

    def _get_all_indecies(self):
        self.client_indices = client.IndicesClient(self.es.indices)
        self.indices = self.client_indices.get_aliases()

    def _list_index(self):
        self._get_all_indecies()
        i = 1
        for index in self.indices:
            print str(i) + "\t" + index
            i += 1

    def _delete_index(self):
        try:
            user_input = raw_input("Are you sure you want to delete the above indices. " + TColors.red("NO UNDO") +  " (yes/no): ")
            if user_input != "yes":
                print "you said no bye!!"
                exit(1)
            print "Starting deleting"
            self.client_indices.delete(self.to_be_deleted)
            print "Finished deleting"
        except Exception, e:
            print e

        if isinstance(self.indices,list ):
            print "bulk"
        else:
            print "1 entry"

    def _delete_index_by_day(self, retain_days=7, confirm=True):
        self._get_all_indecies()

        # Match any pattern with "somethingYYYY.MM.DD
        pattern = ".(\d{4}\.\d{2}\.\d{2})$"
        notpattern = "([A-Za-z\-\_]+)"
        match_indcies = dict()
        for index in self.indices:
            match = re.findall(pattern, index)
            if match:
                index_name = re.findall(notpattern, index)[0]
                if not match_indcies.get(index_name):
                    match_indcies.update({index_name: []})
                match_indcies[index_name].append(index)
            else:
                print TColors.red(" ? Index name '%s' does not mach date pattern. Ignoring" % index)

        to_be_deleted = []
        for index_name in match_indcies:
            new_list = sorted(match_indcies.get(index_name))
            index_len = len(new_list)
            if index_len > retain_days:
                print "%s, Count: %d, to be delete: %s" % (index_name, index_len, TColors.yellow(index_len-retain_days))
                for delete_index in new_list[0:index_len-retain_days]:
                    print " > X ", TColors.yellow(delete_index)
                    to_be_deleted.append(delete_index)

        if len(to_be_deleted) > 0:
            self.to_be_deleted = ",".join(to_be_deleted)
            self._delete_index()
        else:
            print "Nothing to be deleted"



    @staticmethod
    def print_help():
        print __doc__

    def parse(self):
        if self.arguments.get("index"):
            if self.arguments.get("list"):
                self._connect()
                self._list_index()
            elif self.arguments.get("delete"):
                self._connect()
                self._delete_index_by_day()
        elif self.arguments.get("help"):
            self.print_help()