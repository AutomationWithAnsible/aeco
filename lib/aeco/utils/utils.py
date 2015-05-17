import dateutil.parser
import dateutil.relativedelta
import logging
from datetime import datetime, timedelta
from tabulate import tabulate
import readline
import rlcompleter
import glob

__STR_TRUNC__ = 25
__DB_HOST__ = "ah-control000.yetudev.com"
__DB_PORT__ = "28015"
__DB_NAME__ = "ansible"
__T_SUMMARY__ = "summary"
__T_FAILURE__ = "failure"

class TColors:
    @staticmethod
    def header(text):
        return "{}{}{}".format('\033[95m', str(text), '\033[0m')

    @staticmethod
    def blue(text):
        return "{}{}{}".format('\033[94m', str(text), '\033[0m')

    @staticmethod
    def green(text):
        return "{}{}{}".format('\033[92m', str(text), '\033[0m')

    @staticmethod
    def yellow(text):
        return "{}{}{}".format('\033[33m', str(text), '\033[0m')

    @staticmethod
    def red(text):
        return "{}{}{}".format('\033[91m', str(text), '\033[0m')

    @staticmethod
    def warning(text):
        return "{}{}{}".format('\033[93m', str(text), '\033[0m')


def format_last_run(timestamp, red=24, yellow=12, color=True, show_only=2):
    if isinstance(timestamp, timedelta):
        rd = dateutil.relativedelta.relativedelta(seconds=int(timestamp.total_seconds()),
                                                  microseconds=timestamp.microseconds)
    else:
        if isinstance(timestamp, unicode):
            timestamp = dateutil.parser.parse(timestamp)
        timestamp = timestamp.replace(tzinfo=None)
        time_utc_now = datetime.utcnow()
        rd = dateutil.relativedelta.relativedelta(time_utc_now, timestamp)

    total_hours = 0
    last_run = []
    if rd.years > 0:
        last_run.append(str(rd.years) + " year")
        total_hours = 999999  # haaa
    if rd.months > 0:
        last_run.append(str(rd.months) + " month")
        total_hours = 999999  # haaa
    if rd.days > 0:
        last_run.append(str(rd.days) + " day")
        total_hours += (rd.days * 24)
    if rd.hours > 0:
        last_run.append(str(rd.hours) + " hr")
        total_hours += rd.hours
    if rd.minutes > 0:
        last_run.append(str(rd.minutes) + " min")
        total_hours += rd.minutes * 0.0166667
    if rd.seconds > 0:
        last_run.append(str(rd.seconds) + " sec")

    if show_only > len(last_run):
        show_only = len(last_run)

    last_run = ", ".join(last_run[:show_only])

    if total_hours >= red and color:
        last_run = TColors.red("{}".format(last_run))
    elif total_hours >= yellow and color:
        last_run = TColors.yellow("{}".format(last_run))
    return last_run


def print_table(results, headers=None, question=None, footer=None, table_format="simple"):
    # Question Section (if exists)
    if question:
        print question + "\n"
    # Table
    print tabulate(results, headers=headers, tablefmt=table_format)
    # Footer Section (if exists)
    if footer:
        print footer


def truncate_str(string, truncate):
    if not truncate and len(string) > __STR_TRUNC__:
        return string[:__STR_TRUNC__] + "..."
    else:
        return string

class tabCompleter(object):
    """
    A tab completer that can either complete from
    the filesystem or from a list.

    Partially taken from:
    http://stackoverflow.com/questions/5637124/tab-completion-in-pythons-raw-input
    """

    def pathCompleter(self,text,state):
        """
        This is the tab completer for systems paths.
        Only tested on *nix systems
        """
        line   = readline.get_line_buffer().split()

        return [x for x in glob.glob(text+'*')][state]


    def createListCompleter(self,ll):
        """
        This is a closure that creates a method that autocompletes from
        the given list.

        Since the autocomplete function can't be given a list to complete from
        a closure is used to create the listCompleter function with a list to complete
        from.
        """
        def listCompleter(text,state):
            line  = readline.get_line_buffer()
            if not line:
                return [c + " " for c in ll][state]
            else:
                return [c + " " for c in ll if c.startswith(line)][state]
        self.listCompleter = listCompleter


def input_choice(question, options=None, fmode=True):
    if 'libedit' in readline.__doc__:
        readline.parse_and_bind("bind '\t' rl_complete")
    else:
        readline.parse_and_bind("tab: complete")
        readline.set_completer_delims('\t')
    t = tabCompleter()
    t.createListCompleter(options)
    readline.set_completer(t.listCompleter)
    while 1:
        user_input = raw_input(question + ": ").strip()
        if fmode:
            break
        else:
            if user_input not in options:
                print "Invalid option use <tab> to see options"
            else:
                break
    return user_input