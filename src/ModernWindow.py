#!/usr/bin/env python3
"""ParsLinux Formatter — GTK4 & Libadwaita Modern Kullanıcı Arayüzü (ModernWindow.py).

GNOME HIG uyumlu AdwClamp düzenleri, AdwPreferencesGroup, AdwComboRow,
AdwEntryRow, AdwPasswordEntryRow, dinamik açık/koyu tema desteği,
ve eşzamanlı olmayan (asynchronous) gerçek zamanlı ilerleme monitörü sunar.
"""

import math
import os
import signal
import subprocess
import sys
import threading
import time
from typing import List, Optional

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gio, GLib, Gtk

import USBDeviceManager
from USBDeviceManager import validate_usb_drive, DriveError
from Utils import format_duration, format_size

APP_ID = "tr.org.parslinux.formatter.gtk4"
APP_NAME = "ParsLinux Formatter"
APP_VERSION = "1.0.0"

SUPPORTED_FS_LIST = [
    ("FAT32", "FAT32 — Evrensel Uyumluluk (Tüm Cihazlar & TV/Oto Teypleri)"),
    ("EXFAT", "exFAT — Modern Flash Bellekler & 4 GB+ Dosyalar"),
    ("NTFS", "NTFS — Windows ve Büyük Dosya Depolama"),
    ("EXT4", "EXT4 — Standart GNU/Linux Günlüklemeli Dosya Sistemi"),
    ("F2FS", "F2FS — Flash Depolama Dostu (Hızlı & Uzun Ömürlü)"),
    ("BTRFS", "BTRFS — Yeni Nesil Anlık Görüntü & Sıkıştırma"),
    ("XFS", "XFS — Yüksek I/O Verimli Kurumsal Dosya Sistemi"),
]


def find_formatter_script() -> str:
    """USBFormatter.py yolunu bulur."""
    candidates = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "USBFormatter.py"),
        "/usr/share/parslinux/parslinux-formatter/src/USBFormatter.py",
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return "USBFormatter.py"


class ModernWindow(Adw.ApplicationWindow):
    """Ana GTK4 / Libadwaita Biçimlendirici Penceresi."""

    def __init__(self, app: Adw.Application, initial_device: Optional[str] = None):
        super().__init__(application=app, title=APP_NAME)
        self.set_default_size(680, 720)

        self.initial_device = initial_device
        self.device_list: List[List] = []
        self.worker_process: Optional[subprocess.Popen] = None
        self.cancelled = False

        self.setup_ui()
        self.refresh_devices()

    def setup_ui(self):
        # Ana Dikey Kutu
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(main_box)

        # Başlık Çubuğu (HeaderBar)
        header = Adw.HeaderBar()
        title_widget = Adw.WindowTitle(
            title=APP_NAME,
            subtitle="Modern USB Depolama Biçimlendirici",
        )
        header.set_title_widget(title_widget)

        # Tema Değiştirici Buton
        theme_btn = Gtk.Button(icon_name="night-light-symbolic")
        theme_btn.set_tooltip_text("Koyu / Açık Tema Değiştir")
        theme_btn.connect("clicked", self.toggle_theme)
        header.pack_start(theme_btn)

        # Aygıtları Yenile Butonu
        refresh_btn = Gtk.Button(icon_name="view-refresh-symbolic")
        refresh_btn.set_tooltip_text("USB Aygıtlarını Yenile")
        refresh_btn.connect("clicked", lambda _: self.refresh_devices())
        header.pack_start(refresh_btn)

        # Hakkında Butonu
        about_btn = Gtk.Button(icon_name="help-about-symbolic")
        about_btn.set_tooltip_text("Uygulama Hakkında")
        about_btn.connect("clicked", self.show_about_dialog)
        header.pack_end(about_btn)

        main_box.append(header)

        # Bildirim Katmanı (Toast Overlay)
        self.toast_overlay = Adw.ToastOverlay()
        main_box.append(self.toast_overlay)

        # Sayfa Yığını (Stack)
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.toast_overlay.set_child(self.stack)

        # --- SAYFA 1: Yapılandırma Ekranı ---
        config_scroll = Gtk.ScrolledWindow()
        config_clamp = Adw.Clamp(maximum_size=620, tightening_threshold=500)
        config_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        config_box.set_margin_top(20)
        config_box.set_margin_bottom(28)
        config_box.set_margin_start(16)
        config_box.set_margin_end(16)
        config_clamp.set_child(config_box)
        config_scroll.set_child(config_clamp)
        self.stack.add_named(config_scroll, "config")

        # 1. Grup: Hedef Depolama Birimi
        dev_group = Adw.PreferencesGroup(
            title="1. Hedef Depolama Aygıtı",
            description="Biçimlendirmek istediğiniz çıkarılabilir USB depolama birimini seçin.",
        )
        self.dev_combo = Adw.ComboRow(title="USB Bellek")
        self.dev_model = Gtk.StringList()
        self.dev_combo.set_model(self.dev_model)
        self.dev_combo.connect("notify::selected", self.on_device_selected)
        dev_group.add(self.dev_combo)
        config_box.append(dev_group)

        # 2. Grup: Dosya Sistemi ve Etiket
        fs_group = Adw.PreferencesGroup(
            title="2. Dosya Sistemi ve Birim Bilgileri",
            description="Kullanım amacınıza uygun dosya sistemini ve disk adını belirleyin.",
        )

        self.fs_combo = Adw.ComboRow(title="Dosya Sistemi")
        self.fs_model = Gtk.StringList()
        for _, desc in SUPPORTED_FS_LIST:
            self.fs_model.append(desc)
        self.fs_combo.set_model(self.fs_model)
        fs_group.add(self.fs_combo)

        self.label_entry = Adw.EntryRow(title="Birim Etiketi (Disk Adı)")
        self.label_entry.set_show_apply_button(False)
        fs_group.add(self.label_entry)
        config_box.append(fs_group)

        # 3. Grup: Gelişmiş Biçimlendirme Seçenekleri
        adv_group = Adw.PreferencesGroup(
            title="3. Gelişmiş Güvenlik ve Bölümleme Seçenekleri",
            description="Bölümleme tablosu türü, tam silme ve donanımsal şifreleme ayarları.",
        )

        self.gpt_switch = Adw.SwitchRow(
            title="Modern GPT Bölümleme Tablosu",
            subtitle="Standart MBR (DOS) yerine modern UEFI uyumlu GPT tablosu kullanır.",
        )
        adv_group.add(self.gpt_switch)

        self.fill_switch = Adw.SwitchRow(
            title="Tam Sıfırlama (Zero-Fill)",
            subtitle="Diskin tamamına sıfırlar yazar (4 MiB yüksek hızlı tampon, geri döndürülemez silme).",
        )
        adv_group.add(self.fill_switch)

        self.trim_switch = Adw.SwitchRow(
            title="Donanımsal TRIM (blkdiscard)",
            subtitle="SSD ve modern USB belleklerde blokları anında donanımsal olarak sıfırlar.",
        )
        adv_group.add(self.trim_switch)

        # LUKS Şifreleme Genişleticisi
        self.crypt_expander = Adw.ExpanderRow(
            title="LUKS2 Donanımsal Disk Şifreleme",
            subtitle="USB belleğinizi güçlü parola korumalı şifreli bir depoya dönüştürür.",
        )
        self.crypt_expander.set_show_enable_switch(True)
        self.crypt_expander.set_enable_expansion(False)

        self.pass_entry = Adw.PasswordEntryRow(title="Şifreleme Parolası")
        self.pass_confirm = Adw.PasswordEntryRow(title="Parolayı Tekrar Girin")
        self.crypt_expander.add_row(self.pass_entry)
        self.crypt_expander.add_row(self.pass_confirm)
        adv_group.add(self.crypt_expander)

        config_box.append(adv_group)

        # Başlat Butonu
        self.start_btn = Gtk.Button(label="Diski Biçimlendir...")
        self.start_btn.add_css_class("suggested-action")
        self.start_btn.add_css_class("pill")
        self.start_btn.set_size_request(-1, 50)
        self.start_btn.connect("clicked", self.on_start_clicked)
        config_box.append(self.start_btn)

        # --- SAYFA 2: Biçimlendirme İlerleme Ekranı ---
        progress_clamp = Adw.Clamp(maximum_size=580)
        progress_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        progress_box.set_margin_top(48)
        progress_box.set_margin_bottom(36)
        progress_box.set_margin_start(16)
        progress_box.set_margin_end(16)
        progress_clamp.set_child(progress_box)

        # Başlık Durum Sayfası
        self.prog_status = Adw.StatusPage(
            icon_name="drive-harddisk-symbolic",
            title="Disk Biçimlendiriliyor...",
            description="Lütfen işlem tamamlanana kadar USB diski çıkarmayın.",
        )
        progress_box.append(self.prog_status)

        # İlerleme Çubuğu
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_show_text(True)
        self.progress_bar.set_size_request(-1, 24)
        progress_box.append(self.progress_bar)

        # Hız ve Kalan Süre Etiketi
        self.speed_label = Gtk.Label(label="Hazırlanıyor...")
        self.speed_label.add_css_class("dim-label")
        progress_box.append(self.speed_label)

        # İptal Butonu
        self.cancel_btn = Gtk.Button(label="İşlemi İptal Et")
        self.cancel_btn.add_css_class("destructive-action")
        self.cancel_btn.add_css_class("pill")
        self.cancel_btn.connect("clicked", self.on_cancel_clicked)
        progress_box.append(self.cancel_btn)

        self.stack.add_named(progress_clamp, "formatting")

        # --- SAYFA 3: Tamamlandı / Başarı Ekranı ---
        success_clamp = Adw.Clamp(maximum_size=560)
        success_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        success_box.set_margin_top(64)
        success_box.set_margin_bottom(36)
        success_clamp.set_child(success_box)

        self.success_status = Adw.StatusPage(
            icon_name="emblem-ok-symbolic",
            title="Biçimlendirme Başarıyla Tamamlandı!",
            description="USB diskiniz hazırlandı. Aygıtı güvenle kullanabilir veya çıkarabilirsiniz.",
        )
        success_box.append(self.success_status)

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        btn_box.set_halign(Gtk.Align.CENTER)

        new_btn = Gtk.Button(label="Yeni Birim Biçimlendir")
        new_btn.add_css_class("suggested-action")
        new_btn.add_css_class("pill")
        new_btn.connect("clicked", lambda _: self.reset_to_config())
        btn_box.append(new_btn)

        exit_btn = Gtk.Button(label="Kapat")
        exit_btn.add_css_class("pill")
        exit_btn.connect("clicked", lambda _: self.get_application().quit())
        btn_box.append(exit_btn)

        success_box.append(btn_box)
        self.stack.add_named(success_clamp, "success")

    def toggle_theme(self, button):
        """Koyu ve Açık tema arasında dinamik geçiş yapar."""
        style_mgr = Adw.StyleManager.get_default()
        if style_mgr.get_dark():
            style_mgr.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
        else:
            style_mgr.set_color_scheme(Adw.ColorScheme.FORCE_DARK)

    def show_about_dialog(self, button):
        """Hakkında diyaloğunu görüntüler."""
        about = Adw.AboutDialog(
            application_name=APP_NAME,
            application_icon="parslinux-formatter",
            developer_name="ParsLinux Geliştirici Topluluğu",
            version=APP_VERSION,
            copyright="© 2026 ParsLinux Geliştiricileri",
            license_type=Gtk.License.GPL_3_0,
            website="https://pars.org.tr",
            issue_url="https://github.com/parslinux/parslinux-formatter/issues",
        )
        about.present(self)

    def refresh_devices(self):
        """Sistemdeki çıkarılabilir USB diskleri tarar ve ComboRow'u günceller."""
        self.device_list = USBDeviceManager.get_usb_devices()
        
        # StringList'i temizle ve yeniden doldur
        while self.dev_model.get_n_items() > 0:
            self.dev_model.remove(0)

        if not self.device_list:
            self.dev_model.append("Hiçbir çıkarılabilir USB depolama aygıtı bulunamadı")
            self.dev_combo.set_sensitive(False)
            self.start_btn.set_sensitive(False)
            return

        self.dev_combo.set_sensitive(True)
        self.start_btn.set_sensitive(True)

        selected_idx = 0
        for idx, dev in enumerate(self.device_list):
            entry_str = f"/dev/{dev[0]} — {dev[1]} ({dev[2]})"
            self.dev_model.append(entry_str)
            if self.initial_device and dev[0] in self.initial_device:
                selected_idx = idx

        self.dev_combo.set_selected(selected_idx)

    def on_device_selected(self, combo, param):
        """Kullanıcı farklı bir disk seçtiğinde tetiklenir."""
        pass

    def on_start_clicked(self, button):
        """Biçimlendirme öncesi doğrulama ve onay modalını açar."""
        idx = self.dev_combo.get_selected()
        if idx >= len(self.device_list) or not self.device_list:
            return

        target_dev = self.device_list[idx]
        block_name = target_dev[0]
        fs_type, _ = SUPPORTED_FS_LIST[self.fs_combo.get_selected()]
        label = self.label_entry.get_text().strip()

        # Etiket uzunluk kontrolleri
        if fs_type == "FAT32" and len(label) > 11:
            self.show_toast("FAT32 birim etiketi en fazla 11 karakter olabilir.")
            return
        elif fs_type == "NTFS" and len(label) > 32:
            self.show_toast("NTFS birim etiketi en fazla 32 karakter olabilir.")
            return
        elif fs_type == "EXT4" and len(label) > 16:
            self.show_toast("EXT4 birim etiketi en fazla 16 karakter olabilir.")
            return

        # Şifreleme kontrolü
        crypt_pass = None
        if self.crypt_expander.get_enable_expansion():
            p1 = self.pass_entry.get_text()
            p2 = self.pass_confirm.get_text()
            if not p1:
                self.show_toast("Lütfen LUKS2 şifreleme parolası belirleyin.")
                return
            if p1 != p2:
                self.show_toast("Girilen şifreleme parolaları eşleşmiyor!")
                return
            if len(p1) < 4:
                self.show_toast("Parola en az 4 karakter uzunluğunda olmalıdır.")
                return
            crypt_pass = p1

        # 5 Kademeli Güvenlik Doğrulaması
        try:
            validate_usb_drive(block_name)
        except DriveError as err:
            self.show_error_dialog("Güvenlik Engeli", str(err))
            return

        # Onay Modalı (Adw.MessageDialog)
        body_text = (
            f"Seçilen disk: /dev/{block_name} ({target_dev[1]} — {target_dev[2]})\n"
            f"Dosya Sistemi: {fs_type}\n"
            f"Birim Etiketi: '{label or 'Belirtilmedi'}'\n\n"
            "⚠️ DİKKAT: Bu işlem hedef disk üzerindeki TÜM bölümleri ve verileri "
            "geri döndürülemez biçimde kalıcı olarak silecektir!"
        )

        dialog = Adw.MessageDialog(
            heading="Diski Biçimlendirmek İstiyor Musunuz?",
            body=body_text,
        )
        dialog.set_transient_for(self)
        dialog.add_response("cancel", "Vazgeç")
        dialog.add_response("format", "Evet, Biçimlendir")
        dialog.set_response_appearance("format", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_default_response("cancel")

        def _on_response(dlg, response):
            if response == "format":
                self.start_formatting_process(block_name, fs_type, label, crypt_pass)

        dialog.connect("response", _on_response)
        dialog.present()

    def start_formatting_process(self, block_name: str, fs_type: str, label: str, crypt: Optional[str]):
        """pkexec ile USBFormatter.py sürecini arka planda başlatır."""
        script_path = find_formatter_script()
        cmd_args = [
            "--device", block_name,
            "--type", fs_type,
            "--label", label,
        ]
        if self.fill_switch.get_active():
            cmd_args.append("--fill")
        if self.trim_switch.get_active():
            cmd_args.append("--trim")
        if self.gpt_switch.get_active():
            cmd_args.append("--gpt")
        if crypt:
            cmd_args += ["--crypt", crypt]

        if os.geteuid() == 0:
            cmd = [sys.executable, script_path] + cmd_args
        else:
            cmd = ["pkexec", script_path] + cmd_args

        self.cancelled = False
        self.progress_bar.set_fraction(0.0)
        self.speed_label.set_text("Biçimlendirme başlatılıyor...")
        self.stack.set_visible_child_name("formatting")

        try:
            self.worker_process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
        except Exception as exc:
            self.show_error_dialog("Çalıştırma Hatası", str(exc))
            self.stack.set_visible_child_name("config")
            return

        # Arka plan okuyucu iş parçacığı
        thread = threading.Thread(target=self._monitor_worker, daemon=True)
        thread.start()

    def _monitor_worker(self):
        proc = self.worker_process
        if not proc or not proc.stdout:
            return

        while True:
            line = proc.stdout.readline()
            if not line:
                break
            line = line.strip()
            if not line:
                continue

            if line.startswith("PROGRESS"):
                parts = line.split("|")
                if len(parts) >= 3:
                    try:
                        written = int(parts[1])
                        total = int(parts[2])
                        speed = float(parts[3]) if len(parts) > 3 else 0.0
                        eta = parts[4] if len(parts) > 4 else "--:--"
                        fraction = (written / total) if total > 0 else 0.0
                        GLib.idle_add(self._update_progress_ui, fraction, speed, eta, written, total)
                    except (ValueError, IndexError):
                        pass

        ret = proc.wait()
        GLib.idle_add(self._on_worker_finished, ret)

    def _update_progress_ui(self, fraction: float, speed: float, eta: str, written: int, total: int):
        self.progress_bar.set_fraction(fraction)
        self.progress_bar.set_text(f"%{int(fraction * 100)}")
        if total > 0:
            self.speed_label.set_text(
                f"{format_size(written)} / {format_size(total)} | {speed:.1f} MB/s | Kalan: {eta}"
            )
        return False

    def _on_worker_finished(self, returncode: int):
        if self.cancelled:
            self.stack.set_visible_child_name("config")
            self.show_toast("İşlem kullanıcı tarafından iptal edildi.")
            return False

        if returncode == 0:
            self.stack.set_visible_child_name("success")
            self.send_desktop_notification("Biçimlendirme Tamamlandı", "USB belleğinizi güvenle kullanabilirsiniz.")
        elif returncode in (126, 127):
            self.stack.set_visible_child_name("config")
            self.show_toast("PolicyKit yetkilendirmesi reddedildi veya yapılamadı.")
        else:
            stderr_msg = ""
            if self.worker_process and self.worker_process.stderr:
                stderr_msg = self.worker_process.stderr.read().strip()
            self.stack.set_visible_child_name("config")
            self.show_error_dialog("Biçimlendirme Başarısız", stderr_msg or "İşlem sırasında bir hata oluştu.")

        return False

    def on_cancel_clicked(self, button):
        """Kullanıcı iptal butonuna bastığında stdin borusunu kapatır."""
        self.cancelled = True
        if self.worker_process and self.worker_process.stdin and not self.worker_process.stdin.closed:
            try:
                self.worker_process.stdin.close()
            except OSError:
                pass
        self.speed_label.set_text("İptal ediliyor, tamponlar boşaltılıyor...")

    def reset_to_config(self):
        """Başarı ekranından yapılandırma ekranına döner."""
        self.label_entry.set_text("")
        self.pass_entry.set_text("")
        self.pass_confirm.set_text("")
        self.refresh_devices()
        self.stack.set_visible_child_name("config")

    def show_toast(self, message: str):
        toast = Adw.Toast(title=message)
        self.toast_overlay.add_toast(toast)

    def show_error_dialog(self, title: str, message: str):
        dlg = Adw.MessageDialog(heading=title, body=message)
        dlg.set_transient_for(self)
        dlg.add_response("ok", "Tamam")
        dlg.present()

    def send_desktop_notification(self, title: str, body: str):
        try:
            notif = Gio.Notification.new(title)
            notif.set_body(body)
            notif.set_icon(Gio.ThemedIcon(name="parslinux-formatter"))
            self.get_application().send_notification("format-complete", notif)
        except Exception:
            pass


class Application(Adw.Application):
    """ParsLinux Formatter Gtk/Adw Uygulama Sınıfı."""

    def __init__(self):
        super().__init__(
            application_id=APP_ID,
            flags=Gio.ApplicationFlags.HANDLES_OPEN | Gio.ApplicationFlags.NON_UNIQUE,
        )
        self.window = None

    def do_activate(self):
        if not self.window:
            self.window = ModernWindow(self)
        self.window.present()

    def do_open(self, files, n_files, hint):
        dev_path = None
        if n_files > 0:
            dev_path = files[0].get_path()
        if not self.window:
            self.window = ModernWindow(self, initial_device=dev_path)
        self.window.present()


if __name__ == "__main__":
    app = Application()
    sys.exit(app.run(sys.argv))
