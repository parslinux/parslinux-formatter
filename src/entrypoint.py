#!/usr/bin/env python3
"""ParsLinux Formatter — Ana Giriş Noktası ve Arayüz Seçici (entrypoint.py).

Sistemde GTK4 ve Libadwaita mevcutsa modern arayüzü (ModernWindow.py),
aksi takdirde klasik GTK3 arayüzünü (Main.py) başlatır.
"""

import os
import sys

# src dizinini sys.path başına ekle
src_dir = os.path.dirname(os.path.abspath(__file__))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)


def main():
    try:
        import gi
        gi.require_version("Gtk", "4.0")
        gi.require_version("Adw", "1")
        from ModernWindow import Application as Gtk4App
        app = Gtk4App()
        sys.exit(app.run(sys.argv))
    except Exception:
        import gi
        gi.require_version("Gtk", "3.0")
        from Main import app as gtk3_app
        sys.exit(gtk3_app.run(sys.argv))


if __name__ == "__main__":
    main()
