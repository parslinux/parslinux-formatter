# ParsLinux Formatter — Kurulum ve Derleme Kılavuzu (INSTALL.md)

Bu belge, **ParsLinux Formatter** uygulamasının bağımlılıklarını, kaynak koddan kurulumunu, Debian paketi oluşturulmasını ve sistemden kaldırılmasını açıklar.

---

## 📦 1. Sistem Gereksinimleri ve Bağımlılıklar

ParsLinux Formatter'ın tüm dosya sistemlerini biçimlendirebilmesi ve arayüzlerinin sorunsuz çalışabilmesi için aşağıdaki paketler gereklidir:

### Debian / Ubuntu / ParsLinux:
```bash
sudo apt update
sudo apt install -y \
    python3 \
    python3-gi \
    python3-pyudev \
    python3-setuptools \
    gir1.2-gtk-3.0 \
    gir1.2-gtk-4.0 \
    gir1.2-adwaita-1 \
    dosfstools \
    ntfs-3g \
    exfatprogs \
    e2fsprogs \
    btrfs-progs \
    xfsprogs \
    f2fs-tools \
    cryptsetup \
    parted \
    util-linux \
    policykit-1
```

---

## 🚀 2. Kaynak Koddan Kurulum (setup.py)

Depoyu yerel sisteme kurmak için kök dizinde:

```bash
# Dil çevirilerini (.mo) derleyip sisteme kur
sudo python3 setup.py install --prefix=/usr
```

Kurulum sonrasında aşağıdaki çalıştırılabilir dosyalar `/usr/bin/` altına eklenecektir:
- `parslinux-formatter` (Klasik GTK3 arayüzü)
- `parslinux-formatter-gtk4` (Modern GTK4 / Libadwaita arayüzü)
- `parslinux-formatter-cli` (Bağımsız komut satırı arayüzü)

---

## 📦 3. Debian (.deb) Paketi Üretimi

Resmi `.deb` paketini derlemek için:

```bash
# Gerekli derleme araçlarını kur
sudo apt install -y debhelper-compat dh-python

# Paketi derle
dpkg-buildpackage -us -uc -b

# Üretilen paketi kur (bir üst dizinde oluşur)
sudo dpkg -i ../parslinux-formatter_1.0.0_all.deb
```

---

## 🗑️ 4. Sistemden Kaldırma (Uninstall)

```bash
# Debian paketi olarak kurulduysa:
sudo apt remove --purge parslinux-formatter

# setup.py ile kurulduysa:
sudo rm -rf /usr/share/parslinux/parslinux-formatter
sudo rm -f /usr/bin/parslinux-formatter*
sudo rm -f /usr/share/applications/tr.org.parslinux.formatter.desktop
sudo rm -f /usr/share/polkit-1/actions/tr.org.parslinux.pkexec.parslinux-formatter.policy
```
