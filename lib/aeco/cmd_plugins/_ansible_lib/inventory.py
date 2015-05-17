import sys
import os
import subprocess
import rethinkdb as r
from aeco_lib.utils import print_table, format_last_run, TColors
from common import CommonReDB


class AnsibleInventory(CommonReDB):
    db_name = "ansible"
    table_summary = "summary"
    supported_sort_summary = ['run', 'host', 'play', 'ok', 'changed', 'unreachable', 'failed', 'user']
    supported_filter_summary = ['tag', 'play', 'ignore', "user"]  # ToDO Check what works

    def __init__(self, bind, port, docs=__doc__, options=None):
        super(AnsibleInventory, self).__init__(bind, port, options=options, docs=docs)
        self.inventory_hosts = []
        self.inventory_files = ""

    def inventory_status_query(self, sort, order_func, filter_func):
        # TODO: Fix me should work before group also to avoid elimination by max
        query = r.db(self.db_name).table(self.table_summary)\
            .order_by("@timestamp")\
            .filter(r.branch(bool(filter_func), filter_func, True))\
            .group("host")\
            .max("@timestamp").ungroup()\
            .order_by(order_func(r.row['reduction'][sort]))

        if self.arguments.get("--verbose"):
            print "Rl > ", query
        cursor = query.run()

        for document in cursor:
            item = self._reduction_filter(document, True)
            self._format_summary_item(item)

    def _format_summary_item(self, item):
        # TODO: smart print of time
        # Status Flag
        if len(self.inventory_hosts) > 1 and (self.answers["filter"] is None or self.answers["filter"] == "tag=all"):
            try:
                pop_host = self.inventory_hosts.index(item["host"])
                self.inventory_hosts.pop(pop_host)
                item["host"] = "* " + item["host"]
            except:
                item["host"] = "? " + item["host"]

        # Tags color
        if "all" in item["only_tags"]:
            item["only_tags"] = ",".join(item["only_tags"])
        else:
            item["only_tags"] = TColors.yellow(",".join(item["only_tags"]))

        item["skip_tags"] = ",".join(item["skip_tags"])
        # Color recap
        if item["ok"] > 0:
            item["ok"] = TColors.green(item["ok"])
        if item["failures"] > 0:
            item["failures"] = TColors.red(item["failures"])
        if item["changed"] > 0:
            item["changed"] = TColors.yellow(item["changed"])
        if item["unreachable"] > 0:
            item["unreachable"] = TColors.red(item["unreachable"])
        if item["failures"] > 0 or item["unreachable"] > 0:
            item["host"] = TColors.red(item["host"])
        elif item["changed"] > 0:
            item["host"] = TColors.yellow(item["host"])
        else:
            item["host"] = TColors.green(item["host"])
        # Color last run
        last_run = format_last_run(item["@timestamp"])

        self.results.append([item["host"],
                             last_run, item["play_name"],
                             item["ok"],
                             item["changed"],
                             item["unreachable"],
                             item["failures"],
                             item["time"],
                             item["only_tags"],
                             item["skip_tags"],
                             item["user"]])

    def _parse_ansible_inventory(self):
        inv_files = self.arguments.get("--ifile")
        if inv_files == "ENV":
            inv_files = os.getenv("AECO_INI")
            if not inv_files:
                print " Error: Inventory variable not set AECO_INI"
                exit(1)

        for inv_file in inv_files.split(","):
            sp = subprocess.Popen(["ansible", "-i", inv_file, "--list-hosts", "all"],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            hosts, err = sp.communicate()
            if not sp.returncode == 0:
                print "Warning error in getting inventory got: {}".format(err)
                exit(1)
            self.inventory_files += os.path.basename(inv_file) + " " # TODO: FIX WITH JOIN
            self.inventory_hosts += hosts.replace(" ", "").split("\n")

    def _print_results(self):
        question = "Q> Ansible inventory status| host(s) '{}' returned '{}' sort '{}' order '{}' filter '{}'"\
            .format(TColors.yellow(self.inventory_files),
                    TColors.yellow(len(self.results)),
                    TColors.yellow(self.answers["sort"]),
                    TColors.yellow(self.answers["order"]),
                    TColors.yellow(self.answers["filter"]))

        headers = ["Host", "Last Run", "Play Name", "Ok", "CH", "UR", "FL", "Time(s)", "+Tag", "-Tag", "User"]
        footer = ""
        for host_run in self.inventory_hosts:
            if len(host_run) > 0:  # make sure list is not ""
                footer += TColors.blue("r " + host_run) + "\n"
        print_table(self.results, headers=headers, question=question, footer=footer)

    def parse(self):
        self._connect()
        self._parse_ansible_inventory()
        self.inventory_status_query(self._sort(self.supported_sort_summary), self._order_func(),
                                    self._filter_func(self.supported_filter_summary, False))

        self._print_results()