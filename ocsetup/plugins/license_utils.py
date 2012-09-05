#!/usr/bin/python
# license_util.py - Copyright (C) 2012 CloudTimes, Inc.
# license utils for CT in ovirt-node.
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
import time
import datetime

from snack import *
from ovirtnode.ovirtfunctions import *

sys.path.append('/usr/share/vdsm-reg')
#import deployUtil

#================define basic variable.=======================
PRODUCT_ID = "IVNH"
DEFAULTREMAININGDAYS = 30

LICENSEFILE = "/etc/sysconfig/license"
LICENSECONFIG = "/etc/sysconfig/licenseconfig"
LICENSEDATE = "/etc/sysconfig/.regdate"

BINNODEDECODE = "/usr/sbin/node-decode"

config = ConfigParser.ConfigParser()

#=================basic check function ========================
def isCTServer():
    return False

def hasDeprecated():
    days, issuccess = computeDeprecatedDays()
    if issuccess:
        if days > DEFAULTREMAININGDAYS:
            return True
        else:
            return False
    else:
        log("Failed to invoke computeDeprecatedDays .")
    return True

def computeDeprecatedDays():
    regTime = None
    ISOTIMEFORMAT = "%Y-%m-%d"
    try:
        if not os.path.exists(LICENSEDATE):
            return 0, True
        with file(LICENSEDATE) as f:
            for line in f:
                regTime = line[0:10]
                break
        log("reg time is : %s" % regTime)
        t = time.strptime(str(regTime), ISOTIMEFORMAT)
        begin_day = datetime.datetime(*t[0:6])
        today = datetime.datetime.today()
        rap = today - begin_day
        return rap.days, True
    except:
        log("Failed to test whether the license deprecates.")
        log("Traceback is : %s" % traceback.format_exc())
        return -1, False

    return -1, False

def hasStarted():
    if not os.path.exists(LICENSEDATE):
        return False
    else:
        return True

def hasRegistered():
    # judge whether the server is ctserver.
    if isCTServer():
        log("The server is from CloudTimes, so it has registed defaultly.")
        return True

    # check whether licensefile exists. if not, return false
    if not os.path.exists(LICENSEFILE):
        log("The file ( %s ) doesn't exist. I guess the machine need to be registered." % LICENSEFILE)
        return False

    #invoke node-decode to see whether the license is deprecated.
    out = None
    err = None
    ret = None
    macaddress = getLicenseConfig("vars", "mac", "F0:DE:F1:00:00:00")
    hostuuid = getLicenseConfig ("vars", "systemuuid", "00000000-0000-0000-0000-000000000000")
    #out, err, ret = deployUtil._logExec([BINNODEDECODE, '-f', LICENSEFILE, '-m', macaddress, '-u', hostuuid, '-p', PRODUCT_ID])
    out = err = ret = 0
    if ret != 0:
        log("Failed to check the licensefile. the out is %s . " % out)
        return False
    else:
        return True
    return False

def getVersionInfo():
    return PRODUCT_VERSION

def getMacAddress():
    #macs = deployUtil.getMacs()
    macs = "0"
    #SUNUS TEMPORARILY CHANG MACS's VALUE
    if len(macs) == 0:
        return "00:00:00:00:00:00"
    return macs[0]

#==========================read and write the license conf file.=========================

def setConfigItem(section, item, value):
    try:
        config.read(LICENSECONFIG)
        if not config.has_section(section):
            config.add_section(section)
        config.set(section, item, value)
        config.write(file(LICENSECONFIG, 'w'))
    except:
        log("Error for setConfigItem: %s" % traceback.format_exc())
        return False
    return True

def setLicenseConfig():
    #if setConfigItem("vars", "systemuuid", deployUtil.getMachineUUID()) \
    if setConfigItem("vars", "systemuuid", "5d7a2335-12a4-4894-a57f-ba48df5a0a07") \
    and setConfigItem("vars", "mac", getMacAddress()) :
        return True
    else:
        return False

def getLicenseConfig(section, item, defaultvalue):
    config.read(LICENSECONFIG)
    try:
       return config.get(section, item)
    except:
       return defaultvalue

