
"""
aeco ssh

Usage:
  aeco ssh [<argument>...]
  aeco ssh -h, --help

Options:
  -h, --help            Show this screen and exit.
"""


from docopt import docopt
from aeco.utils.utils import input_choice
from aeco.utils.base import AecoBase
import sys
import json
import os
import re

class Ssh(AecoBase):
    def __init__(self, options=None):
        super(Ssh, self).__init__(options=options, docs=__doc__)


    def _run_cmd(self, ip):
        cmd = "ssh %s %s" % (ip, " ".join(sys.argv[2:]))
        print "Running %s" % cmd
        os.system(cmd)
    def __get__(self):
        with open('/tmp/server.json') as data_file:
            servers = json.load(data_file)
        server_names = []
        for server, ips in servers.iteritems():
            server_names.append(server)

        ssh_hostname = input_choice("SSH Server", server_names, fmode=False)
        ips =  servers.get(ssh_hostname)

        if len(ips) == 1:
            self._run_cmd(ips[0])
        elif len(ips) > 1:
            matched_ip = False
            for ip in ips:
                if re.match(r'10.224.*.*', ip):
                    matched_ip = ip
                    break
            if not matched_ip:
                matched_ip = ips[0]
            self._run_cmd(matched_ip)
        else:
            print "No IP defined for this server"
            exit(1)

    def parse(self):
        self.__get__()

