#!/usr/bin/python3
"""ParsLinux Formatter — Klasik GTK3 Uygulama Yaşam Döngüsü (Main.py)."""

import sys
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gio, Gtk, GLib

from MainWindow import MainWindow

APP_ID = "tr.org.parslinux.formatter"


class Application(Gtk.Application):
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            application_id=APP_ID,
            flags=Gio.ApplicationFlags.HANDLES_OPEN | Gio.ApplicationFlags.NON_UNIQUE,
            **kwargs,
        )
        self.window = None
        GLib.set_prgname(APP_ID)

    def do_activate(self):
        if not self.window:
            self.window = MainWindow(self)
        self.window.window.present()

    def do_open(self, files, filecount, hint):
        if filecount >= 1:
            file_path = files[0].get_path()
            if "/dev" in file_path:
                self.window = MainWindow(self, file_path)
            else:
                self.window = MainWindow(self)
        else:
            self.window = MainWindow(self)
        self.window.window.present()


app = Application()

if __name__ == "__main__":
    app.run(sys.argv)
