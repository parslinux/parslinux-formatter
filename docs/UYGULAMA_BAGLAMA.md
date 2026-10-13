# ParsLinux Formatter — Masaüstü ve Sistem Uygulama Bağlama Kılavuzu (UYGULAMA_BAGLAMA.md)

Bu doküman, **ParsLinux Formatter** uygulamasının Linux masaüstü ortamlarına (GNOME, KDE Plasma, XFCE, Cinnamon), dosya yöneticilerine (Nautilus, Nemo, Thunar, Dolphin) ve sistem menülerine nasıl entegre edildiğini açıklar.

---

## 1. Masaüstü Giriş Dosyası (.desktop)

Uygulamanın sistem menüsünde görünmesini ve arama çubuğunda "Biçimlendirici" veya "Format" yazıldığında çıkmasını sağlayan dosya:
`/usr/share/applications/tr.org.parslinux.formatter.desktop`

```ini
[Desktop Entry]
Name=ParsLinux Formatter
Name[tr]=ParsLinux USB Biçimlendirici
GenericName=USB Formatter
GenericName[tr]=USB Biçimlendirici
Comment=Format USB flash drives easily and securely
Comment[tr]=USB bellekleri kolay ve güvenli biçimde biçimlendirin
Exec=parslinux-formatter-gtk4 %f
Icon=parslinux-formatter
Terminal=false
Type=Application
Categories=System;X-Pars-Apps;Utility;
Keywords=usb;format;fat32;ntfs;exfat;ext4;btrfs;f2fs;luks;
StartupNotify=true
StartupWMClass=tr.org.parslinux.formatter
```

---

## 2. Dosya Yöneticisi Sağ Tık (Context Menu) Entegrasyonu

Bir USB belleğe dosya yöneticisinde sağ tıklandığında doğrudan "Biçimlendir..." seçeneğinin çıkması için:

### GNOME Files (Nautilus) & Nemo:
`/usr/share/nautilus-python/extensions/` veya `~/.local/share/nautilus-python/extensions/parslinux_formatter.py` betiği:

```python
import os
from gi.repository import Nautilus, GObject

class FormatterExtension(GObject.GObject, Nautilus.MenuProvider):
    def get_file_items(self, *args):
        files = args[-1]
        if len(files) == 1 and files[0].is_directory() and files[0].get_uri().startswith("file:///media"):
            item = Nautilus.MenuItem(
                name="ParsLinuxFormatter::format",
                label="ParsLinux ile Biçimlendir...",
                tip="Bu sürücüyü ParsLinux Formatter ile biçimlendirin"
            )
            item.connect('activate', lambda _: os.system("parslinux-formatter-gtk4 &"))
            return [item]
        return []
```

---

## 3. PolicyKit Yetkilendirme Entegrasyonu

Kullanıcı arayüzü doğrudan root hakları istemez; biçimlendirme tetiklendiğinde sistem şifresi modalı PolicyKit tarafından açılır:
`/usr/share/polkit-1/actions/tr.org.parslinux.pkexec.parslinux-formatter.policy`
