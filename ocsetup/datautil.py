#!/usr/bin/env python
# encoding=utf-8
#
# Copyright (C) 2012 Sunus Lee, CT
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301 USA
#
# Refer to the README and COPYING files for full details of the license
#
#!/usr/bin/env python
# encoding=utf-8

import os
from ovirtnode.ovirtfunctions import  network_up, aug, logical_to_physical_networks,\
                            augtool_get, logger,\
                            has_ip_address, get_ipv6_address, get_ip_address,\
                            nic_link_detected, pad_or_trim
from ovirtnode.network import get_system_nics
from ovirtnode.log import get_rsyslog_config
import gudev
import gtk

#TEMP VARS
OVIRT_VARS = {}


OVIRT_DEFAULTS = "/etc/default/ovirt"
get_hostname = lambda: os.uname()[1]
double_check = lambda i, attr:\
        hasattr(i, attr) and getattr(i, attr) is not None


def datas_refresh(oc_widgets):
    """
    refresh a page's all data
    """
    # some of the item don't create by _create_iteme which `certainly`
    # have attributes called ('get_conf', 'set_conf', 'show_conf', 'conf_path')
    # so we have to do use the double_check function here.
    for i in oc_widgets.values():
        if double_check(i, 'get_conf'):
            if double_check(i, 'conf_path'):
                v = i.get_conf(i.conf_path)
            else:
                v = i.get_conf()
            if v:
                if double_check(i, 'show_conf'):
                    i.show_conf(v)
                elif hasattr(i, 'set_label'):
                    i.set_label(v)
                    i.get_oc_value = i.get_label
                elif hasattr(i, 'set_text'):
                    i.set_text(v)
                    i.get_oc_value = i.get_text
                else:
                    print 'Need a Setter for', i


def conf_apply(apy_btn):
    print 'hello!'
    i = apy_btn
    while (isinstance(i.get_parent(), gtk.Notebook) and
            hasattr(i, 'oc_widgets')) == False:
        i = i.get_parent()
    oc_widgets = i.oc_widgets
    for widget in oc_widgets.values():
        if hasattr(widget, 'get_oc_value'):
            print 'Apply value:', widget.get_oc_value()
        if double_check(widget, 'set_conf'):
            if double_check(widget, 'conf_path'):
                widget.set_conf(widget.get_oc_value, widget.conf_path)
            else:
                widget.set_conf(widget.get_oc_value)


def data_read(path):
    pass


def data_write(path, key):
    pass


def read_status_datas():
    if network_up():
        network_status = {}
        status_text = []
        client = gudev.Client(['net'])
        # reload augeas tree
        aug.load()
        for nic in client.query_by_subsystem("net"):
            try:
                interface = nic.get_property("INTERFACE")
                logger.debug(interface)
                if not interface == "lo":
                    if has_ip_address(interface) or\
                    get_ipv6_address(interface):
                        ipv4_address = get_ip_address(interface)
                        try:
                            ipv6_address, netmask = get_ipv6_address(interface)
                        except:
                            ipv6_address = ""
                        network_status[interface] = (ipv4_address, ipv6_address)
            except:
                pass
        # remove parent/bridge duplicates
        for key in sorted(network_status.iterkeys()):
            if key.startswith("br"):
                parent_dev = key[+2:]
                if network_status.has_key(parent_dev):
                    del network_status[parent_dev]
        for key in sorted(network_status.iterkeys()):
            ipv4_addr, ipv6_addr = network_status[key]
            cmd = "/files/etc/sysconfig/network-scripts/" +\
            "ifcfg-%s/BOOTPROTO" % str(key)
            dev_bootproto = augtool_get(cmd)
            if dev_bootproto is None:
                cmd = "/files/etc/sysconfig/network-scripts/" +\
                "ifcfg-br%s/BOOTPROTO" % str(key)
                dev_bootproto = augtool_get(cmd)
                if dev_bootproto is None:
                    dev_bootproto = "Disabled"
            if not nic_link_detected(key):
                ipv4_addr = "(Link Inactive)"
            if ipv4_addr.strip() == "" and dev_bootproto.strip() == "dhcp":
                if "Inactive" in ipv4_addr:
                    ipv4_addr = "(Link Inactive)"
                else:
                    ipv4_addr = "(DHCP Failed)"
            if OVIRT_VARS.has_key("OVIRT_IPV6") and ipv6_addr != "":
                pass
            else:
                ipv6_addr = ""
            status_text.append([key.strip(), dev_bootproto.strip(),
                                ipv4_addr.strip(), ipv6_addr.strip()])
            logger.debug(status_text)
            logger.debug(network_status)
    else:
        status_text.append(["Not Connected", "", "", ""])
    return status_text


def read_logical_netwrok():
    networks = logical_to_physical_networks()
    net_entry = []
    for key in networks.iterkeys():
        device, mac = networks[key]
        key = pad_or_trim(12, key)
        device = pad_or_trim(8, device)
        net_entry.append([key, device, mac])
    return net_entry


def read_log_status():
    logging_status_text = ""
    if not get_rsyslog_config() is None:
        host, port = get_rsyslog_config()
        logging_status_text += "Rsyslog: %s:%s\n" % (host, port)
    netconsole_server = augtool_get("/files/etc/sysconfig/netconsole/" +
                                    "SYSLOGADDR")
    netconsole_server_port = augtool_get("/files/etc/sysconfig/" +
                                         "netconsole/SYSLOGPORT")
    if netconsole_server and netconsole_server_port:
        logging_status_text += "Netconsole: %s:%s" % (netconsole_server,
                                            netconsole_server_port)
    if len(logging_status_text) == 0:
        logging_status_text = "Local Only"
    return logging_status_text


def read_nics():
    nics = []
    nic_dict, configured_nics, ntp_dhcp = get_system_nics()
    for key in sorted(nic_dict.iterkeys()):
        (dev_interface, dev_bootproto, dev_vendor, dev_address,
        dev_driver, dev_conf_status, dev_bridge) = (
                nic_dict[key].split(",", 6))
        dev_vendor = pad_or_trim(10, dev_vendor)
        dev_interface = pad_or_trim(6, dev_interface)
        if len(dev_interface.strip()) == 0:
            continue
        else:
            nics.append([dev_interface, dev_conf_status,
                        dev_vendor, dev_address])
    return nics
