#!/usr/bin/env python
# encoding=utf-8

import sys
from ocsetup.ocsetup_ui import WidgetBase, EMPTY_LINE, _
from ocsetup.ocsetup_ui_widgets import ButtonList
from ocsetup.wrapper_ovirtfunctions import PluginBase
class Plugin(PluginBase):
    def __init__(self):
        PluginBase.__init__(self, "License")

    def form(self):
        title = WidgetBase('imvp_title', 'Label', _('IMVP Confiuration'),
                            title=True)
        management_server_addr = WidgetBase('imvp_server_addr', 'Label',
                                            _('Management Server'))
        management_server_addr_val = WidgetBase('imvp_server_addr_val',
                                            'Entry')
        management_server_port = WidgetBase('imvp_serve_port', 'Label',
                                            _('Management Server Port'))
        management_server_port_val = WidgetBase('imvp_serve_port_val', 'Entry', '',
                                            '8443')
        connect_to_imvp = WidgetBase('connect_to_imvp', 'CheckButton',
                        _('Connect to IMVP Manager and Validate Certificate'))
        set_pw = WidgetBase('set_imvp_pw', 'Label', _('Set IMVP Admin Password'),
                            title=True)
        imvp_pw = WidgetBase('imvp_pw', 'Label', 'Password')
        imvp_pwe = WidgetBase('imvp_pw', 'Entry')
        imvp_cpw = WidgetBase('imvp_cpw', 'Label', 'Confirm Password')
        imvp_cpwe = WidgetBase('imvp_cpw', 'Entry')
        imvp_changes = WidgetBase('imvp_changes', ButtonList, '',
                            params={'labels':[_('Apply'), _('Reset')]})
        return [ 'imvp', 'IMVP',
                    [
                        (title,),
                        (management_server_addr, management_server_addr_val),
                        (management_server_port, management_server_port_val),
                        (connect_to_imvp,),
                        (set_pw,),
                        (imvp_pw, imvp_pwe),
                        (imvp_cpw, imvp_cpwe),
                        (WidgetBase('__', 'Label', vhelp=140),),
                        (imvp_changes,),
                    ]
              ]

    def action(self):
        pass

def get_plugin():
    p = Plugin()
    return p.form()
