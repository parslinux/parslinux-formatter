#!/usr/bin/python3
"""ParsLinux Formatter — Klasik GTK3 Arayüz Denetleyicisi (MainWindow.py).

Geriye dönük uyumluluk için GTK3/Glade altyapısını destekler,
güvenli PolicyKit yetkilendirmesi, işbirlikçi iptal ve dinamik udev
olay dinleme mekanizması içerir.
"""

import locale
from locale import gettext as _
import os
import subprocess
import sys

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gio, Gtk

from USBDeviceManager import USBDeviceManager, validate_usb_drive, DriveError
from Utils import format_duration, format_size

APPNAME = "parslinux-formatter"
TRANSLATIONS_PATH = "/usr/share/locale"

locale.bindtextdomain(APPNAME, TRANSLATIONS_PATH)
locale.textdomain(APPNAME)


class MainWindow:
    def __init__(self, application, dev_file=None):
        self.dev_file = dev_file
        self.writerProcessPID = None
        self.writerStdin = None
        self.cancelled = False

        # Gtk Builder
        self.builder = Gtk.Builder()
        self.builder.set_translation_domain(APPNAME)

        ui_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ui", "MainWindow.glade")
        self.builder.add_from_file(ui_file)
        self.builder.connect_signals(self)

        # Window
        self.window = self.builder.get_object("window")
        self.window.set_position(Gtk.WindowPosition.CENTER)
        self.window.set_application(application)
        self.window.connect("destroy", self.onDestroy)

        self.defineComponents()

        # USB Manager
        self.usbDevice = []
        self.usbManager = USBDeviceManager()
        self.usbManager.setUSBRefreshSignal(self.listUSBDevices)
        self.listUSBDevices()

        # Sürüm ve Hakkında Bilgileri
        version = "1.0.0"
        ver_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "__version__")
        if os.path.exists(ver_file):
            try:
                with open(ver_file, "r") as f:
                    version = f.read().strip()
            except OSError:
                pass

        self.dialog_about.set_version(version)
        self.dialog_about.set_program_name(_("ParsLinux USB Formatter"))
        self.dialog_about.set_logo_icon_name("parslinux-formatter")

        if self.dialog_about.get_titlebar() is None:
            about_headerbar = Gtk.HeaderBar.new()
            about_headerbar.set_show_close_button(True)
            about_headerbar.set_title(_("Hakkında — ParsLinux USB Biçimlendirici"))
            about_headerbar.pack_start(
                Gtk.Image.new_from_icon_name("parslinux-formatter", Gtk.IconSize.LARGE_TOOLBAR)
            )
            about_headerbar.show_all()
            self.dialog_about.set_titlebar(about_headerbar)

        self.application = application
        self.cb_encrypt.connect("toggled", self.onEncryptChanged)

        self.window.show_all()

    def onEncryptChanged(self, *args):
        self.ui_revealer_encrypt.set_reveal_child(self.cb_encrypt.get_active())

    def onDestroy(self, action):
        self.window.get_application().quit()

    def defineComponents(self):
        self.stack_windows = self.builder.get_object("stack_windows")

        # Main bileşenler
        self.txt_deviceName = self.builder.get_object("txt_deviceName")
        self.txt_password = self.builder.get_object("txt_password")
        self.list_devices = self.builder.get_object("list_devices")
        self.cmb_devices = self.builder.get_object("cmb_devices")
        self.list_formats = self.builder.get_object("list_formats")
        self.cmb_formats = self.builder.get_object("cmb_formats")
        self.btn_start = self.builder.get_object("btn_start")
        self.pb_writingProgress = self.builder.get_object("pb_writingProgress")
        self.btn_cancelWriting = self.builder.get_object("btn_cancelWriting")
        self.ui_revealer_encrypt = self.builder.get_object("ui_revealer_encrypt")

        # Seçenekler
        self.cb_slowFormat = self.builder.get_object("cb_slowFormat")
        self.cb_encrypt = self.builder.get_object("cb_encrypt")

        # Diyaloglar
        self.dialog_write = self.builder.get_object("dialog_write")
        self.dialog_write.set_position(Gtk.WindowPosition.CENTER)
        self.dlg_lbl_format = self.builder.get_object("dlg_lbl_format")
        self.dlg_lbl_disk = self.builder.get_object("dlg_lbl_disk")
        self.dialog_about = self.builder.get_object("dialog_about")

    def listUSBDevices(self):
        device_list = self.usbManager.getUSBDevices()
        self.list_devices.clear()

        active_id = ""
        for device in device_list:
            # Model, Label ve Boyut
            self.list_devices.append([device[0], device[1], device[2]])
            if self.dev_file is not None and device[0] in self.dev_file:
                active_id = device[0]

        if active_id != "":
            self.cmb_devices.set_active_id(active_id)
        else:
            self.cmb_devices.set_active(0)

        self.btn_start.set_sensitive(len(device_list) > 0)

    def cmb_devices_changed(self, combobox):
        tree_iter = combobox.get_active_iter()
        if tree_iter:
            model = combobox.get_model()
            self.usbDevice = list(model[tree_iter][:3])
            self.btn_start.set_sensitive(True)
        else:
            self.btn_start.set_sensitive(False)

    def on_txt_password_icon_press(self, entry, icon_pos, event):
        entry.set_visibility(True)
        entry.set_icon_from_icon_name(icon_pos, "view-conceal-symbolic")

    def on_txt_password_icon_release(self, entry, icon_pos, event):
        entry.set_visibility(False)
        entry.set_icon_from_icon_name(icon_pos, "view-reveal-symbolic")

    def btn_start_clicked(self, button):
        if self.formatting_rule_checks():
            self.pb_writingProgress.set_visible(self.cb_slowFormat.get_active())
            self.btn_cancelWriting.set_visible(self.cb_slowFormat.get_active())
            GLib.idle_add(self.prepare_writing)

    def btn_exit_clicked(self, button):
        self.window.get_application().quit()

    def btn_write_new_file_clicked(self, button):
        self.stack_windows.set_visible_child_name("main")
        self.listUSBDevices()

    def btn_information_clicked(self, button):
        self.dialog_about.run()
        self.dialog_about.hide()

    def btn_cancelWriting_clicked(self, button):
        """İşbirlikçi iptal: stdin borusunu kapatır ve sinyal gönderir."""
        self.cancelled = True
        if self.writerStdin is not None:
            try:
                os.close(self.writerStdin)
                self.writerStdin = None
            except OSError:
                pass
        if self.writerProcessPID:
            try:
                os.kill(self.writerProcessPID, signal.SIGTERM)
            except OSError:
                pass

    def prepare_writing(self):
        selected_iter = self.cmb_formats.get_active_iter()
        if not selected_iter:
            return

        selected_format = self.cmb_formats.get_model()[selected_iter][0]
        self.dlg_lbl_format.set_markup(f"- <b>{selected_format}</b>")
        self.dlg_lbl_disk.set_markup(
            f"- <b>{self.usbDevice[1]} [ {self.usbDevice[2]} ]</b> <i>( /dev/{self.usbDevice[0]} )</i>"
        )

        response = self.dialog_write.run()
        self.dialog_write.hide()
        if response == Gtk.ResponseType.YES:
            script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "USBFormatter.py")
            process_command = [
                "pkexec",
                script_path,
                "--device",
                self.usbDevice[0],
                "--type",
                selected_format,
                "--label",
                self.txt_deviceName.get_text().strip(),
            ]
            if self.cb_slowFormat.get_active():
                process_command.append("--fill")
            if self.cb_encrypt.get_active():
                process_command += ["--crypt", self.txt_password.get_text()]

            self.cancelled = False
            self.startProcess(process_command)
            self.stack_windows.set_visible_child_name("waiting")

    def startProcess(self, params):
        self.writerProcessPID, stdin_fd, stdout_fd, _ = GLib.spawn_async(
            params,
            flags=GLib.SPAWN_SEARCH_PATH
            | GLib.SPAWN_LEAVE_DESCRIPTORS_OPEN
            | GLib.SPAWN_DO_NOT_REAP_CHILD,
            standard_input=True,
            standard_output=True,
            standard_error=True,
        )
        self.writerStdin = stdin_fd

        GLib.io_add_watch(
            GLib.IOChannel(stdout_fd),
            GLib.PRIORITY_LOW,
            GLib.IOCondition.IN | GLib.IOCondition.HUP | GLib.IOCondition.ERR,
            self.onProcessStdout,
        )
        GLib.child_watch_add(
            GLib.PRIORITY_DEFAULT, self.writerProcessPID, self.onProcessExit
        )

    def onProcessStdout(self, source, condition):
        if condition & (GLib.IOCondition.HUP | GLib.IOCondition.ERR):
            return False

        io_status, line, _, _ = source.read_line()
        if io_status != GLib.IOStatus.NORMAL or not line:
            return True

        line = line.strip()
        if line.startswith("PROGRESS"):
            parts = line.split("|")
            if len(parts) >= 3:
                try:
                    written_bytes = int(parts[1])
                    total_bytes = int(parts[2])
                    speed_mb = float(parts[3]) if len(parts) > 3 else 0.0
                    eta_str = parts[4] if len(parts) > 4 else "--:--"
                    percent = (written_bytes / total_bytes) if total_bytes > 0 else 0.0

                    self.pb_writingProgress.set_text(
                        f"{format_size(written_bytes)} / {format_size(total_bytes)} (%{int(percent * 100)}) | {speed_mb:.1f} MB/s | Kalan: {eta_str}"
                    )
                    self.pb_writingProgress.set_fraction(percent)
                except (ValueError, IndexError):
                    pass

        return True

    def onProcessExit(self, pid, status):
        self.pb_writingProgress.set_fraction(0.0)
        self.pb_writingProgress.set_text(_("Biçimlendiriliyor"))

        if self.writerStdin is not None:
            try:
                os.close(self.writerStdin)
            except OSError:
                pass
            self.writerStdin = None

        if status == 0:
            self.sendNotification(
                _("Biçimlendirme Tamamlandı."),
                _("USB depolama aygıtını güvenle çıkarabilirsiniz."),
            )
            self.stack_windows.set_visible_child_name("finished")
        elif self.cancelled or status in (15, 32256, 32512):
            self.stack_windows.set_visible_child_name("main")
        else:
            dialog = Gtk.MessageDialog(
                self.window,
                0,
                Gtk.MessageType.ERROR,
                Gtk.ButtonsType.OK,
                _("Diski biçimlendirirken bir hata oluştu."),
            )
            dialog.format_secondary_text(
                _(
                    "Lütfen USB aygıtının doğru bağlandığından, başka bir uygulama tarafından kullanılmadığından emin olun ve tekrar deneyin."
                )
            )
            dialog.run()
            dialog.destroy()
            self.stack_windows.set_visible_child_name("main")

    def sendNotification(self, title, body):
        try:
            notification = Gio.Notification.new(title)
            notification.set_body(body)
            notification.set_icon(Gio.ThemedIcon(name="parslinux-formatter"))
            self.application.send_notification("parslinux-formatter", notification)
        except Exception:
            pass

    def formatting_rule_checks(self):
        active_iter = self.cmb_formats.get_active_iter()
        if not active_iter:
            return False

        selected_format = self.cmb_formats.get_model()[active_iter][0]
        device_name = self.txt_deviceName.get_text().strip()

        if self.cb_encrypt.get_active():
            if len(self.txt_password.get_text()) == 0:
                self.show_error_dialog(
                    _("Parola gerekli."),
                    _("Lütfen LUKS şifreleme için bir parola girin."),
                )
                return False

        if selected_format == "FAT32":
            if len(device_name) > 11:
                self.show_error_dialog(
                    _("Aygıt adı çok uzun."),
                    _("FAT32 biçimi en fazla 11 karakter destekler."),
                )
                return False
            try:
                device_name.encode("cp850", errors="strict")
            except ValueError:
                self.show_error_dialog(
                    _("Geçersiz karakterler."),
                    _("FAT32 biçimi yalnızca ASCII karakterleri destekler."),
                )
                return False

        elif selected_format == "NTFS":
            if len(device_name) > 32:
                self.show_error_dialog(
                    _("Aygıt adı çok uzun."),
                    _("NTFS biçimi en fazla 32 karakter destekler."),
                )
                return False

        elif selected_format == "EXFAT":
            if len(device_name) > 15:
                self.show_error_dialog(
                    _("Aygıt adı çok uzun."),
                    _("exFAT biçimi en fazla 15 karakter destekler."),
                )
                return False

        elif selected_format == "EXT4":
            if len(device_name) > 16:
                self.show_error_dialog(
                    _("Aygıt adı çok uzun."),
                    _("EXT4 biçimi en fazla 16 karakter destekler."),
                )
                return False

        # 5 Kademeli Güvenlik Kontrolü
        if self.usbDevice:
            try:
                validate_usb_drive(self.usbDevice[0])
            except DriveError as err:
                self.show_error_dialog(
                    _("Güvenlik İhlali"),
                    str(err),
                )
                return False

        return True

    def show_error_dialog(self, primary, secondary):
        dialog = Gtk.MessageDialog(
            self.window,
            0,
            Gtk.MessageType.ERROR,
            Gtk.ButtonsType.OK,
            primary,
        )
        dialog.format_secondary_text(secondary)
        dialog.run()
        dialog.destroy()
