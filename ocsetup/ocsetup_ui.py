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


import gtk
import sys
from ocsetup_ui_widgets import ButtonList, DetailedList,\
                               ConfirmDialog, ApplyResetBtn, RadioButtonList
from ovirtnode.ovirtfunctions import system_closefds, augtool_get,\
                                augtool, nic_link_detected
from wrapper_ovirtfunctions import exec_extra_buttons_cmds
import gettext
import datautil
from ovirtnode.network import Network
from ocsetup_conf_paths import *
sys.path.append('..')
gettext.bindtextdomain('ocsetup', '/usr/share/locale/')
gettext.textdomain('ocsetup')
_ = gettext.gettext


class WidgetBase(dict):

    def __init__(self, name, itype, label='', value='', **kwargs):
        super(WidgetBase, self).__init__(self)
        self.__setitem__('type', itype)
        self.__setitem__('name', name)
        self.__setitem__('label', label)
        self.__setitem__('value', value)
        for key in ('title', 'get_conf', 'get_conf_args',
                    'set_conf', 'set_conf_args',
                    'show_conf', 'conf_path',
                    'params', 'vhelp', 'width'):
            v = kwargs.get(key, None)
            self.__setitem__(key, v)

EMPTY_LINE = WidgetBase('empty', 'Label', '')


def load_pic(filename, w, h):
    pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(filename, w, h)
    image = gtk.Image()
    image.set_from_pixbuf(pixbuf)
    return image




class OcLayout(list):

    def __init__(self, name, tab_string):
        super(OcLayout, self).__init__()
        self.append(name)
        self.append(tab_string)


class OcStatus(OcLayout):

    def __init__(self):
        super(OcStatus, self).__init__('status', _('Status'))

    def confirm_cmd(self, obj):
        warn_message = "Warn %s" % obj.get_label()
        resp_id = ConfirmDialog(message=warn_message).run_and_close()
        if resp_id == gtk.RESPONSE_OK:
            cmd = ('_'.join(obj.get_label().split())).lower()
            system_closefds(exec_extra_buttons_cmds[cmd])

    def get_layout(self):
        networking_status = WidgetBase('networking_status', 'Label',
                                    _('Network Status'), title=True)
        networking_list = WidgetBase('status_network_list', DetailedList, '',
                params={'labels':
                [_('Device'), _('Bootproto'), _('IPV4 Address'), _('IPV6 Address')]},
                get_conf=datautil.read_status_datas)
        logical_network = WidgetBase('logical_network', DetailedList, '',
                params={'labels':
                [_('Logical Network'), _('Device'), _('MAC Address')]},
                get_conf=datautil.read_logical_netwrok)
        status_log_label = WidgetBase('status_log', 'Label', _('Log'),
                title=True)
        status_log_value = WidgetBase('status_log_val', 'Label',
                get_conf=datautil.read_log_status)
        status_buttons = WidgetBase('status_buttons', ButtonList, '',
                params={'labels':
                [_('Log Off'), _('Lock'), _('Restart'), _('Power Off')],
                'callback':
                [self.confirm_cmd, self.confirm_cmd, self.confirm_cmd, self.confirm_cmd]})
        self.append([
                    (networking_status,),
                    (networking_list,),
                    (logical_network,),
                    (EMPTY_LINE,),
                    (EMPTY_LINE,),
                    (status_log_label,),
                    (status_log_value,),
                    (status_buttons,),
                    ])
        return self


class OcLogging(OcLayout):

    def __init__(self):
        super(OcLogging, self).__init__('logging', _('Logging'))

    def get_layout(self):
        logging = WidgetBase('logging', 'Label', _('Logging'),
                title=True)
        log_max_size_label = WidgetBase('log_max_size_label', 'Label',
                _('Logrotate Max Log Size (KB):'))
        log_max_size_value = WidgetBase('log_max_size_value', 'Entry', '', '1024')
        log_rsys = WidgetBase('rsys', 'Label',
                _('Rsyslog is an enhanced multi-threaded syslog'),
                title=True)
        log_server_address = WidgetBase('log_server_address', 'Label', _('Server Address:'))
        log_server_address_val = WidgetBase('log_server_address_value', 'Entry', '')
        log_server_server_port = WidgetBase('log_server_server_port', 'Label', _('Server Port:'))
        log_server_server_port_val = WidgetBase('log_server_server_port', 'Entry', '', '514')
        changes_log = WidgetBase('log_apply_reset', ApplyResetBtn)
        self.append([
                    (logging,),
                    (log_max_size_label, log_max_size_value),
                    (log_rsys,),
                    (log_server_address, log_server_address_val),
                    (log_server_server_port, log_server_server_port_val,),
                    (WidgetBase('empty', 'Label', '', vhelp=200),),
                    (changes_log,),
                    ]
                    )
        return self

class OcNetwork(OcLayout):

    def __init__(self):
        super(OcNetwork, self).__init__('network', _('Network'))

    def get_layout(self):
        System_Identification = WidgetBase('system_identification', 'Label',
                                         _('System Identification'),
                title=True)
        Hostname_label = WidgetBase('hostname', 'Label', _('Hostname'))
        Hostname_value = WidgetBase('hostname', 'Entry', '', _(''),
                get_conf=datautil.get_hostname)

        DNS_SERVER1_label = WidgetBase('dns_server1', 'Label', _('DNS Server1:'))
        DNS_SERVER1_value = WidgetBase('dns_server1', 'Entry',
                        get_conf=augtool_get, conf_path=DNS_SERVER1_PATH,
                        set_conf=datautil.augtool_set)
        DNS_SERVER2_label = WidgetBase('dns_server2', 'Label', _('DNS Server2:'))
        DNS_SERVER2_value = WidgetBase('dns_server2', 'Entry',
                        get_conf=augtool_get, conf_path=DNS_SERVER2_PATH,
                        set_conf=datautil.augtool_set)
        NTP_SERVER1_label = WidgetBase('ntp_server1', 'Label', _('NTP Server1:'))
        NTP_SERVER1_value = WidgetBase('ntp_server1', 'Entry',
                        get_conf=augtool_get, conf_path=NTP_SERVER1_PATH,
                        set_conf=datautil.augtool_set)
        NTP_SERVER2_label = WidgetBase('ntp_server2', 'Label', _('NTP Server2:'))
        NTP_SERVER2_value = WidgetBase('ntp_server2', 'Entry',
                        get_conf=augtool_get, conf_path=NTP_SERVER2_PATH,
                        set_conf=datautil.augtool_set)

        # need to do some hack to import and run the codes
        # from ocsetup_ui_widgets.
        def show_networkdetail_cb(obj, path, row):
            from ocsetup_ui_widgets import NetworkDetailWindows
            network_detail_win = NetworkDetailWindows(obj, path, row)
            network_page = network_detail_win.page_network_detail
            network_page.ipv4_address_Entry.set_property("editable", False)
            network_page.ipv4_netmask_Entry.set_property("editable", False)
            network_page.ipv4_gateway_Entry.set_property("editable", False)
            network_page.ipv4_address_Entry.set_text("Field is disabled")
            network_page.ipv4_netmask_Entry.set_text("Field is disabled")
            network_page.ipv4_gateway_Entry.set_text("Field is disabled")

            def static_cb(btn, page):
                state = page.ipv4_address_Entry.get_property('editable')
                page.ipv4_address_Entry.set_text("Field is disabled" if state else '')
                page.ipv4_netmask_Entry.set_text("Field is disabled" if state else '')
                page.ipv4_gateway_Entry.set_text("Field is disabled" if state else '')
                page.ipv4_address_Entry.set_property("editable", not state)
                page.ipv4_netmask_Entry.set_property("editable", not state)
                page.ipv4_gateway_Entry.set_property("editable", not state)

            network_page.ipv4_settings_custom.btns[1].connect("toggled", static_cb, network_page)


        NETWORK_LIST = WidgetBase('network_network_list', DetailedList, '',
                params={'labels': [_('Device'), _('Status'), _('Model'),
                        _('MAC Address')],
                        'callback': show_networkdetail_cb},
                get_conf=lambda : datautil.read_nics(datautil.filter_rn_get_list))
        changes_network = WidgetBase('network_apply_reset', ApplyResetBtn)
        self.append([
                    (System_Identification, ),
                    (Hostname_label,Hostname_value,),
                    (DNS_SERVER1_label, DNS_SERVER1_value),
                    (DNS_SERVER2_label, DNS_SERVER2_value),
                    (EMPTY_LINE,),
                    (NTP_SERVER1_label, NTP_SERVER1_value),
                    (NTP_SERVER2_label, NTP_SERVER2_value),
                    (EMPTY_LINE,),
                    (NETWORK_LIST,),
                    (changes_network,),
                    ])
        return self


class NetworkDetail(OcLayout):

    def __init__(self, treeview_datas):
        super(NetworkDetail, self).__init__('network_detail', 'invisible_tab')
        ifname = treeview_datas[0]
        dev_interface, dev_bootproto, dev_vendor, dev_address,\
        dev_driver, dev_conf_status, dev_bridge = datautil.read_nics(lambda allinfos: allinfos[0][ifname].split(','))
        if nic_link_detected(ifname):
            link_status = "Active"
        else:
            link_status = "Inactive"
        network_detail_if = WidgetBase('interface', 'Label', '',
                get_conf = lambda : _("Interface: ") + dev_interface)
        network_detail_driver = WidgetBase('driver', 'Label', '',
                get_conf = lambda : _("Driver: ") + dev_driver)
        network_detail_proto = WidgetBase('protocol', 'Label', '',
                get_conf = lambda : _('Protocol: ') + dev_bootproto)
        network_detail_vendor = WidgetBase('vendor', 'Label', '',
                get_conf = lambda : _('Vendor: ') + dev_vendor)
        network_detail_link_status = WidgetBase('link_status', 'Label', '',
                get_conf = lambda : _('Link Status: ') + link_status)
        network_detail_mac_address = WidgetBase('mac_address', 'Label', '',
                get_conf = lambda : _('Mac Address: ') + dev_address)
        network_detail_ipv4_setting_label = WidgetBase('ipv4_setting', 'Label', _('IPV4 Settings:'))
        network_detail_ipv4_settings = WidgetBase('ipv4_settings', RadioButtonList, '',
                params={'labels': ['Disable', 'Static'], 'type': 'CheckButton'})
        network_detail_ipv4_address = WidgetBase('ipv4_address', 'Label', 'IP Address:')
        network_detail_ipv4_address_val = WidgetBase('ipv4_address', 'Entry',
                set_conf=datautil.augtool_set, conf_path=NIC_IP_PATH)
        network_detail_ipv4_netmask = WidgetBase('ipv4_netmask', 'Label', 'Netmask:')
        network_detail_ipv4_netmask_val = WidgetBase('ipv4_netmask', 'Entry',
                set_conf=datautil.augtool_set, conf_path=NIC_NETMASK_PATH)
        network_detail_ipv4_gateway = WidgetBase('ipv4_gateway', 'Label', 'Gateway:')
        network_detail_ipv4_gateway_val = WidgetBase('ipv4_gateway', 'Entry',
                set_conf=datautil.augtool_set, conf_path=NIC_GATEWAY_PATH)
        network_detail_vlan_id = WidgetBase('vlan_id', 'Label', _('Vlan Id'))
        network_detail_vlan_id_val = WidgetBase('vlan_id', 'Entry',
                set_conf=datautil.augtool_set, conf_path=NIC_VLAN_PATH)
        network_detail_back = WidgetBase('ipv4_back', ButtonList, '',
                params={'labels': ['Back'], 'callback': [self.network_detail_back]})
        network_change = WidgetBase('network_detail_apply_reset', ApplyResetBtn, params=(self.network_apply_cb))
        self.append([
                (network_detail_if, network_detail_driver),
                (network_detail_proto, network_detail_vendor),
                (network_detail_link_status, network_detail_mac_address),
                (WidgetBase('empty', 'Label', '', vhelp=30),),
                (network_detail_ipv4_setting_label,),
                (network_detail_ipv4_settings,),
                (network_detail_ipv4_address, network_detail_ipv4_address_val),
                (network_detail_ipv4_netmask, network_detail_ipv4_netmask_val),
                (network_detail_ipv4_gateway, network_detail_ipv4_gateway_val),
                (WidgetBase('empty', 'Label', '', vhelp=30),),
                (network_detail_vlan_id, network_detail_vlan_id_val,),
                (network_change, network_detail_back,),
                ])

    def network_detail_back(self, obj):
        w = obj.get_window()
        w.hide()

    def network_apply_cb(self, btn):
        # we need to do 2 steps to apply
        # a network configuration.
        # first write config to /etc/default/ovirt
        # then 'actually' apply the configuration.
        datautil.conf_apply(btn)
        network = Network()
        network.configure_interface()
        network.save_network_configuration()


class OcSecurity(OcLayout):

    def __init__(self):
        super(OcSecurity, self).__init__('security', _('Security'))

    def get_layout(self):
        remote_access = WidgetBase('remote_access', 'Label', _('Remote Access'),
                title=True)
        enable_ssh = WidgetBase('enable_ssh', 'CheckButton', _('Enable SSH '))
        local_access = WidgetBase('local_access', 'Label', _('Local Access'),
                title=True)
        local_access_password = WidgetBase('local_access_password', 'Label', _('Password:'))
        local_access_password_value = WidgetBase('local_access_password', 'Entry', '')
        local_access_password_confirm = WidgetBase('local_access_password', 'Label',
                                                _('Confirm Password:'))
        local_access_password_confirm_value = WidgetBase('local_access_password_confirm',
                                                        'Entry', '')
        Changes_Security = WidgetBase('security_apply_reset', ApplyResetBtn, )
        self.append([
                    (remote_access,),
                    (enable_ssh,),
                    (EMPTY_LINE,),
                    (local_access,),
                    (local_access_password, local_access_password_value,),
                    (local_access_password_confirm, local_access_password_confirm_value,),
                    (WidgetBase('empty', 'Label', '', vhelp=180),),
                    (Changes_Security,),
                    ])
        return self


class OcKDump(OcLayout):

    def __init__(self):
        super(OcKDump, self).__init__('kernel_dump', _('KernelDump'))

    def get_layout(self):
        kernedump_label = WidgetBase('kernel_dump', 'Label', _('Kernel Dump'), title=True)
        nfs_ssh_restore_check_button_list = WidgetBase('nfs_ssh_restor', ButtonList, '',
                params={'labels':[_('NFS'), _('SSH'), _('RESTORE')],
                        'type': 'CheckButton'})
        nfs_location_label = WidgetBase('nfs_location', 'Label', _('NFS Location'))
        nfs_location_value = WidgetBase('nfs_location', 'Entry', '', '')
        ssh_location_label = WidgetBase('ssh_location', 'Label', _('SSH Location'))
        ssh_location_value = WidgetBase('ssh_location', 'Entry', '', '')
        changes_kdump = WidgetBase('kdump', ButtonList, '',
                params={'labels':[_('Apply'), _('Reset')], })
        self.append([
                    (kernedump_label,),
                    (nfs_ssh_restore_check_button_list,),
                    (nfs_location_label,nfs_location_value,),
                    (ssh_location_label,ssh_location_value,),
                    (WidgetBase('empty', 'Label', '', vhelp=220),),
                    (changes_kdump,),
                    ])
        return self

layouts =\
        [
            OcStatus().get_layout(),
            OcNetwork().get_layout(),
            OcSecurity().get_layout(),
            OcLogging().get_layout(),
            OcKDump().get_layout(),
        ]
