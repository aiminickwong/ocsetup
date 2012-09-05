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
import ConfigParser

from snack import *

sys.path.append('/usr/share/vdsm-reg')
from ovirtnode.ovirtfunctions import *
from ocsetup.ocsetup_ui import WidgetBase, EMPTY_LINE
from license_utils import hasRegistered, getVersionInfo, getLicenseConfig, hasStarted, \
                          setLicenseConfig, computeDeprecatedDays, DEFAULTREMAININGDAYS
from ocsetup.wrapper_ovirtfunctions import PluginBase
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
        '''
        try:
            hasregister = hasRegistered()
            hasstart = hasStarted()

            headermessage = ('label', 'Basic Information', 'Basic Information')
            #heading = Label(headermessage)
            #show hypervisor version information
            version = getVersionInfo()
            versionlabel = ('label', "  Version: " + version,
                    "Version:" + version)


            #show basic register information
            subtopiclabel = ('label', 'Basic Register Information: ',
                             'Basic Register Information')
            licenseconfig = getLicenseConfig("vars", "mac", "F0:DE:F1:00:00:00")
            maclabel = ('label',
                "Mac: "+ licenseconfig,
                "Mac: "+ licenseconfig)

            lc = getLicenseConfig("vars", "systemuuid",
                    "00000000-0000-0000-0000-000000000000")
            systemuuidlabel = ('label', "  SystemUUID: " + lc,
                                " SystemUUID:  " + lc)
            if hasstart and hasregister:
                taillabel = "Note: Your hypervisor has been registered successfully.\n \
                Any question, please contact : service@cloud-times.com!"
            else:
                days, issuccess = computeDeprecatedDays()
                if issuccess:
                    log("the day is %d" % days)
                    remaindays = DEFAULTREMAININGDAYS - days
                    if remaindays < 0:
                        remaindays = 0
                else:
                    log("Failed to invoke computeDeprecatedDays. ")
                warninginfo = "You have " + str(remaindays) + " to use before registering."
                taillabel_text = "Note: Your hypervisor hasn't been registered.Please use\nthe information above to register.\n"+warninginfo
            #elements.setField(Textbox(56,4, taillabel), 0, 7, anchorLeft = 1)
            taillabel = ('label', taillabel_text, taillabel_text)
        except:
            log("Here some error happened.format ext:  %s " % traceback.format_exc())
        #return [Label(""), elements]
        '''

        headermessage = WidgetBase('Basic_Information', 'Label', 'Basic Information',
                extras={'title': True})
        version = 'test_version'
        subtopiclabel = WidgetBase('Basic_Register_Information','Label', 
                             'Basic Register Information')

        versionlabel =  WidgetBase("Version", 'Label', 
                    "Version:" + version)

        taillabel_text = "Note: Your hypervisor hasn't been registered.Please use\nthe information above to register.\n"
        taillabel = WidgetBase('tailtext', 'Label', taillabel_text)
        return [ 'License', 'License',
                    [
                        (headermessage,),
                        (versionlabel,),
                        (subtopiclabel,),
                        (taillabel,),
                        (EMPTY_LINE,),
                    ]
              ]


    def action(self):
        pass

def get_plugin():
    p = Plugin()
    return p.form()
