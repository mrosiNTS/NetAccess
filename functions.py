#!/usr/bin/env python3

import yaml
import sys
from netaddr import *
from nornir_napalm.plugins.tasks import napalm_get      # requires pip3 install nornir_napalm
from nornir_utils.plugins.functions import print_result # requires pip3 install nornir_utils
from nornir_netmiko.tasks import netmiko_send_command   # requires pip3 install nornir_netmiko
from nornir_netmiko.tasks import netmiko_send_config   # requires pip3 install nornir_netmiko

def read_file():
    # Reading config.yaml file

    with open("entry_config.yaml", "r") as file:
        try:
            config = yaml.safe_load(file)
        except Exception as err:
            print('missing yml file or wrong name')
            sys.exit()

    mgmt_IP_add = config["IP_add_subnet"]  # just the subnet is assigned and not the prefix
    login_username = config["username"]
    login_password = config["password"]
    enable_password = config["enapassword"]

    return mgmt_IP_add, login_username, login_password, enable_password


def yaml_files_creation(num_devices, mgmt_IP, login_user, login_passw):
    # dictionaries creation to be user for the ssh access to devices
    arg_count = 1
    hosts = {}
    groups = {}
    defaults = {}

    while arg_count < (num_devices + 1):
        last_byte = int(sys.argv[arg_count])
        prefix = IPNetwork(mgmt_IP)
        add = str(prefix.network + last_byte)
        hosts.update({'Device' + str(arg_count): {'hostname': add, 'groups': ['nxos']}})
        arg_count += 1

    # group.yaml file updating
    groups.update({'nxos': {'platform': 'nxos_ssh'}})

    # defaults.yaml file updating
    defaults.update({'username': login_user})
    defaults.update({'password': login_passw})
    defaults.update({'connection_options': {
                                      'napalm': {
                                          'extras': {
                                              'optional_args': {
                                                  'secret': 'cisco'}}}}})

    # create hosts, groups and defaults yaml files

    with open(r'./inventory/hosts.yaml', 'w') as file:
        file.write('---\n')
        hosts = yaml.dump(hosts, file)

    with open(r'./inventory/groups.yaml', 'w') as file:
        file.write('---\n')
        groups = yaml.dump(groups, file)

    with open(r'./inventory/defaults.yaml', 'w') as file:
        file.write('---\n')
        defaults = yaml.dump(defaults, file)

def collect_interfaces(devices):
    # get interfaces configurations
    output = devices.run(task=napalm_get, getters=["interfaces"])
    outcome = output["Device1"][0]

    print(outcome.result["interfaces"]["Management0"])

def OSPF_routing_table(devices):
    # get OSPF routing table from devices
    output = devices.run(task=netmiko_send_command, command_string="show ip route ospf-CORE | begin /32 next 4 | exclude /30")
    outcome = output["Device1"][0]
    print_result(output)

def new_L0_int_OSPF_metric (devices):
    # change metric OSPF to loopback interfaces
    output = devices.run(task=netmiko_send_config, config_commands=["interface loopback0", "ip ospf cost 1000"])
    outcome = output["Device1"][0]
    print_result(output)