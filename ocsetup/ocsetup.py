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
from ocsetup_ui_widgets import ShellWindow, LogWindow, DetailedList,\
                               ColorLabel
from ocsetup_ui_constants import OC_NOTEBOOK_TAB_WIDTH, OC_NOTEBOOK_TAB_HEIGHT,\
                            OC_NOTEBOOK_WIDTH, OC_NOTEBOOK_HEIGHT,\
                            OC_TEXT_WIDTH, OC_TEXT_HEIGHT,\
                            OC_DETAILEDLIST_HEIGHT,\
                            OC_HEADER_HEIGHT, \
                            OC_FOOTER_HEIGHT,\
                            OC_WIDTH, OC_HEIGHT,\
                            OC_HEADER_BG, OC_FOOTER_BG,\
                            OC_PAGE_WIDGET_HPADDING, OC_PAGE_LISTS_HPADDING,\
                            OC_ALIGNMENT_LONG_TITLE_X,\
                            OC_ALIGNMENT_LONG_TITLE_Y,\
                            OC_ALIGNMENT_TITLE_X, OC_ALIGNMENT_TITLE_Y,\
                            OC_ALIGNMENT_CONTENT_X, OC_ALIGNMENT_CONTENT_Y,\
                            OC_DEFAULT, GTK_SIGNAL_DESTROY, GTK_SIGNAL_SWITCH_PAGE
from distutils.sysconfig import get_python_lib
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
            self._new_attr('tab_' + page[0], tab)
            tab.set_size_request(OC_NOTEBOOK_TAB_WIDTH, OC_NOTEBOOK_TAB_HEIGHT)
            # we need to call _create_page to create self.xxx_page
            _page = self._new_attr('page_' + page[0], self._create_page(page))
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
        vbox = gtk.VBox(False, 10)
        self.pages[layout[0]] = {}
        d = self.pages[layout[0]]
        for ir, item_row in enumerate(layout[2]):
            hbox = gtk.HBox(False)
            if ir == (len(layout[2]) - 1):
                hbox.pack_start(gtk.Label(), True, False)
            for i, item in enumerate(item_row):
                # check to create item via gtk basic class
                # or via comstum functions which is callable
                if callable(item['type']):
                    if item.get('params'):
                        _item = item['type'](item['params'])
                    else:
                        _item = item['type']()
                    item['type'] = 'custom'
                else:
                    _item = self._create_item(item)
                _item.get_conf = item.get('get_conf', None)
                _item.set_conf = item.get('set_conf', None)
                _item.conf_path = item.get('conf_path', None)
                self._new_attr(item['name'] + '_' + item['type'], _item)
                d['%s_%s' % (item['name'], item['type'])] = _item

                if isinstance(_item, (gtk.CheckButton, DetailedList)):
                    hbox.pack_start(_item, True, True,
                                    padding=OC_PAGE_LISTS_HPADDING)
                # HButtonBox is kind of list, use OC_PAGE_LISTS_HPADDING too.
                elif isinstance(_item, gtk.HButtonBox):
                    hbox.pack_start(_item, False, False,
                                    padding=OC_PAGE_LISTS_HPADDING)
                else:
                    hbox.pack_start(_item, False, False)
                if item.get('title'):
                    if isinstance(_item, gtk.Label) \
                    and len(_item.get_label()) > OC_TEXT_WIDTH:
                        _item.set_alignment(OC_ALIGNMENT_LONG_TITLE_X,
                                            OC_ALIGNMENT_LONG_TITLE_Y)
                    else:
                        _item.set_alignment(OC_ALIGNMENT_TITLE_X,
                                            OC_ALIGNMENT_TITLE_Y)
                else:
                    if hasattr(_item, 'set_alignment'):
                        if isinstance(_item, gtk.Entry):
                            _item.set_alignment(OC_ALIGNMENT_CONTENT_X)
                        else:
                            _item.set_alignment(OC_ALIGNMENT_CONTENT_X,
                                                OC_ALIGNMENT_CONTENT_Y)
                if isinstance(_item, DetailedList):
                    hbox.set_size_request(OC_DEFAULT, OC_DETAILEDLIST_HEIGHT)
                if item.get('vhelp'):
                    hbox.set_size_request(OC_DEFAULT, item['vhelp'])
            vbox.pack_start(hbox, False, False,
                                padding=OC_PAGE_WIDGET_HPADDING)
        vbox.oc_widgets = d
        return vbox

    def _new_attr(self, attr_name, attr_value):
        """
        create a attribute 'attr_name' with value 'attr_value'
        to instance then return the attr_value
        """
        self.__setattr__(attr_name, attr_value)
        return self.__getattribute__(attr_name)

    def _handle_switch_page(self, notebook, page, page_num):
        curpage = notebook.get_nth_page(page_num)
        datautil.datas_refresh(curpage.oc_widgets)

    def _create_item(self, data):
        itype = data['type']
        label = data.get('label')
        value = data.get('value')
        item = getattr(gtk, itype)()
        item.set_size_request(OC_DEFAULT, OC_TEXT_HEIGHT)
        if value and hasattr(item, 'set_text'):
            item.set_text(value)
        elif label and hasattr(item, 'set_label'):
            item.set_label(label)
        if itype == 'Label':
            item.set_width_chars(OC_TEXT_WIDTH)
            if len(label) > OC_TEXT_WIDTH:
                item.set_line_wrap(True)
                item.set_size_request(OC_DEFAULT,
                                OC_TEXT_HEIGHT*((len(label)//OC_TEXT_WIDTH)+1))
        return item


def run():
    OcSetup(layouts)
    gtk.main()
