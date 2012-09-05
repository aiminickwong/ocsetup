#!/bin/bash

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


if [ ! -d "locale" ];then
    mkdir locale
fi
for f in po/*.po; do
    msgfmt.py $f
    if [ $? -eq 0 ]; then
        bn=`basename $f`
        lang=${bn%.po}
        mkdir -p locale/$lang/LC_MESSAGES
        mv po/$lang.mo locale/$lang/LC_MESSAGES/ocsetup.mo
    fi
done

# $1 is the destination path of local
# automatically passed by the setup.py
if [ "$1" != "" ]; then
    if [ ! -d $1 ]; then
        mkdir -p $1
    fi
    cp -fr locale "$1"
fi
