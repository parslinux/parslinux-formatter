#!/usr/bin/env python3
"""ParsLinux Formatter - setup.py paket kurulum yapılandırması."""

import os
import subprocess
from setuptools import setup, find_packages

changelog = "debian/changelog"
version = "1.0.0"
if os.path.exists(changelog):
    try:
        head = open(changelog).readline()
        version = head.split("(")[1].split(")")[0]
    except Exception:
        pass

# src/__version__ dosyasını güncelle
with open("src/__version__", "w") as f:
    f.write(version)


def create_mo_files():
    podir = "po"
    mo = []
    if not os.path.isdir(podir):
        return mo

    for po in os.listdir(podir):
        if po.endswith(".po"):
            lang = po.split(".po")[0]
            os.makedirs(f"{podir}/{lang}/LC_MESSAGES", exist_ok=True)
            mo_file = f"{podir}/{lang}/LC_MESSAGES/parslinux-formatter.mo"
            msgfmt_cmd = f"msgfmt {podir}/{po} -o {mo_file}"
            subprocess.call(msgfmt_cmd, shell=True)
            mo.append(
                (
                    f"/usr/share/locale/{lang}/LC_MESSAGES",
                    [mo_file],
                )
            )
    return mo


data_files = [
    ("/usr/share/applications/", ["tr.org.parslinux.formatter.desktop"]),
    (
        "/usr/share/parslinux/parslinux-formatter/assets",
        [
            "assets/parslinux-formatter.svg",
            "assets/main.svg",
            "assets/disk.svg",
            "assets/format.svg",
        ],
    ),
    (
        "/usr/share/parslinux/parslinux-formatter/src",
        [
            "src/entrypoint.py",
            "src/Main.py",
            "src/MainWindow.py",
            "src/ModernWindow.py",
            "src/CLI.py",
            "src/USBFormatter.py",
            "src/USBDeviceManager.py",
            "src/Utils.py",
            "src/__version__",
        ],
    ),
    ("/usr/share/parslinux/parslinux-formatter/ui", ["ui/MainWindow.glade"]),
    (
        "/usr/share/polkit-1/actions",
        ["tr.org.parslinux.pkexec.parslinux-formatter.policy"],
    ),
    (
        "/usr/share/icons/hicolor/scalable/apps/",
        ["assets/parslinux-formatter.svg"],
    ),
    (
        "/usr/share/metainfo",
        ["tr.org.parslinux.Formatter.metainfo.xml"],
    ),
] + create_mo_files()

setup(
    name="ParsLinux Formatter",
    version=version,
    packages=find_packages(),
    scripts=["bin/parslinux-formatter", "bin/parslinux-formatter-cli", "bin/parslinux-formatter-gtk4"],
    install_requires=["PyGObject"],
    data_files=data_files,
    author="ParsLinux Developers",
    author_email="dev@pars.org.tr",
    description="High-performance, secure USB drive formatting utility for ParsLinux.",
    license="GPLv3",
    keywords="usb format fat32 ntfs exfat ext4 btrfs f2fs pars parslinux",
    url="https://github.com/parslinux/parslinux-formatter",
)
