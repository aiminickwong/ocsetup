#!/usr/bin/python


# license.py - Copyright (C) 2012 CloudTimes, Inc.
# Plugins for showing information about license in ovirt-node.
# Written by Jarod.W <wangli@cloud-times.com>
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
import sys
import traceback

from ovirtnode.ovirtfunctions import log

sys.path.append("/usr/share/vdsm-reg")
from ovirtnode.license_utils import hasRegistered, getVersionInfo,\
    getLicenseConfig, hasStarted,\
    setLicenseConfig, computeDeprecatedDays,\
    DEFAULTREMAININGDAYS
from ocsetup.wrapper_ovirtfunctions import PluginBase
from ocsetup.ocsetup_ui import WidgetBase, EMPTY_LINE


class Plugin(PluginBase):
    """
    Plugin for license information of IVNH.
    """
    def __init__(self):
        PluginBase.__init__(self, "License")
        setLicenseConfig()

    def form(self):
        log("enter license form function....")
        remaindays = 0
        try:
            hasregister = hasRegistered()
            hasstart = hasStarted()

            headermessage = WidgetBase(
                "Basic_Information",
                "Label",
                "Basic Information",
                title=True)

            #show hypervisor version information
            version = getVersionInfo()
            versionlabel = WidgetBase(
                "Version", "Label",
                "Version:" + version)

            #show register information
            subtopiclabel = WidgetBase(
                "SUB_TOPIC_LABEL", "Label",
                "Basic Register Information: ", title=True)

            maclabel = WidgetBase(
                "MAC_LABEL", "Label", "",
                get_conf=lambda: "MAC :  " + getLicenseConfig(
                    "vars",
                    "mac",
                    "F0:DE:F1:00:00:00"))

            sysuuidlabel = WidgetBase(
                "SYSTEMUUID_LABEL", "Label", "",
                get_conf=lambda: "UUID :  " + getLicenseConfig(
                    "vars",
                    "systemuuid",
                    "00000000-0000-0000-0000-000000000000"))

            if hasstart and hasregister:
                taillabel_text = "Your hypervisor has been registered"
                taillabel_text.append(" successfully.Any question, ")
                taillabel_text.append("please contact : ")
                taillabel_text.append("service@cloud-times.com!")
            else:
                days, issuccess = computeDeprecatedDays()
                if issuccess:
                    log("the day is %d" % days)
                    remaindays = DEFAULTREMAININGDAYS - days
                    if remaindays < 0:
                        remaindays = 0
                else:
                    log("Failed to invoke computeDeprecatedDays. ")
                warninginfo = "You have "
                warninginfo.append(str(remaindays))
                warninginfo.append(" to use before registering.")
                taillabel_text = "Your hypervisor hasn't been registered."
                taillabel_text.append("Please use the information")
                taillabel_text.append(" above to register.")
                taillabel_text.append(warninginfo)
            note = WidgetBase("note", "Label", "Note:", title=True)
            taillabel = WidgetBase(
                "TAIL_LABEL", "Label",
                taillabel_text, width=80)
        except:
            log("Here some error happened.format ext:  %s "
                % traceback.format_exc())

        return [
            "License",
            "License",
            [
                (headermessage,),
                (versionlabel,),
                (subtopiclabel,),
                (maclabel,),
                (sysuuidlabel,),
                (note,),
                (taillabel,),
                (EMPTY_LINE,),
            ]]

    def action(self):
        pass


def get_plugin():
    p = Plugin()
    return p.form()
