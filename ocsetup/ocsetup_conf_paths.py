#!/usr/bin/env python
# encoding=utf-8
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


OVIRT_DEFAULTS = "etc/default/ovirt"
# use augtool_get to read the configuration values.
DNS_SERVER1_PATH = "/files/etc/resolv.conf/nameserver[1]"
DNS_SERVER2_PATH = "/files/etc/resolv.conf/nameserver[2]"
NTP_SERVER1_PATH = "/files/etc/ntp.conf/server[1]"
NTP_SERVER2_PATH = "/files/etc/ntp.conf/server[2]"
NIC_IP_PATH = "/files/" + OVIRT_DEFAULTS + "/OVIRT_IP_ADDRESS"
NIC_NETMASK_PATH = "/files/" + OVIRT_DEFAULTS + "/OVIRT_IP_NETMASK"
NIC_GATEWAY_PATH = "/files/" + OVIRT_DEFAULTS + "/OVIRT_IP_GATEWAY"
NIC_VLAN_PATH = "/files/" + OVIRT_DEFAULTS + "/OVIRT_VLAN"
NIC_BOOTIF_PATH = "/files/" + OVIRT_DEFAULTS + "/OVIRT_BOOTIF"
ENABLE_SSH_PATH = "/files/etc/ssh/sshd_config/PasswordAuthentication"
