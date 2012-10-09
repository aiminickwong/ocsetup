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
import gobject
import sys
import os
import time
from ocsetup_ui_widgets import ButtonList, DetailedList,\
    ConfirmDialog, ApplyResetBtn, RadioButtonList,\
    ValidateEntry, ProgressBar
from ocsetup_ui_constants import OC_MAX_ENTRY_LEN
from ovirtnode.ovirtfunctions import system_closefds, augtool_get,\
    nic_link_detected, log, is_valid_user_host, is_valid_nfs,\
    ovirt_store_config, unmount_config, system
from ovirtnode.log import get_rsyslog_config, ovirt_rsyslog, set_logrotate_size
from wrapper_ovirtfunctions import exec_extra_buttons_cmds, check_output
import gettext
import datautil
from ovirtnode.network import Network
from ovirtnode.kdump import write_kdump_config, restore_kdump_config
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
                    'params', 'vhelp', 'width',
                    'init_func', 'init_func_args'):
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
        networking_status = WidgetBase(
            'networking_status', 'Label', _('Network Status'), title=True)
        networking_list = WidgetBase(
            'status_network_list', DetailedList, '',
            params={'labels':
            [_('Device'), _('Bootproto'),
            _('IPV4 Address'), _('IPV6 Address')]},
            get_conf=datautil.read_status_datas)
        logical_network = WidgetBase(
            'logical_network', DetailedList, '',
            params={'labels':
            [_('Logical Network'), _('Device'), _('MAC Address')]},
            get_conf=datautil.read_logical_netwrok)
        status_log_label = WidgetBase(
                'status_log', 'Label', _('Log: '), title=True)
        status_log_value = WidgetBase(
            'status_log_val', 'Label',
            get_conf=datautil.read_log_status)

        running_vms_label = WidgetBase(
            'running_vms_label', 'Label', _('Running VMs: '), title=True)
        running_vms_value = WidgetBase(
            'running_vms_value', 'Label',
            get_conf=datautil.get_running_vms)

        status_buttons = WidgetBase(
            'status_buttons', ButtonList, '',
            params={'labels':
            [_('Log Off'), _('Lock'), _('Restart'), _('Power Off')],
            'callback':
            [self.confirm_cmd, self.confirm_cmd,
            self.confirm_cmd, self.confirm_cmd]})
        self.append([
                    (networking_status,),
                    (networking_list,),
                    (logical_network,),
                    (EMPTY_LINE,),
                    (EMPTY_LINE,),
                    (status_log_label, status_log_value,),
                    (running_vms_label, running_vms_value,),
                    (status_buttons,),
                    ])
        return self


class OcLogging(OcLayout):

    def __init__(self):
        super(OcLogging, self).__init__('logging', _('Logging'))

    def get_layout(self):
        logging = WidgetBase(
            'logging', 'Label', _('Logging'), title=True)
        log_max_size_label = WidgetBase(
            'log_max_size_label', 'Label',
            _('Logrotate Max Log Size (KB):'))
        #because log_max_size_value has conf_path,
        #so set_conf will actually take two params(conf_path and value),
        #but, in fact, we only need one(value), conf_path is useless here.
        #so, using lambda to absorb conf_path, and only pass value to real
        #set_conf callback.
        log_max_size_value = WidgetBase(
            'log_max_size_value', ValidateEntry,
            get_conf=lambda v: datautil.augtool_get(v) or '1024',
            set_conf=lambda _, v: set_logrotate_size(v),
            conf_path=LOG_LOGRORATE_SIZE_PATH,
            params={'validator': datautil.validate_int})
        log_rsys = WidgetBase(
            'rsys', 'Label',
            _('Rsyslog is an enhanced multi-threaded syslog'), title=True)
        log_server_address = WidgetBase(
            'log_server_address', 'Label', _('Server Address:'))
        log_server_address_val = WidgetBase(
            'log_server_address', ValidateEntry,
            get_conf=lambda: get_rsyslog_config()[0] if
            get_rsyslog_config() else "",
            params={'validator': datautil.validate_ip})
        log_server_server_port = WidgetBase(
            'log_server_port', 'Label', _('Server Port:'))
        log_server_server_port_val = WidgetBase(
            'log_server_port', ValidateEntry,
            get_conf=lambda: get_rsyslog_config()[1] if
            get_rsyslog_config() else "514",
            params={'validator': datautil.validate_port},
            set_conf=self.set_log_server)
        changes_log = WidgetBase('log_apply_reset', ApplyResetBtn)
        self.append([
                    (logging,),
                    (log_max_size_label, log_max_size_value),
                    (log_rsys,),
                    (log_server_address, log_server_address_val),
                    (log_server_server_port, log_server_server_port_val,),
                    (WidgetBase('empty', 'Label', '', vhelp=140),),
                    (changes_log,)])
        return self

    def set_log_server(self, _):
        try:
            from ocsetup import ocs
            page = ocs.page_logging
            cur_server = page.log_server_address_custom.entry.get_text()
            cur_port = page.log_server_port_custom.entry.get_text()
            ovirt_rsyslog(cur_server, cur_port, "udp")
        except Exception, e:
            log(e)
            pass


class OcNetwork(OcLayout):

    def __init__(self):
        super(OcNetwork, self).__init__('network', _('Network'))

    def get_layout(self):
        System_Identification = WidgetBase(
            'system_identification', 'Label',
            _('System Identification'), title=True)
        Hostname_label = WidgetBase('hostname', 'Label', _('Hostname'))
        Hostname_value = WidgetBase(
            'hostname', 'Entry', '', _(''),
            get_conf=datautil.get_hostname)

        DNS_SERVER1_label = WidgetBase(
            'dns_server1', 'Label', _('DNS Server1:'))
        DNS_SERVER1_value = WidgetBase(
            'dns_server1', ValidateEntry,
            get_conf=augtool_get, conf_path=DNS_SERVER1_PATH,
            set_conf=datautil.augtool_set,
            params={'validator': datautil.validate_ip})
        DNS_SERVER2_label = WidgetBase(
            'dns_server2', 'Label', _('DNS Server2:'))
        DNS_SERVER2_value = WidgetBase(
            'dns_server2', ValidateEntry,
            get_conf=augtool_get, conf_path=DNS_SERVER2_PATH,
            set_conf=datautil.augtool_set,
            params={'validator': datautil.validate_ip})
        NTP_SERVER1_label = WidgetBase(
            'ntp_server1', 'Label', _('NTP Server1:'))
        NTP_SERVER1_value = WidgetBase(
            'ntp_server1', ValidateEntry,
            get_conf=augtool_get, conf_path=NTP_SERVER1_PATH,
            set_conf=datautil.augtool_set,
            params={'validator': datautil.validate_ip})
        NTP_SERVER2_label = WidgetBase(
            'ntp_server2', 'Label', _('NTP Server2:'))
        NTP_SERVER2_value = WidgetBase(
            'ntp_server2', ValidateEntry,
            get_conf=augtool_get, conf_path=NTP_SERVER2_PATH,
            set_conf=datautil.augtool_set,
            params={'validator': datautil.validate_ip})

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
                s = lambda t: "Field is disabled" if t else ''
                page.ipv4_address_Entry.set_text(s(state))
                page.ipv4_netmask_Entry.set_text(s(state))
                page.ipv4_gateway_Entry.set_text(s(state))
                page.ipv4_address_Entry.set_property("editable", not state)
                page.ipv4_netmask_Entry.set_property("editable", not state)
                page.ipv4_gateway_Entry.set_property("editable", not state)

            network_page.ipv4_settings_custom.btns[1].connect(
                "toggled", static_cb, network_page)

        NETWORK_LIST = WidgetBase(
            'network_network_list', DetailedList, '',
            params={'labels': [_('Device'), _('Status'), _('Model'),
            _('MAC Address')], 'callback': show_networkdetail_cb},
            get_conf=lambda: datautil.read_nics(datautil.filter_rn_get_list))
        changes_network = WidgetBase('network_apply_reset', ApplyResetBtn)
        self.append([
                    (System_Identification, ),
                    (Hostname_label, Hostname_value,),
                    (DNS_SERVER1_label, DNS_SERVER1_value),
                    (DNS_SERVER2_label, DNS_SERVER2_value),
                    (NTP_SERVER1_label, NTP_SERVER1_value),
                    (NTP_SERVER2_label, NTP_SERVER2_value),
                    (NETWORK_LIST,),
                    (changes_network,),
                    ])
        return self


class NetworkDetail(OcLayout):

    def __init__(self, treeview_datas):
        super(NetworkDetail, self).__init__('network_detail', 'invisible_tab')
        ifname = treeview_datas[0]
        (self.dev_interface, dev_bootproto, dev_vendor, dev_address,
            dev_driver, dev_conf_status, dev_bridge) =\
            datautil.read_nics(lambda allinfos: allinfos[0][ifname].split(','))
        if nic_link_detected(ifname):
            link_status = "Active"
        else:
            link_status = "Inactive"
        network_detail_if = WidgetBase(
            'interface', 'Label', '',
            get_conf=lambda: _("Interface: ") + self.dev_interface)
        network_detail_driver = WidgetBase(
            'driver', 'Label', '',
            get_conf=lambda: _("Driver: ") + dev_driver)
        network_detail_proto = WidgetBase(
            'protocol', 'Label', '',
            get_conf=lambda: _('Protocol: ') + dev_bootproto)
        network_detail_vendor = WidgetBase(
            'vendor', 'Label', '',
            get_conf=lambda: _('Vendor: ') + dev_vendor)
        network_detail_link_status = WidgetBase(
            'link_status', 'Label', '',
            get_conf=lambda: _('Link Status: ') + link_status)
        network_detail_mac_address = WidgetBase(
            'mac_address', 'Label', '',
            get_conf=lambda: _('Mac Address: ') + dev_address)
        network_detail_ipv4_setting_label = WidgetBase(
            'ipv4_setting', 'Label', _('IPV4 Settings:'))
        network_detail_ipv4_settings = WidgetBase(
            'ipv4_settings', RadioButtonList, '',
            params={'labels': ['Disable', 'Static'], 'type': 'CheckButton'})
        network_detail_ipv4_address = WidgetBase(
            'ipv4_address', 'Label',
            'IP Address:')
        network_detail_ipv4_address_val = WidgetBase(
            'ipv4_address', 'Entry',
            set_conf=datautil.augtool_set, conf_path=NIC_IP_PATH)
        network_detail_ipv4_netmask = WidgetBase(
            'ipv4_netmask', 'Label', 'Netmask:')
        network_detail_ipv4_netmask_val = WidgetBase(
            'ipv4_netmask', 'Entry',
            set_conf=datautil.augtool_set, conf_path=NIC_NETMASK_PATH)
        network_detail_ipv4_gateway = WidgetBase(
            'ipv4_gateway', 'Label', 'Gateway:')
        network_detail_ipv4_gateway_val = WidgetBase(
            'ipv4_gateway', 'Entry',
            set_conf=datautil.augtool_set, conf_path=NIC_GATEWAY_PATH)
        network_detail_vlan_id = WidgetBase('vlan_id', 'Label', _('Vlan Id'))
        network_detail_vlan_id_val = WidgetBase('vlan_id', 'Entry', '')
        network_detail_back = WidgetBase(
            'ipv4_back', ButtonList, '',
            params={'labels': ['Back'],
            'callback': [self.network_detail_back]})
        network_change = WidgetBase(
            'network_detail_apply_reset',
            ApplyResetBtn,
            params={'apply_cb': self.network_apply_cb})
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
            (network_change, network_detail_back,)])

    def network_detail_back(self, obj):
        w = obj.get_window()
        w.hide()

    def network_apply_cb(self, btn):
        # we need to do 2 steps to apply
        # a network configuration.
        # first write config to /etc/default/ovirt
        datautil.augtool_set(NIC_BOOTIF_PATH, self.dev_interface)
        # then 'actually' apply the configuration.
        datautil.conf_apply(btn)
        network = Network()
        network.configure_interface()
        network.save_network_configuration()


class OcSecurity(OcLayout):

    def __init__(self):
        super(OcSecurity, self).__init__('security', _('Security'))

    def get_layout(self):
        remote_access = WidgetBase(
            'remote_access', 'Label',
            _('Remote Access'),
            title=True)
        enable_ssh = WidgetBase(
            'enable_ssh', 'CheckButton',
            '', get_conf=self.get_ssh_conf, conf_path=ENABLE_SSH_PATH,
            set_conf=self.set_ssh_conf)
        local_access = WidgetBase(
            'local_access', 'Label', _('Local Access'), title=True)
        local_access_password = WidgetBase(
            'local_access_password', 'Label', _('Password:'))
        local_access_password_value = WidgetBase(
            'local_access_password', ValidateEntry, '',
            params={'validator': datautil.pw_strength,
                    'entry_init_func': ("set_visibility",),
                    'entry_init_func_args': ((False,),)})
        local_access_password_confirm = WidgetBase(
            'local_access_password', 'Label',
            _('Confirm Password:'))
        local_access_password_confirm_value = WidgetBase(
            'local_access_password_confirm',
            ValidateEntry, '',
            params={'validator': datautil.is_pw_same,
            'entry_init_func': ("set_visibility",),
            'entry_init_func_args': ((False,),)},
            set_conf=self.change_password)
        Changes_Security = WidgetBase('security_apply_reset', ApplyResetBtn)
        local_access_pw_cfm = local_access_password_confirm
        local_access_pw_cfm_val = local_access_password_confirm_value
        self.append([
                    (remote_access,),
                    (enable_ssh,),
                    (EMPTY_LINE,),
                    (local_access,),
                    (local_access_password, local_access_password_value,),
                    (local_access_pw_cfm, local_access_pw_cfm_val,),
                    (WidgetBase('empty', 'Label', '', vhelp=140),),
                    (Changes_Security,),
                    ])
        return self

    def get_ssh_conf(self, path):
        try:
            from ocsetup import ocs
            state = augtool_get(path)
            if state == "no":
                ocs.page_security.enable_ssh_CheckButton.set_active(False)
            elif state == "yes":
                ocs.page_security.enable_ssh_CheckButton.set_active(True)
            else:
                log('ssh PasswordAuthentication invail val:' + state)
        except Exception, e:
            log(e)
            pass
        # because this widget (CheckButton) is kind special,
        # it will return `two` value: one is the state of ssh enable/disable
        # and the other one is the label, which is a static string.
        # that is , 'Enable SSH PasswordAuthentication'
        return _('Enable SSH PasswordAuthentication')

    def set_ssh_conf(self, path, _):
        try:
            from ocsetup import ocs
            ssh_btn = ocs.page_security.enable_ssh_CheckButton
            check_button_state = ssh_btn.get_active()
            current_state = augtool_get(path)
            if check_button_state is False:
                datautil.augtool_set(path, "no")
            else:
                datautil.augtool_set(path, "yes")
            if ((current_state == "no" and check_button_state is True) or
                    (current_state != "no" and check_button_state is False)):
                    # SSHD CONFIGURE CHANGED, RESTART.
                    system_closefds("service sshd restart &>/dev/null")
        except Exception, e:
            print e

    def change_password(self, _):
        try:
            from ocsetup import ocs
            from ovirtnode.password import set_password
            page = ocs.page_security
            pw1 = page.local_access_password_custom.entry.get_text()
            set_password(pw1, "admin")
            log("change password for admin:" + pw1)
        except Exception, e:
            log(e)
            pass


class OcKDump(OcLayout):

    def __init__(self):
        super(OcKDump, self).__init__('kernel_dump', _('KernelDump'))

    def get_layout(self):
        kernedump_label = WidgetBase(
            'kernel_dump', 'Label', _('Kernel Dump'), title=True)
        nfs_ssh_restore_check_button_list = WidgetBase(
            'nfs_ssh_restore', RadioButtonList, '',
            params={
                'labels': [_('NFS'), _('SSH'), _('RESTORE')],
                'callback': [
                    self.disable_entry_cb,
                    self.disable_entry_cb,
                    self.disable_entry_cb]},
            get_conf=self.get_kdump_conf)
        nfs_location_label = WidgetBase(
            'nfs_location', 'Label',
            _('NFS Location'))
        nfs_location_value = WidgetBase(
            'nfs_location', ValidateEntry,
            params={'validator': is_valid_nfs,
            'entry_init_func': ('set_width_chars',),
            'entry_init_func_args': ((OC_MAX_ENTRY_LEN,),)},
            set_conf=write_kdump_config)
        ssh_location_label = WidgetBase(
            'ssh_location', 'Label',
            _('SSH Location'))
        ssh_location_value = WidgetBase(
            'ssh_location', ValidateEntry,
            params={'validator': lambda _: True,
                    'entry_init_func': ('set_sensitive', 'set_width_chars'),
                    'entry_init_func_args': ((False,), (OC_MAX_ENTRY_LEN,))},)
        changes_kdump = WidgetBase(
            'kdump', ApplyResetBtn,
            params={'apply_cb': self.kdump_apply})
        self.append([
                    (kernedump_label,),
                    (nfs_ssh_restore_check_button_list,),
                    (nfs_location_label,),
                    (nfs_location_value,),
                    (ssh_location_label,),
                    (ssh_location_value,),
                    (WidgetBase('empty', 'Label', '', vhelp=100),),
                    (changes_kdump,),
                    ])
        return self

    def disable_entry_cb(self, btn):
        if btn.get_active() is False:
            return
        try:
            from ocsetup import ocs
            page = ocs.page_kernel_dump
            btns = ocs.page_kernel_dump.nfs_ssh_restore_custom.btns
            page.ssh_location_custom.entry.set_sensitive(False)
            page.nfs_location_custom.entry.set_sensitive(False)
            if btn == btns[0]:
                page.nfs_location_custom.entry.set_sensitive(True)
                page.ssh_location_custom.validate_status.set_label("")
                page.ssh_location_custom.bool_validate_state = 0
            if btn == btns[1]:
                page.ssh_location_custom.entry.set_sensitive(True)
                page.nfs_location_custom.validate_status.set_label("")
                page.nfs_location_custom.bool_validate_state = 0
        except e:
            pass

    def kdump_apply(self, obj):
        try:
            from ocsetup import ocs
        except ImportError:
            pass
        else:
            page = ocs.page_kernel_dump
            buttons = page.nfs_ssh_restore_custom.btns
            val = None
            for i in range(3):
                # i == 0 is NFS, i == 1 is SSH, i == 2 is RESTORE
                if buttons[i].get_active() and i == 0:
                    val = page.nfs_location_custom.entry.get_text()
                elif buttons[i].get_active() and i == 1:
                    val = page.ssh_location_custom.entry.get_text()
                elif buttons[i].get_active() and i == 2:
                    restore_kdump_config()
            if val:
                write_kdump_config(val)
                pb = ProgressBar()
                pb.make_progress(0.1)
                if '@' in val:
                    if os.path.exists("/usr/bin/kdumpctl"):
                        kdump_prop_cmd = "kdumpctl propagate"
                    else:
                        kdump_prop_cmd = "service kdump propagate"
                    from sshcmd import runcmd
                    runcmd(kdump_prop_cmd)
                    pb.make_progress(0.2)
                    if runcmd:
                        # SSH LOGIN SUCCESS.
                        ovirt_store_config("/root/.ssh/kdump_id_rsa.pub")
                        ovirt_store_config("/root/.ssh/kdump_id_rsa")
                        ovirt_store_config("/root/.ssh/known_hosts")
                        ovirt_store_config("/root/.ssh/config")
                pb.make_progress(0.5)
                system('servic kdump restart &')
                while True:
                    res = check_output('service kdump status')
                    if 'starting' not in res:
                        break
                    pb.make_progress(0.5)
                    time.sleep(3)
                pb.make_progress(0.8)
                if 'Kdump is not operational' in res:
                    # restart kdump Failed.
                    unmount_config("/etc/kdump.conf")
                    if os.path.exists("/etc/kdump.conf"):
                        os.remove("/etc/kdump.conf")
                    pb.make_progress(0, 'FAILED!')
                    pb.progress_label.set_label('FAILED!')
                elif 'Kdump is operational' in res:
                    ovirt_store_config("/etc/kdump.conf")
                    pb.make_progress(1, 'successful!')
                else:
                    log('kdump start Failed:' + res)
                    pb.make_progress(0, 'FAILED!')
                    pb.progress_label.set_label('FAILED!')

    def get_kdump_conf(self):
        try:
            from ocsetup import ocs
        except:
            return
        with open("/etc/kdump.conf") as kdump_config_file:
            btns = ocs.page_kernel_dump.nfs_ssh_restore_custom.btns
            config_nfs = ocs.page_kernel_dump.nfs_location_custom
            config_ssh = ocs.page_kernel_dump.ssh_location_custom
            config_nfs.entry.set_sensitive(False)
            config_ssh.entry.set_sensitive(False)
            for line in kdump_config_file:
                if not line.startswith("#"):
                    if line.startswith("net"):
                        if "@" in line:
                            btns[1].set_active(True)
                            config_ssh.entry.set_text(line[4:].strip())
                            config_ssh.entry.set_sensitive(True)
                        elif ':' in line:
                            btns[0].set_active(True)
                            config_nfs.entry.set_text(line[4:].strip())
                            config_nfs.entry.set_sensitive(True)
                    elif "/dev/HostVG/Data" in line:
                        btns[2].set_active()

layouts =\
    [
        OcStatus().get_layout(),
        OcNetwork().get_layout(),
        OcSecurity().get_layout(),
        OcLogging().get_layout(),
        OcKDump().get_layout()
    ]
