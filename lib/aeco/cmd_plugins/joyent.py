# Requirements
#   1- Python:
#      - smartdc
#      - simplejson
#   2- Ansible: Needs to be installed system wide with python
# Configuration:
# - keyname or bash env JOYENT_KEYNAME
# - username or bash env JOYENT_USERNAME
# - api or bash env JOYENT_API
# - id_rsa or bash env JOYENT_ID_RSA
# - _ansible_lib or bash env JOYENT_ANSIBLE_LIB


"""
aeco joyent

Usage:
  aeco joyent server list [-v]
  aeco joyent server delete <servername>
  aeco joyent server create
  aeco joyent server start <servername>
  aeco joyent server stop <servername>
  aeco joyent network list
  aeco joyent update
  aeco joyent -h | --help

Options:
  -h, --help            Show this screen and exit.
"""

from docopt import docopt
from smartdc import DataCenter
from aeco.utils.utils import print_table, format_last_run, TColors, input_choice
from aeco.utils.base import AecoBase
import ansible.runner
from ansible import inventory

import os
import json


class Joyent(AecoBase):
    def __init__(self, options=None):
        super(Joyent, self).__init__(options=options, docs=__doc__)
        self.machines = []
        self.sdc = None
        
        self.key_name = self._get_config("keyname")
        self.user_name = self._get_config("username")
        self.location = self._get_config("api")
        self.id_rsa = self._get_config("id_rsa")
        
        if self.user_name == False:
            print "Joyent username is not set"
            exit(1)
        if self.key_name == False:
            print "id_rsa is not set"
            exit(1)
        if self.id_rsa == False:
            print "id_rsa is not set"
            exit(1)
        
        self.key_id = "/" + self.user_name + "/keys/" + self.key_name

    def _connect(self):
        try:
            self.sdc = DataCenter(location=self.location,
                                  key_id=self.key_id, secret=self.id_rsa,
                                  allow_agent=True, verbose=self.verbose)

        except Exception as e:
            print self.location, self.key_id, self.id_rsa
            print "Failed to login: %s" % e
            exit(1)

    def _machine_format(self, m):
        if m.state == "running":
            m.state = TColors.green(m.state)
        elif m.state == "stopped":
            m.state = TColors.red(m.state)
        else:
            m.state = TColors.yellow(m.state)
        m.created = format_last_run(m.created, color=False)
        m.dataset = str(m.dataset).split(":")
        self.results.append([m.name,
                             m.state,
                             "",
                             ", ".join(m.ips),
                             m.type[0].upper(),
                             ":".join(m.dataset[-2:]),
                             m.created])

    def _network_format(self, network):
        if network["public"] == True:
            network["public"] = TColors.green("Public")
        else:
            network["public"] = TColors.red("Private")
        if "description" not in network:
            network["description"] = ""
        self.results.append([network["public"],
                             network["name"],
                             network["id"],
                             network["description"]])

    def _list_server(self):
        try:
            self.machines = self.sdc.machines()
        except Exception as e:
            print "Unable to search for server: %s" % str(e)
            exit(1)
        for machine in self.machines:
            self._machine_format(machine)

        # Print results
        headers = ["Name", "State", "ID", "IPs", "Type", "DataSet", "Created"]
        question = "List joyent Machines in {}".format(TColors.yellow(self.location))
        print_table(self.results, headers=headers, question=question)

    def joyent_runner(self, machine_name, api, state, package=None, networks=None, image=None):
        print ".....\nPlease wait doing API request to {}".format(api)

        module_arg = {"name": machine_name, "state": state, "data_center": api}
        if state == "present":
            module_arg.update({"networks": networks, "flavor": package, "image": image, "fire_forget": "false"})
        inventory_manager = inventory.Inventory("127.0.0.1,")
        # construct the ansible runner and execute on all hosts
        results = ansible.runner.Runner(
            pattern='*',
            forks=1,
            inventory=inventory_manager,
            transport="local",
            module_name='joyent',
            module_path=self._get_config("ansible_lib"),
            module_args=module_arg
        ).run()
        for (hostname, result) in results['contacted'].items():
            if 'failed' in result:
                print "Failed \n%s" % result['msg']
            elif 'failed' not in result:
                if result.get("msg"):
                    msg = TColors.red(result.get("msg"))
                    if result.get("changed"):
                        if result.get("ips"):
                            msg += " IPs=" + ", ".join(result.get("ips"))
                        print msg
                    else:
                        print result.get("msg")
                    print result.get("timer")
                else:
                    print "Output format not correct dumping all:\n%s", result

    @staticmethod
    def _load_list(json_file, fields=None, return_id=False):
        if os.path.isfile(json_file):
            if fields is None:
                fields = ["name"]
            # Warn if over two weeks old
            json_data = open(json_file)
            data_list = json.load(json_data)
            name_list = map(lambda x: ":".join([x.get(field) for field in fields]), data_list)
                #name_list = map(lambda x: x.get(fields), json.load(json_data))
            if return_id:
                id_list = map(lambda x: x.get("id"), data_list)
                return name_list, id_list
            else:
                return name_list
        else:
            return None

    def _create_server(self):
        path_to_json_file = os.path.dirname(os.path.realpath(__file__)) + "/joyent"
        machine_name = input_choice("Machine name", fmode=True)
        api = input_choice("API Server", ["us-east-1", "us-west-1", "us-sw-1", "eu-ams-1", "us-east-2", "us-east-3"],
                           fmode=False)

        package_list = self._load_list(path_to_json_file + "/{}.package.json".format(api))
        package = input_choice("Package", options=package_list, fmode=True)

        image_list, image_id = self._load_list(path_to_json_file + "/{}.images.json".format(api),
                                               fields=["name", "version"], return_id=True)
        image = input_choice("Image", options=image_list, fmode=True)
        if image in image_list:
            image_ref = "alias=" + image
            image = image_id[image_list.index(image)]
        else:
            image_ref = ""

        network_list, network_id = self._load_list(path_to_json_file + "/{}.networks.json".format(api), return_id=True)
        networks_ref,  networks = [], []
        new_input = input_choice("Network", options=network_list, fmode=False)
        while not new_input == "d":
            if new_input in network_list:
                networks_ref.append(new_input)
                networks.append(network_id[network_list.index(new_input)])

            new_input = input_choice("Network ('d' for done)", options=network_list, fmode=True)
            if new_input == "d":
                break

        networks = ",".join(networks)
        networks_ref = "alias=" + ",".join(networks_ref)
        print "You want to provision the following:"
        print "{0:15}: {1:30}".format("DC", TColors.warning(api))
        print "{0:15}: {1:30}".format("Machine Name", TColors.warning(machine_name))
        print "{0:15}: {1:30}".format("Package", TColors.warning(package))
        print "{0:15}: {1:30} {2:30}".format("Image", TColors.warning(image), image_ref)
        print "{0:15}: {1:30} {2:30}".format("Networks", TColors.warning(networks), networks_ref)
        answer = input_choice("Are you (yes/no)", ["yes", "no"], fmode=False)
        if answer == "yes":
            self.joyent_runner(machine_name, api, "present", package=package, image=image, networks=networks)
        else:
            print "bye..."

    def _update_db(self):
        try:
            self.machines = self.sdc.machines()
        except Exception as e:
            print "Unable to search for server: %s" % str(e)
            exit(1)

        for machine in self.machines:
            self._machine_format(machine)

        # Print results
        server_list = {}
        for server in self.results:
            server_list.update({server[0]: server[3].split(",")})

        with open('/tmp/server.json', 'w') as outfile:
            json.dump(server_list, outfile)

    def _delete_server(self):
        machine_name = self.arguments.get("<servername>")
        api = self._get_config("api")
        print "Are you sure you want to delete '" + TColors.red(machine_name) + "' in '" + TColors.red(api) + "'?"
        user_input = raw_input("If you are sure please type the server name again: ")
        if user_input != machine_name:
            print "Server names don't match. bye!!"
            exit(1)

        self.joyent_runner(machine_name, api, "absent")
        print "if you run on mac os OS X Mavericks, Mountain Lion, and Lion, you can reset your dns cache with:"
        print "\tsudo killall -HUP mDNSResponder"
        print "if you run mac os OS X Yosemite you can reset your dns cache with:"
        print "\tsudo discoveryutil mdnsflushcache"

    def _stop_server(self):
        machine_name = self.arguments.get("<servername>")
        api = self._get_config("api")
        print "Are you sure you want to stop '" + TColors.red(machine_name) + "' in '" + TColors.red(api) + "'?"
        user_input = raw_input("If you are sure please type the server name again: ")
        if user_input != machine_name:
            print "Server names don't match. bye!!"
            exit(1)
        self.joyent_runner(machine_name, api, "stopped")

    def _start_server(self):
        machine_name = self.arguments.get("<servername>")
        api = self._get_config("api")
        print "Are you sure you want to start '" + TColors.red(machine_name) + "' in '" + TColors.red(api) + "'?"
        user_input = raw_input("If you are sure please type the server name again: ")
        if user_input != machine_name:
            print "Server names don't match. bye!!"
            exit(1)
        self.joyent_runner(machine_name, api, "running")

    def _network_list(self):
        networks = []
        try:
            networks = self.sdc.networks()
        except Exception as e:
            print "Unable to search for networks: %s" % str(e)
            exit(1)
        for network in networks:
            self._network_format(network)
        
        headers = ["Public", "Name", "Id","Description"]
        question = "List of joyent networks in {}".format(TColors.yellow(self.location))
        print_table(self.results, headers=headers, question=question)
        exit(1)

    @staticmethod
    def print_help():
        print __doc__

    def parse(self):
        if self.arguments.get("server"):
            if self.arguments.get("list"):
                self._connect()
                self._list_server()
            elif self.arguments.get("delete"):
                self._delete_server()
            elif self.arguments.get("create"):
                self._create_server()
            elif self.arguments.get("stop"):
                self._stop_server()
            elif self.arguments.get("start"):
                self._start_server()
        elif self.arguments.get("network"):
            if self.arguments.get("list"):
                self._connect()
                self._network_list()
        elif self.arguments.get("update"):
            self._connect()
            self._update_db()
