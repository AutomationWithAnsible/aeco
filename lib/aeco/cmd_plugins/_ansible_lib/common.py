import rethinkdb as r
from aeco_lib.base import AecoBase


class CommonReDB(AecoBase):
    lookup_sort_field = {"run": "@timestamp", "play": "play_name", "ignore": "ignore_error", "args": "fail_module_args",
                         "host": "hosts", "module": "fail_module_name", "msg": "fail_msg", "tags": "only_tags",
                         "tag": "only_tags", "ok": "ok", "changed": "changed", "unreachable": "unreachable",
                         "failed": "failed", "user": "user"}

    lookup_filter_field = {"module": "match", "tag": "contains", "play": "match", "user": "match", "ignore": "bool"}

    def __init__(self, bind, port, options=None, docs=__doc__):
        super(CommonReDB, self).__init__(options=options, docs=docs)
        self.bind = bind
        self.port = port
        self.answers = dict()
        self.answers["filter"] = self.arguments.get("--filter")
        self.answers["sort"] = self.arguments.get("--sort")

    def _connect(self):
        try:
            r.connect(self.bind, self.port, timeout=5).repl()
        except Exception, e:
            print("rethinkdb connection Issue: ", e.message)
            exit(1)

    # Return dic with filter
    @staticmethod
    def _reduction_filter(item, reduction):
        if reduction:
            return item["reduction"]
        return item

    def _order_func(self):
        if self.arguments.get("--order") not in ["ascending", "asc", "a", "descending", "desc", "d"]:
            print "Warning unknown value '{}' ignoring and using ascending".format(self.arguments.get("--order"))
            order_func = getattr(r, "asc")
            self.answers["order"] = "Ascending"
        elif self.arguments.get("--order")[0].lower() == "a":
            order_func = getattr(r, "asc")
            self.answers["order"] = "Ascending"
        else:
            order_func = getattr(r, "desc")
            self.answers["order"] = "Descending"
        return order_func

    def _filter_func(self, supported_list, reduction=False):
        if not self.arguments.get("--filter"):
            return False
        filter_list = []

        for filter_by in self.arguments.get("--filter").split(","):
            if "=" in filter_by:
                key, value = filter_by.split("=")
                if len(value.strip()) == 0:
                    return False, "Error filter '{}' value cant be emtpy.".format(key)
                elif key in supported_list:
                    reql_match_func = self.lookup_filter_field.get(key)
                    field = self.lookup_sort_field.get(key)
                    if reql_match_func == "bool":
                        if value.lower() in ["true", "t", "yes", "1"]:
                            filter_list.append(self._reduction_filter(r.row, reduction)["ignore_error"] == True)
                        elif value.lower() in ["false", "f", "no", "0"]:
                            filter_list.append(self._reduction_filter(r.row, reduction)["ignore_error"] == False)
                        else:
                            print "Error filter '{}' requires boolean value got '{}'.".format(key, value)
                            exit(1)
                    else:
                        # Construct a reql function/query i.e. r.row[field].contains(value)
                        temp_func = getattr(r, "row")
                        temp_func = self._reduction_filter(temp_func, reduction)[field]
                        temp_func = getattr(temp_func, reql_match_func)
                        temp_func = temp_func(value)
                        filter_list.append(temp_func)
                else:
                    print "'{}' is not a supported filter. Supported filters {}"\
                        .format(key, supported_list)
                    exit(1)
            else:
                print "'{}' Filters are key=value syntax. Missing value".format(filter)
                exit(1)

        # TODO: CLEAN
        if len(filter_list) > 1:
            filter_func = None
            for func in filter_list:
                if filter_func:
                    filter_func = filter_func & func
                else:
                    filter_func = func
        elif len(filter_list) == 1:
            filter_func = filter_list[0]
        else:
            filter_func = False
        return filter_func

    def _hostname(self):
        if self.arguments.get("--limit"):
            self.answers["host"] = str(self.arguments.get("--limit"))
        else:
            self.answers["host"] = None
        return self.answers["host"]

    def _sort(self, supported_list):
        if not self.arguments.get("--sort") in supported_list:

            print "Sort argument only supports the following {}\n Got '{}'"\
                .format(supported_list, self.arguments.get("--sort"))
            exit(1)

        return self.lookup_sort_field.get(self.arguments.get("--sort"))

    def parse(self):
        raise NotImplementedError