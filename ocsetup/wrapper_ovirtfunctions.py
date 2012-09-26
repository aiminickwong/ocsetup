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


from subprocess import Popen, PIPE


def check_output(*args):
    return Popen(args, stdout=PIPE).communicate()[0]


def new_attr(obj, attr_name, attr_value):
    """
    create a attribute 'attr_name' with value 'attr_value'
    to instance then return the attr_value
    """
    obj.__setattr__(attr_name, attr_value)
    return obj.__getattribute__(attr_name)


exec_extra_buttons_cmds = {
    "restart": "echo 'restart'",
    "power_off": "echo 'power_off'",
    "log_off": "kill `pgrep -f ocsetup.ocsetup.run\(\)`",
    "lock": "echo 'lock'"}


class PluginBase(object):
    """Base class for pluggable Hypervisor configuration options.

    Configuration plugins are modules in ovirt_config_setup package.
    They provide implementation of this base class, adding specific
    form elements and processing.

    Because we only need to two parameters to init a plug in ocsetup,
    (origin version needs three), so we override this PluginBase.
    """

    def __init__(self, name):
        """Initialize a PluginBase instance

        name -- configuration option label
        """
        self.name = name
        """A name of the configuration option."""

    def label(self):
        """Returns label for the configuration option."""
        return self.name

    def form(self):
        """Returns form elements for the configuration option.
        Must be implemented by the child class.
        """
        pass

    def action(self):
        """Form processing action for the Hypervisor configuration option.
        Must be implemented by the child class.
        """
        pass
