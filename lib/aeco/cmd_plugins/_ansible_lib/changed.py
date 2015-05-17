import rethinkdb as r
from aeco_lib.utils import print_table, format_last_run, TColors, truncate_str
from common import CommonReDB


class AnsibleChanged(CommonReDB):
    db_name = "ansible"
    table_changed = "changed"
    supported_sort_changed = ['run', 'host', 'play', 'module']
    supported_filter_changed = ['tag', 'play', 'module', 'ignore', "user"]

    def __init__(self, bind, port, docs=__doc__, options=None):
        super(AnsibleChanged, self).__init__(bind, port, options=options, docs=docs)

    # Get changeds for a host or regexp hosts
    def _host_changed_query(self, hostname, limit, sort, order_func, filter_func, not_truncate):
        # Query
        query = r.db(self.db_name).table(self.table_changed)\
            .filter(r.row["host"].match("^" + str(hostname)) &
                    r.branch(bool(filter_func), filter_func, True))\
            .limit(int(limit))\
            .order_by(order_func(sort))

        if self.arguments.get("--verbose"):
            print "Rl > ", query

        cursor = query.run()

        # Loop through items and format them
        for document in cursor:
            self._format_changed_item(document, not_truncate)

    # Organize print
    def _format_changed_item(self, item, truncate):
        item["skip_tags"] = ",".join(item["skip_tags"])  # Flatten list
        # Tags color and flatten list
        if "all" in item["only_tags"]:
            item["only_tags"] = ",".join(item["only_tags"])
        else:
            item["only_tags"] = TColors.yellow(",".join(item["only_tags"]))
        # Color last
        last_run = format_last_run(item["@timestamp"], color=False)
        # Truncate
        changed_module_args_tr = truncate_str(item["changed_module_args"], truncate)
        changed_msg_tr = truncate_str(item["changed_msg"], truncate)
        # Update our results table with all values
        self.results.append([item["host"],
                             last_run,
                             item["play_name"],
                             item["user"],
                             item["only_tags"],
                             item["skip_tags"],
                             item["extra_vars"],
                             item["changed_module_name"],
                             changed_module_args_tr,
                             changed_msg_tr])

    def _print_results(self):
        question = "Q> Ansbile changeds | host(s) '{}' returned '{}' limit '{}' sort '{}' order '{}' filter '{}'"\
            .format(TColors.yellow(self.answers["host"]),
                    TColors.yellow(len(self.results)),
                    TColors.yellow(self.arguments.get("--rlimit")),
                    TColors.yellow(self.answers["sort"]),
                    TColors.yellow(self.answers["order"]),
                    TColors.yellow(self.answers["filter"]))

        headers = ["Host", "Last Run", "Play Name", "User", "+Tag", "-Tag", "vars", "Module", "Args", "Msg"]
        print_table(self.results, headers=headers, question=question)

    def parse(self):
        self._connect()
        reduction = False
        self._host_changed_query(self._hostname(),
                                 self.arguments.get("--rlimit"),
                                 self._sort(self.supported_sort_changed),
                                 self._order_func(),
                                 self._filter_func(self.supported_filter_changed, reduction),
                                 self.arguments.get("--not-truncate"))
        self._print_results()