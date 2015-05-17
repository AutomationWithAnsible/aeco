"""
aeco control

Usage:
  aeco  control status  [-v]
  aeco  control detail  <jobname> [-r=<int>] [-v]
  aeco  control console <jobname> [<buildnumber>]  [-v]
  aeco  control -h, --help

Options:
  -r, --rlimit=<int>    Record limit to retrieve [default: 20].
  -v, --verbose         Be more verbose.
  -h, --help            Show this screen and exit.
"""

import jenkinsapi
from jenkinsapi.jenkins import Jenkins
from docopt import docopt
from aeco_lib.utils import print_table, format_last_run, TColors
from aeco_lib.base import AecoBase


class Control(AecoBase):
    def __init__(self, options=None):
        super(Control, self).__init__(options=options, docs=__doc__)
        self.J = None

    def _connect(self):
        jenkins_url = self._get_config("jenkins_url")
        try:
            self.J = Jenkins(jenkins_url)
        except Exception, e:
            print "Jenkins connection Issue: '{}',  Error: '{}'".format(jenkins_url, e.message)
            exit(1)

    def _projects_status(self):
        self._connect()
        for job in self.J.keys():
            name = job.split("-")
            if len(name) != 2:
                print "Error Jenkins  job '{}' violates name SKIPPING JOB. Name example  'ansible-env-project_name.yml'"\
                    .format(name)
                return False
            # Check if this job has last build
            try:
                build = self.J[job].get_last_build()
            except jenkinsapi.custom_exceptions.NoBuildData:
                build = None

            if build:
                buildno = build.buildno
                # Status color
                status = build.get_status()
                if build.get_status() == "SUCCESS":
                    status = TColors.green(status)
                elif build.get_status() == "FAILURE":
                    status = TColors.red(status)
                else:
                    status = TColors.yellow(status)
                # Color duration
                duration = format_last_run(build.get_duration())
                # Color timestamp
                last_run = format_last_run(build.get_timestamp())
            else:
                buildno = " - "
                status = " - "
                duration = " - "
                last_run = " - "
            # update results
            self.results.append([name[0], name[1], buildno, last_run, status, duration])
        # Print results
        headers = ["ENV", "Name", "no",  "Last Run", "Status", "Exec Time"]
        print_table(self.results, headers=headers)

    def _projects_detail(self):
        self._connect()
        job_name = self.arguments.get("<jobname>")
        try:
            project = self.J[job_name]
        except jenkinsapi.custom_exceptions.UnknownJob:
            print "Error '" + TColors.red(job_name) + "' does not exist"
            exit(1)

        first_build = project.get_first_buildnumber()
        last_build = project.get_last_buildnumber()

        r_limit = self.arguments.get("--rlimit")
        if (last_build - first_build) > int(r_limit):
            first_build = last_build - int(r_limit)

        for buildno in range(first_build, last_build):
            try:
                build = project.get_build(buildno)
            except jenkinsapi.custom_exceptions.NoBuildData:
                build = None
            if build:
                # Status color
                status = build.get_status()
                if build.get_status() == "SUCCESS":
                    status = TColors.green(status)
                elif build.get_status() == "FAILURE":
                    status = TColors.red(status)
                if build:
                    status = TColors.yellow(status)
                    # Color duration
                    duration = format_last_run(build.get_duration())
                    # Color timestamp
                    last_run = format_last_run(build.get_timestamp(), color=False)
                    self.results.append([buildno, last_run, duration, status])
        # Print results
        headers = ["No.", "Last run", "Exec time", "Status"]
        print_table(self.results, headers=headers)

    def _projects_console(self):
        self._connect()
        job_name = self.arguments.get("<jobname>")
        buildnober = self.arguments.get("<buildnumber>")
        try:
            if buildnober is None:
                build = self.J[job_name].get_last_build()
            else:
                build = self.J[job_name].get_build(int(buildnober))
        except jenkinsapi.custom_exceptions.UnknownJob:
            print "Error '" + TColors.red(job_name) + "' does not exist"
            exit(1)
        except KeyError:
            print "Error unknown job build '" + TColors.red(buildnober) + " for '" + TColors.red(job_name)
            exit(1)
        else:
            print build.get_console()

    @staticmethod
    def print_help():
        print __doc__

    def parse(self):
        if self.arguments.get("status"):
            self._projects_status()
        elif self.arguments.get("console"):
            self._projects_console()
        elif self.arguments.get("detail"):
            self._projects_detail()
        elif self.arguments.get("help"):
            self.print_help()