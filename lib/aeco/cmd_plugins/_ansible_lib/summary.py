import sys
import os
import rethinkdb as r
from aeco_lib.utils import print_table, format_last_run, TColors
from common import CommonReDB


class AnsibleSummary(CommonReDB):
    db_name = "ansible"
    table_summary = "summary"
    supported_sort_summary = ['run', 'host', 'play', 'ok', 'changed', 'unreachable', 'failed', 'user']
    supported_filter_summary = ['tag', 'play', 'ignore', "user"]

    def __init__(self, bind, port, docs=__doc__, options=None):
        super(AnsibleSummary, self).__init__(bind, port, options=options, docs=docs)

    def summary_status_query(self, sort, order_func, filter_func):
        # TODO: Fix me should work before group also to avoid elimination by max
        query = r.db(self.db_name).table(self.table_summary)\
            .filter(r.row["host"]
                    .match("^" + self.answers["host"]) & r.branch(filter_func, filter_func, True))\
            .limit(int(self.arguments.get("--rlimit")))\
            .order_by(order_func(sort))

        if self.arguments.get("--verbose"):
            print "Rl > ", query
        cursor = query.run()

        for document in cursor:
            item = self._reduction_filter(document, False)
            self._format_summary_item(item)

    def _format_summary_item(self, item):
        # TODO: smart print of time

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
        last_run = format_last_run(item["@timestamp"], color=False)

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

    def _print_results(self):
        question = "Q> Ansible Summary status| host(s) '{}' returned '{}' sort '{}' order '{}' filter '{}'"\
            .format(TColors.yellow(self.answers["host"]),
                    TColors.yellow(len(self.results)),
                    TColors.yellow(self.answers["sort"]),
                    TColors.yellow(self.answers["order"]),
                    TColors.yellow(self.answers["filter"]))
        headers = ["Host", "Last Run", "Play Name", "Ok", "CH", "UR", "FL", "Time(s)", "+Tag", "-Tag", "User"]
        print_table(self.results, headers=headers, question=question)

    def parse(self):
        self._connect()
        self._hostname()
        self.summary_status_query(self._sort(self.supported_sort_summary),
                                  self._order_func(),
                                  self._filter_func(self.supported_filter_summary, False))

        self._print_results()