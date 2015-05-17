from docopt import docopt

class AecoBase(object):
    import os

    def __init__(self, options=None, docs=__doc__):
        if docs:
            self.arguments = docopt(docs)  # Command line arguments
        else:
            self.arguments = {}

        self.verbose = self.arguments.get("--verbose")  # Be more verbose

        self.results = []  # Store results for printing
        self.options = options
        self.config = dict()  # Parsed config options
        self._config_parse()

        if self.verbose:
            print "Config options = '{}'".format(self.config)
            print "args = {}".format(str(self.arguments)).replace("\n", "")

    def _config_parse(self):
        if hasattr(self.options, '__contains__'):  # Check if is iterable
            for item in self.options:
                try:
                    self.config[item[0]] = item[1]
                except IndexError:
                    pass

    def _get_config(self, value):
        if self.config.get(value):
            return self.config.get(value)
        else:
            # PLUGINNAME_VALUE
            env_value = self.__class__.__name__.upper() + "_" + value.upper()
            return self.os.getenv(env_value, False)

    @staticmethod
    def print_help():
        print __doc__

    def parse(self):
        raise NotImplementedError