# ParsLinux Formatter — Sürüm Yönetim Politikası (VERSION.md)

Bu belge, **ParsLinux Formatter** projesinin sürümleme politikasını ve sürüm bilgilerinin kod tabanındaki merkezi eşzamanlama noktalarını tanımlar.

---

## 📌 1. Semantik Sürümleme (SemVer 2.0.0)

Projede `MAJOR.MINOR.PATCH` formatı izlenir:

- **MAJOR (Ana Sürüm):** Geriye dönük uyumsuz köklü mimari değişimler veya büyük sürüm atlamaları (Örn: `1.0.0`).
- **MINOR (Alt Sürüm):** Geriye dönük uyumlu yeni özellikler (Örn: Yeni bir dosya sistemi veya UI modu eklenmesi).
- **PATCH (Yama Sürümü):** Geriye dönük uyumlu hata düzeltmeleri ve güvenlik yamaları.

---

## 📍 2. Geçerli Sürüm Bilgisi

- **Mevcut Sürüm:** `1.0.0`
- **Yayın Tarihi:** 13 Ekim 2026
- **Kod Adı:** *Leopar Biçimlendirici (Pars Leopard Formatter)*

---

## 🔄 3. Sürüm Senkronizasyon Noktaları

Yeni bir sürüm yayınlanırken aşağıdaki dosyalar eşzamanlı olarak güncellenmelidir:

1. `src/__version__`: Tek satırlık yalın sürüm metni (`1.0.0`).
2. `debian/changelog`: Paket sürüm başlığı (`parslinux-formatter (1.0.0) unstable; urgency=medium`).
3. `setup.py`: Paketleyici sürüm meta verisi.
4. `src/ModernWindow.py`: `APP_VERSION = "1.0.0"`.
5. `src/CLI.py`: `get_version()` fonksiyonu dönüş değeri.
6. `tr.org.parslinux.Formatter.metainfo.xml`: `<release version="1.0.0" date="2026-10-13">`.
