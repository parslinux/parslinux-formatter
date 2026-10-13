# ParsLinux Formatter — Katkı Sağlama Kılavuzu (CONTRIBUTING.md)

ParsLinux Formatter projesine katkıda bulunmak istediğiniz için teşekkür ederiz! Açık kaynak topluluğunun gücüne inanıyor ve her türlü katkıyı (kod, çeviri, hata bildirimi, dokümantasyon) memnuniyetle karşılıyoruz.

---

## 🛠️ 1. Geliştirme Ortamı Kurulumu

1. Depoyu forklayın ve yerel makinenize klonlayın:
   ```bash
   git clone https://github.com/parslinux/parslinux-formatter.git
   cd parslinux-formatter
   ```

2. Geliştirme bağımlılıklarını yükleyin:
   ```bash
   sudo apt install -y python3-gi gir1.2-gtk-3.0 gir1.2-gtk-4.0 gir1.2-adwaita-1 python3-pyudev
   ```

3. Yeni bir özellik dalı (feature branch) oluşturun:
   ```bash
   git checkout -b ozellik/yeni-dosya-sistemi
   ```

---

## 📏 2. Kodlama ve Kalite Standartları

- **Python Standartları:** PEP 8 standartlarına uygun temiz kod yazın.
- **Tip İpuçları (Type Annotations):** Yeni fonksiyonlarda mümkün mertebe tip tanımlamalarını ekleyin.
- **Güvenlik Önceliği:** Doğrudan sistem diski erişimi yapan kodlarda 5 kademeli güvenlik kontrollerini asla atlatmayın.
- **Commit Mesajları:** [Conventional Commits](https://www.conventionalcommits.org/) standardını takip edin:
  - `feat: Add F2FS formatting support`
  - `fix: Prevent crash on disconnected drive during fill`
  - `docs: Update CLI reference with trim option`

---

## 🧪 3. Test ve Doğrulama

Değişikliklerinizi göndermeden önce mutlaka birim testlerini ve duman testlerini çalıştırın:

```bash
python3 -m unittest discover tests/ -v
./parslinux-formatter-cli --list
```

---

## 📬 4. Pull Request (PR) Süreci

1. Dalınızı GitHub üzerindeki deponuza gönderin:
   ```bash
   git push origin ozellik/yeni-dosya-sistemi
   ```
2. Ana depoya (`parslinux/parslinux-formatter`) yönelik bir Pull Request açın.
3. PR açıklamasında yaptığınız değişiklikleri, motivasyonunuzu ve test sonuçlarınızı özetleyin.
