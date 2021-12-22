#!/usr/bin/env python3

import sys
import requests
from nornir import InitNornir

from functions import read_file
from functions import yaml_files_creation
from functions import collect_data
from functions import collect_interfaces
from functions import OSPF_routing_table
from functions import new_L0_int_OSPF_metric
from functions import time_bars

def main():

    requests.packages.urllib3.disable_warnings()

    #check if .yaml files must be created becasue first time that mgmt addresses are provided
    answer = input("Is the first time are you providing IP addresses of devices (y/n)? ")
    if answer.lower() == "y":
        # Setting of IP subnet and username/password
        mgmt_IP_add, login_username, login_password, enable_password = read_file()

        # Creation yaml files
        yaml_files_creation(number_devices, mgmt_IP_add, login_username, login_password)

    # use time bars for progressive tasks execution monitoring
    time_bars(nr)

    # collect interfaces configuration
    collect_interfaces(nr)

    # collect OSPF routing table
    OSPF_routing_table(nr)

    # change OSPF metric to loopback0 interface
    new_L0_int_OSPF_metric(nr)

if __name__ == '__main__':
    # the argv[] in input are the less significative byte of IP mgmt address; it's supposed
    # that all the devices have mgmt address on the same subnet

    number_devices = len(sys.argv) - 1

    if number_devices == 0:
        print('Last byte for at least one device has to be provided')
        sys.exit(1)

    main()
