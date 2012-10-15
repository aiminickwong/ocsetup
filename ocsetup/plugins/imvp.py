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

import os
import sys
import traceback

from ovirtnode.ovirtfunctions import ovirt_store_config, \
    is_valid_host_or_ip, \
    is_valid_port, \
    PluginBase, \
    log, \
    network_up, \
    password_check, \
    augtool, \
    is_console, \
    system
from ovirtnode.password import set_password
from ovirtnode.license_utils import hasRegistered, hasStarted, hasDeprecated

from ocsetup.ocsetup_ui import WidgetBase, EMPTY_LINE, _
from ocsetup.ocsetup_ui_widgets import ButtonList, ConfirmDialog
from ocsetup.wrapper_ovirtfunctions import PluginBase

import subprocess

sys.path.append('/usr/share/vdsm-reg')
import deployUtil

sys.path.append('/usr/share/vdsm')
from vdsm import constants
import httplib
import socket


VDSM_CONFIG = "/etc/vdsm/vdsm.conf"
VDSM_REG_CONFIG = "/etc/vdsm-reg/vdsm-reg.conf"
VDC_HOST_PORT = 443
TIMEOUT_FIND_HOST_SEC = 5

fWriteConfig = 0


def set_defaults():
    vdsm_config_file = open(VDSM_CONFIG, "w")
    vdsm_config = """[vars]
trust_store_path = /etc/pki/vdsm/
ssl = true

[addresses]
management_port = 54321
"""
    vdsm_config_file.write(vdsm_config)
    vdsm_config_file.close()


def compatiblePort(portNumber):
    """
    Until the version 3.0, oVirt Engine provided port 8443/8080 to oVirt Node
    download cert and others files. Since 3.1 the default port changed to
    443/80. This function, will return the compatible port in case the VDSM
    cannot communicate with oVirt Engine.

    :param portNumber: port which doesn't communicate with oVirt Engine
    :returns: compatible port number (or None if there is no compatible port)
          and if it's SSL port or not (bool)
    """

    compatPort = {
        '443': ('8443', True),
        '8443': ('443', True),
        '80': ('8080', False),
        '8080': ('80', False)
    }

    return compatPort.get(portNumber, (None, False))


def isHostReachable(
        host,
        port=None,
        ssl=True,
        timeout=socket._GLOBAL_DEFAULT_TIMEOUT):
    """
    This function will try a http connection to a host with determined
    port, ssl and timeout.

    :param host: Host to be tested
    :param port: Which port httplib should use for the test connection
    :param ssl: if it's ssl port or not (bool)
    :param timeout: timeout for the operation, if not speficied the default
                will be socket._GLOBAL_DEFAULT_TIMEOUT
    :returns True or False
    """
    if ssl:
        Connection = httplib.HTTPSConnection
    else:
        Connection = httplib.HTTPConnection

    try:
        conn = Connection(host, port=port, timeout=timeout)
        conn.request('HEAD', '/')
        return True
    except socket.error:
        return False


def write_vdsm_config(engineHost, enginePort):
    if not os.path.exists(VDSM_CONFIG):
        system("touch " + VDSM_CONFIG)
    if os.path.getsize(VDSM_CONFIG) == 0:
        set_defaults()
        ovirt_store_config(VDSM_CONFIG)
        log("@ENGINENAME@ agent configuration files created.")
    else:
        log("@ENGINENAME@ agent configuration files already exist.")

    if system("ping -c 1 " + engineHost):
        sed_cmd = "sed -i --copy \"s/\(^vdc_host_name=\)\(..*$\)/vdc_host_name\
                =" + engineHost + "/\" " + VDSM_REG_CONFIG
        if system(sed_cmd):
            log("The @ENGINENAME@'s address is set: %s\n" % engineHost)
        if enginePort != "":
            sed_cmd = "sed -i --copy \"s/\(^vdc_host_port=\)\(..*$\)/vdc\
                _host_port=" + str(enginePort) + "/\" " + VDSM_REG_CONFIG
            if system(sed_cmd):
                log("The @ENGINENAME@'s port set: %s\n" % enginePort)
            fWriteConfig = 1
    else:
        log("Either " + engineHost + " is an invalid address \
            or the IMVP unresponsive.\n")
        return False

    if fWriteConfig == 1:
        log("Saving vdsm-reg.conf\n")
        if ovirt_store_config(VDSM_REG_CONFIG):
            log("vdsm-reg.conf Saved\n")
            return True


def getEngineConfig():
    vdsm_config = open(VDSM_REG_CONFIG)
    config = {}
    config["vdc_host_port"] = VDC_HOST_PORT
    for line in vdsm_config:
        line = line.strip().replace(" ", "").split("=")
        if "vdc_host_name" in line:
            item, config["vdc_host_name"] = line[0], line[1]
        if "vdc_host_port" in line:
            item, config["vdc_host_port"] = line[0], line[1]
    vdc_server = config["vdc_host_name"] + ":" + config["vdc_host_port"]
    vdsm_config.close()
    return vdc_server


def getEngineInformation(engine_type):
    try:
        vds_server = getEngineConfig()
        engine_address, engine_port = vds_server.split(":")
        if engine_address.startswith("None"):
            engine_address = ""
    except:
        log("Warning: failed to parse engine config. %s " %
            traceback.format_exc())
        engine_address = ""
        engine_port = "8080"
    if engine_type == "address":
        return engine_address
    elif engine_type == "port":
        return engine_port
    return None


class Plugin(PluginBase):
    def __init__(self):
        PluginBase.__init__(self, "IMVP")
        self.registered = None
        self.started = None
        self.deprecated = None
        self.is_network_up = None

    def _getHeaderInfo(self):
        self.registered = hasRegistered()
        self.started = hasStarted()
        self.deprecated = hasDeprecated()
        self.is_network_up = network_up()
        if self.is_network_up:
            header_message = "IMVP Configuration"
            if self.started and not self.registered:
                header_message += " (Network Up, but Not Registered)"
        else:
            header_message = "Network Down, IMVP Configuration Disabled"
        return header_message

    def imvp_apply(self, obj):
        from ocsetup.ocsetup import ocs
        log("enter imvp apply")
        imvp_server_address = \
            ocs.page_imvp.imvp_server_addr_val_Entry.get_text()
        imvp_server_port = \
            ocs.page_imvp.imvp_serve_port_val_Entry.get_text()
        compatPort, sslPort = compatiblePort(imvp_server_port)
        if len(imvp_server_address) > 0:
            deployUtil.nodeCleanup()
            if not (
                isHostReachable(
                    host=imvp_server_address,
                    port=imvp_server_port,
                    ssl=sslPort,
                    timeout=TIMEOUT_FIND_HOST_SEC)):
                if compatPort is None:
                    # Try one more time with SSL=False
                    if not (
                        isHostReachable(
                            host=imvp_server_address,
                            port=imvp_server_port,
                            ssl=False,
                            timeout=TIMEOUT_FIND_HOST_SEC)):
                        msgConn = "Can't connect to IMVP in the specific" + \
                            " port %s" % imvp_server_port

                        resp_id = \
                            ConfirmDialog(message=msgConn).run_and_close()
                        return False
                else:
                    msgConn = "Can't connect to IMVP port %s," + \
                        " trying compatible port %s" % \
                        (imvp_server_port, compatPort)

                    resp_id = ConfirmDialog(message=msgConn).run_and_close()

                    if not (
                        isHostReachable(
                            host=imvp_server_address,
                            port=compatPort, ssl=sslPort,
                            timeout=TIMEOUT_FIND_HOST_SEC)):
                        msgConn = "Can't connect to IMVP using" + \
                            " compatible port %s" % compatPort
                        resp_id = \
                            ConfirmDialog(message=msgConn).run_and_close()
                        return False
                    else:
                        # compatible port found
                        imvp_server_port = compatPort

            if True:
                if (
                    deployUtil.getRhevmCert(
                        imvp_server_address,
                        imvp_server_port, False)):
                    path, dontCare = deployUtil.certPaths('')
                    fp = deployUtil.generateFingerPrint(path)
                    ovirt_store_config(path)
                else:
                    msgConn = "Failed downloading IMVP certificate"
                    resp_id = ConfirmDialog(message=msgConn).run_and_close()
            # Stopping vdsm-reg may fail but its ok -
            # its in the case when the menus are run after installation
            deployUtil._logExec([constants.EXT_SERVICE, 'vdsm-reg', 'stop'])
            if write_vdsm_config(imvp_server_address, imvp_server_port):
                deployUtil._logExec([
                    constants.EXT_SERVICE, 'vdsm-reg',
                    'start'])
                msgConn = "IMVP Configuration Successfully Updated"
                resp_id = ConfirmDialog(message=msgConn).run_and_close()
                retWriteConf = True
            else:
                msgConn = "IMVP Configuration Failed"
                resp_id = ConfirmDialog(message=msgConn).run_and_close()
                retWriteConf = False

            return retWriteConf

    def imvp_reset(self, obj):
        log("enter imvp reset")
        refresh_window(obj)

    def form(self):
        title = WidgetBase(
            'imvp_title', 'Label', "",
            get_conf=self._getHeaderInfo, title=True)
        management_server_addr = WidgetBase('imvp_server_addr', 'Label',
                                            _('Management Server'))
        management_server_addr_val = WidgetBase(
            'imvp_server_addr_val',
            'Entry', '', '',
            get_conf=getEngineInformation, get_conf_args=('address',))
        management_server_port = WidgetBase('imvp_serve_port', 'Label',
                                            _('Management Server Port'))
        management_server_port_val = WidgetBase(
            'imvp_serve_port_val',
            'Entry', '', '',
            get_conf=getEngineInformation, get_conf_args=('port',))
        connect_to_imvp = WidgetBase(
            'connect_to_imvp', 'CheckButton',
            _('Connect to IMVP Manager and Validate Certificate'))
        set_pw = WidgetBase(
            'set_imvp_pw', 'Label',
            _('Set IMVP Admin Password'),
            title=True)
        imvp_pw = WidgetBase('imvp_pw', 'Label', 'Password')
        imvp_pwe = WidgetBase('imvp_pw', 'Entry')
        imvp_cpw = WidgetBase('imvp_cpw', 'Label', 'Confirm Password')
        imvp_cpwe = WidgetBase('imvp_cpw', 'Entry')
        imvp_changes = WidgetBase(
            'imvp_changes', ButtonList, '',
            params={'labels': [_('Apply'), _('Reset')],
            'callback': [self.imvp_apply, self.imvp_reset]})
        return [
            'imvp',
            'IMVP',
            [
                (title,),
                (management_server_addr, management_server_addr_val),
                (management_server_port, management_server_port_val),
                (connect_to_imvp,),
                (set_pw,),
                (imvp_pw, imvp_pwe),
                (imvp_cpw, imvp_cpwe),
                (WidgetBase('__', 'Label', vhelp=140),),
                (imvp_changes,),
            ]]

    def action(self):
        pass


def get_plugin():
    p = Plugin()
    return p.form()
