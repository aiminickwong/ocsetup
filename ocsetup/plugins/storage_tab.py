#!/usr/bin/python
# storage_tab.py - Copyright (C) 2012 CloudTimes, Inc.
# Written by Jarod.W <work.iec23801@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA  02110-1301, USA.  A copy of the GNU General Public License is
# also available at http://www.gnu.org/copyleft/gpl.html.
import traceback

from ovirtnode.ovirtfunctions import log
from ovirtnode.iscsi import get_current_iscsi_initiator_name, \
    set_iscsi_initiator

from ocsetup.wrapper_ovirtfunctions import PluginBase
from ocsetup.ocsetup_ui_widgets import ButtonList
from ocsetup.ocsetup_ui import WidgetBase, _
from ocsetup.datautil import refresh_window


class Plugin(PluginBase):
    """
    Plugin for license information of IVNH.
    """
    def __init__(self):
        PluginBase.__init__(self, "Storage")
        self.iscsi_initiator_label = None
        self.iscsi_initiator_name_value = None
        self.iscsi_button = None

    def storage_apply(self, obj):
        from ocsetup.ocsetup import ocs
        log("enter storage apply")
        set_iscsi_initiator(
            ocs.page_Storage.iscsi_initiator_name_value_Entry.get_text())

    def storage_reset(self, obj):
        log("enter storage reset")
        refresh_window(obj)

    def form(self):
        log("enter storage form function....")
        try:
            self.iscsi_initiator_label = WidgetBase(
                "iscsi_initiator_label",
                "Label",
                "iSCSI Initiator Name:",
                title=True)

            self.iscsi_initiator_name_value = WidgetBase(
                "iscsi_initiator_name_value", "Entry", "", "",
                get_conf=get_current_iscsi_initiator_name)

            self.iscsi_button = WidgetBase(
                'iscsi_button', ButtonList, '',
                params={'labels': [_('Apply'), _('Reset')],
                'callback': [self.storage_apply, self.storage_reset]})
        except:
            log("Here some error happened.format ext:  %s " %
                traceback.format_exc())

        return [
            "Storage",
            "Storage",
            [
                (self.iscsi_initiator_label, self.iscsi_initiator_name_value),
                (WidgetBase('__', 'Label', vhelp=140),),
                (self.iscsi_button,),
            ]]

    def action(self):
        pass


def get_plugin():
    p = Plugin()
    return p.form()
