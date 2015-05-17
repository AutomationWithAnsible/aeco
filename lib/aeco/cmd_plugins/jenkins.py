"""
aeco jenkins

Usage:
  aeco jenkins status  [-v]
  aeco jenkins job name  [-v]
  aeco jenkins -h, --help

Options:
  -v, --verbose         Be more verbose.
  -h, --help            Show this screen and exit.
"""

import jenkinsapi
import jenkinsapi.jenkins
from docopt import docopt
from aeco_lib.utils import print_table, format_last_run, TColors
from aeco_lib.base import AecoBase


class Jenkins(AecoBase):
    def __init__(self, options=None):
        super(Jenkins, self).__init__(options=options, docs=__doc__)
        self.J = None

    def _connect(self):
        try:
            self.J = jenkinsapi.jenkins.Jenkins(self._get_config("jenkins_url"))
        except Exception, e:
            print "Jenkins connection Issue: '{}',  Error: '{}'".format(self.config["jenkins_url"], e.message)
            exit(1)

    def _jobs_status(self):
        self._connect()
        for job in self.J.keys():
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
                duration = format_last_run(build.get_duration(), color=False)
                # Color timestamp
                last_run = format_last_run(build.get_timestamp(), color=False)
            else:
                buildno = " - "
                status = " - "
                duration = " - "
                last_run = " - "
            # update results
            self.results.append([job, buildno, last_run, status, duration])
        # Print results
        headers = ["Name", "no", "Last Run", "Status", "Exec Time"]
        print_table(self.results, headers=headers)

    @staticmethod
    def print_help():
        print __doc__

    def parse(self):
        if self.arguments.get("status"):
            self._jobs_status()
        elif self.arguments.get("job"):
            print "Not yet"
        elif self.arguments.get("help"):
            self.print_help()