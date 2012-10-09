#!/usr/bin/env python

import pexpect
import sys
import gtk
from ovirtnode.ovirtfunctions import log


class PopupEntry(gtk.Dialog):

    def __init__(self, label="", title="", parent=None, flags=0, buttons=None):
        super(PopupEntry, self).__init__(title, parent, flags, buttons)
        self.hbox = gtk.HBox()
        self.label = gtk.Label(label)
        self.add_button("OK", gtk.RESPONSE_OK)
        self.entry = gtk.Entry()
        self.entry.set_visibility(False)
        self.hbox.pack_start(self.label)
        self.hbox.pack_start(self.entry)
        self.vbox.pack_start(self.hbox)
        self.set_position(gtk.WIN_POS_CENTER_ALWAYS)

    def run_and_close(self):
        self.show_all()
        resp_id = self.run()
        text = self.entry.get_text()
        self.destroy()
        return text


def runcmd(cmd):
    child = pexpect.spawn(cmd, logfile=sys.stdout)
    while True:
        i = child.expect([
            pexpect.TIMEOUT,
            'Are you sure you want to continue connecting',
            'Enter passphrase for key',
            'Permission denied, please try again.',
            'password: ',
            'Permission denied',
            pexpect.EOF])
        if i == 0:
            # TIMEOUT.
            return
        elif i == 1:
            child.sendline('yes')
        elif i == 2:
            child.send("\r")
        elif i == 3:
            # wrong password, but you can still try AGAIN.
            password = PopupEntry(
                label='Password:',
                title="Wrong Password?").run_and_close()
        elif i == 4:
            password = PopupEntry(label='Password:').run_and_close()
            child.sendline(password)
        elif i == 5:
            # LOGIN FAILED
            return
        elif i == 6:
            # LOGIN SUCCEED.
            return child
        else:
            log(
                "run cmd error i = %d\n before:%s\nafter:%s" %
                (i, child.before, child.after))
