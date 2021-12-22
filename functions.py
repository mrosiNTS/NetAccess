#!/usr/bin/env python3

import yaml
import sys
from netaddr import *
import pprint
from nornir_napalm.plugins.tasks import napalm_get      # requires pip3 install nornir_napalm
from nornir_utils.plugins.functions import print_result # requires pip3 install nornir_utils
from nornir_netmiko.tasks import netmiko_send_command   # requires pip3 install nornir_netmiko
from nornir_netmiko.tasks import netmiko_send_config   # requires pip3 install nornir_netmiko
from tqdm import tqdm # look here https://nornir.readthedocs.io/en/latest/howto/progress_bar.html for details

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

def collect_data(task, napalm_get_fact_bar, napalm_get_environment_bar):
    """
    This task takes two paramters that are in fact bars;
    napalm_get_bar and other_bar. When we want to tell
    to each respective bar that we are done and should update
    the progress we can do so with bar_name.update()
    """
    task.run(task=napalm_get, getters=["facts"])
    napalm_get_fact_bar.update()
    tqdm.write(f"{task.host}: facts items collected")

    # more actions go here
    task.run(task=napalm_get, getters=["environment"])
    napalm_get_environment_bar.update()
    tqdm.write(f"{task.host}: environment items collected!")

def time_bars(devices):
    # creation of real time bars named "napalm_get_fact_bar" & "napalm_get_environment_bar"
    with tqdm(
            total=len(devices.inventory.hosts), desc="gathering facts",
    ) as napalm_get_fact_bar:
        # we create the second bar named napalm_get_environment_bar
        with tqdm(
                total=len(devices.inventory.hosts), desc="gathering environment",
        ) as napalm_get_environment_bar:
            # we call our grouped task passing both bars
            output = devices.run(
                        task=collect_data,
                        napalm_get_fact_bar=napalm_get_fact_bar,
                        napalm_get_environment_bar=napalm_get_environment_bar,
            )
    outcome1 = output["Device1"][1]
    outcome2 = output["Device1"][2]

    print_result(outcome1)
    print_result(outcome2)

def collect_interfaces(devices):
    # get interfaces configurations
    output = devices.run(task=napalm_get, getters=["interfaces"])
    outcome = output["Device1"][0]
    print_result(outcome)
    pprint.pprint(outcome.result["interfaces"]["Management0"])

def OSPF_routing_table(devices):
    # get OSPF routing table from devices
    output = devices.run(task=netmiko_send_command, command_string="show ip route ospf-CORE | begin /32 next 4 | exclude /30")
    outcome = output["Device1"][0]
    print_result(outcome)

def new_L0_int_OSPF_metric (devices):
    # change metric OSPF to loopback interfaces
    output = devices.run(task=netmiko_send_config, config_commands=["interface loopback0", "ip ospf cost 1000"])
    outcome = output["Device1"][0]
    print_result(outcome)