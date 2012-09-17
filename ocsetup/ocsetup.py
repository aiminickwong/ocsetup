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
import os
import datautil
from ocsetup_ui import layouts
from ocsetup_ui_widgets import ShellWindow, LogWindow, ColorLabel, OcPage
from ocsetup_ui_constants import OC_NOTEBOOK_TAB_WIDTH, OC_NOTEBOOK_TAB_HEIGHT,\
                            OC_NOTEBOOK_WIDTH, OC_NOTEBOOK_HEIGHT,\
                            OC_HEADER_HEIGHT, \
                            OC_FOOTER_HEIGHT,\
                            OC_WIDTH, OC_HEIGHT,\
                            OC_HEADER_BG, OC_FOOTER_BG,\
                            GTK_SIGNAL_DESTROY, GTK_SIGNAL_SWITCH_PAGE
from distutils.sysconfig import get_python_lib
from wrapper_ovirtfunctions import new_attr
OVIRT_PLUGINS_PATH = get_python_lib() + '/ocsetup/plugins/'
sys.path.append(OVIRT_PLUGINS_PATH)


class OcSetup(object):

    def __init__(self, pages):
        self.window = gtk.Window()
        self.window.set_default_size(OC_WIDTH, OC_HEIGHT)
        self.window.set_position(gtk.WIN_POS_CENTER)
        self.vbox = gtk.VBox(False, 1)

        self.notebook = gtk.Notebook()
        self.notebook.set_tab_pos(gtk.POS_LEFT)
        self.notebook.connect(GTK_SIGNAL_SWITCH_PAGE, self._handle_switch_page)
        self.notebook.set_size_request(OC_NOTEBOOK_WIDTH, OC_NOTEBOOK_HEIGHT)
        self.notebook.set_show_border(False)
        self.shell = ShellWindow(self.window, confirm=True,
                        confirm_msg="Are you sure to use shell?")
        self.logger = LogWindow(self.window)
        self.pages = {}
        # Get Plugins from path `OVIRT_PLUGINS_PATH`
        #sys.path.append(OVIRT_PLUGINS_PATH)
        for plugins in os.walk(OVIRT_PLUGINS_PATH):
            for plugin_filename in plugins[2]:
                if plugin_filename.endswith('.py'):
                    try:
                        plugin = __import__(plugin_filename[:-3]).get_plugin()
                        if plugin:
                            pages.append(plugin)
                    except:
                        pass
        for page in pages:
            tab = gtk.Label(page[1])
            new_attr(self, 'tab_' + page[0], tab)
            tab.set_size_request(OC_NOTEBOOK_TAB_WIDTH, OC_NOTEBOOK_TAB_HEIGHT)
            # we need to call _create_page to create self.xxx_page
            _page = new_attr(self, 'page_' + page[0], self._create_page(page))
            self.notebook.append_page(_page, tab)
        header_img = ColorLabel('', OC_HEADER_BG)
        header_img.set_size_request(OC_WIDTH, OC_HEADER_HEIGHT)
        footer_img = ColorLabel('', OC_FOOTER_BG)
        footer_img.set_size_request(OC_WIDTH, OC_FOOTER_HEIGHT)
        self.vbox.pack_start(header_img, False, False)
        self.vbox.pack_start(self.notebook, False, False)
        self.vbox.pack_start(footer_img, True, True)
        self.window.add(self.vbox)
        self.window.connect(GTK_SIGNAL_DESTROY, lambda w: gtk.main_quit())
        self.window.show_all()

    def _create_page(self, layout):
        page = OcPage(layout)
        self.pages[layout[0]] = page.oc_widgets
        return page

    def _handle_switch_page(self, notebook, page, page_num):
        curpage = notebook.get_nth_page(page_num)
        datautil.datas_refresh(curpage.oc_widgets)


def run():
    global ocs
    ocs = OcSetup(layouts)
    gtk.main()
