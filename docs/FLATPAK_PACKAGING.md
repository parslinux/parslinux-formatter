# ParsLinux Formatter — Flatpak ve Flathub Paketleme Kılavuzu (FLATPAK_PACKAGING.md)

Bu kılavuz, **ParsLinux Formatter** uygulamasının Flatpak olarak derlenmesini, sandbox (kum havuzu) izinlerinin yapılandırılmasını, yerel test süreçlerini ve Flathub dağıtımını açıklar.

---

## 1. Flatpak İzin Mimarisi (`finish-args`)

Doğrudan blok aygıtlarına (`/dev/sd*`) erişen ve PolicyKit yetkilendirmesi kullanan disk biçimlendirme araçları aşağıdaki izinlere ihtiyaç duyar:

- `--device=all`: Doğrudan blok cihazlarına (`/dev/sd*`, `/dev/mmcblk*`) düşük seviyeli erişim.
- `--filesystem=/run/udev:ro`: Udev veritabanını okuyarak USB aygıt etiketlerini ve modellerini tespit etmek.
- `--talk-name=org.freedesktop.PolicyKit1`: Root yetkisi gereken biçimlendirme işlemleri için Polkit yetkilendirmesi.
- `--system-talk-name=org.freedesktop.UDisks2`: Disk bağlantı durumlarını izlemek için UDisks2 D-Bus erişimi.
- `--socket=wayland` ve `--socket=fallback-x11`: Modern grafik arayüz desteği.

---

## 2. Flatpak Manifestosu (`tr.org.parslinux.Formatter.json`)

```json
{
  "app-id": "tr.org.parslinux.Formatter",
  "runtime": "org.gnome.Platform",
  "runtime-version": "46",
  "sdk": "org.gnome.Sdk",
  "command": "parslinux-formatter-gtk4",
  "finish-args": [
    "--device=all",
    "--filesystem=/run/udev:ro",
    "--socket=wayland",
    "--socket=fallback-x11",
    "--share=ipc",
    "--talk-name=org.freedesktop.PolicyKit1",
    "--system-talk-name=org.freedesktop.UDisks2"
  ],
  "modules": [
    {
      "name": "parslinux-formatter",
      "buildsystem": "simple",
      "build-commands": [
        "python3 setup.py install --prefix=/app"
      ],
      "sources": [
        {
          "type": "dir",
          "path": "."
        }
      ]
    }
  ]
}
```

---

## 3. Yerel Olarak Derleme ve Test Etme

```bash
# Flatpak builder ile derle ve kur
flatpak-builder --user --install --force-clean build-dir tr.org.parslinux.Formatter.json

# Uygulamayı çalıştır
flatpak run tr.org.parslinux.Formatter
```
