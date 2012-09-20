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


import os
import sys
from distutils.core import setup
SETUP_PREFIX = '/usr/share/'


def find_data_files(paths, prefix):
    ret = []
    for path in paths:
        for dirs in os.walk(path):
            if len(dirs[2]) > 0:
                ret.append((prefix + dirs[0],
                            [dirs[0] + '/' + f for f in dirs[2]]))
    return ret

if sys.argv[1] == 'install':
    os.system('bash ./scripts/makemo.sh %s' % SETUP_PREFIX)

DATAS = find_data_files(paths=('doc',),
                        prefix='/usr/share/')
DATAS_PO = find_data_files(paths=('po',), prefix='/tmp/')
DATAS.extend(DATAS_PO)
DATAS.append(('/usr/libexec/', ['./scripts/run-ocsetup']))
DATAS.append(('/usr/libexec/', ['./scripts/ovirtocsetup']))
DATAS.append(('/tmp/', ['./scripts/makemo.sh']))
setup(
        name        = "OcSetup",
        version     = "0.01",
        url         = "https://github.com/jarod-w/ocsetup",
        author      = "sunus Lee",
        author_email= "sunuslee@gmail.com",
        packages    = ['ocsetup',
                       'ocsetup.plugins'],
        data_files  = DATAS,
        license     = 'GPLV2',
    )
