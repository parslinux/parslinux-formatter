# ParsLinux Formatter — Çeviri ve Yerelleştirme Kılavuzu (TRANSLATION_GUIDE.md)

Bu belge, **ParsLinux Formatter** uygulamasının çok dilli yapısını, gettext `.po` / `.pot` dosyalarını ve yeni bir dil ekleme adımlarını açıklar.

---

## 🌍 1. Desteklenen Diller

- **Türkçe (`tr`)** — Birincil Geliştirme Dili
- **İngilizce (`en`)** — Uluslararası Referans Dili

---

## 🛠️ 2. Yeni Bir Dil Ekleme

Yeni bir dil eklemek için (örneğin Almanca - `de`):

1. Ana çeviri şablonunu (`po/parslinux-formatter.pot`) kopyalayın:
   ```bash
   cp po/parslinux-formatter.pot po/de.po
   ```

2. `po/de.po` dosyasını Poedit veya herhangi bir metin düzenleyici ile açarak dizgileri çevirin.

3. Başlık alanındaki dil kodunu (`Language: de`) güncelleyin.

---

## 🔄 3. Çevirileri Güncelleme (update-translations.sh)

Kaynak kodda yeni bir metin eklendiğinde tüm `.po` dosyalarını güncellemek için:

```bash
./update-translations.sh
```

Bu betik:
- `src/*.py` ve `ui/MainWindow.glade` dosyalarındaki tüm çevrilebilir metinleri tarar.
- `po/parslinux-formatter.pot` dosyasını yeniler.
- Mevcut tüm `.po` dosyalarıyla birleştirir (`msgmerge`).

---

## 📦 4. İkili Çeviri Dosyalarını (.mo) Derleme

Çevirileri ikili gettext formatına dönüştürmek için:

```bash
python3 setup.py build
```
Derlenen `.mo` dosyaları `/usr/share/locale/<dil>/LC_MESSAGES/parslinux-formatter.mo` altına yerleştirilir.
