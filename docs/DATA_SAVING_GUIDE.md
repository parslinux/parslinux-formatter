# ParsLinux Formatter — Veri Güvenliği ve Disk Koruma Kılavuzu (DATA_SAVING_GUIDE.md)

Bu kılavuz, **ParsLinux Formatter** uygulamasının yanlış disk seçimlerini önlemek, veri kayıplarını engellemek ve donanım düzeyinde yazma bütünlüğünü sağlamak için uyguladığı güvenlik katmanlarını ele almaktadır.

---

## 1. Veri Kaybını Önleyen 5 Kademeli Güvenlik Kalkanı

Bir disk biçimlendirme aracında en kritik güvenlik riski, kullanıcının ana işletim sisteminin kurulu olduğu dahili sabit diski veya harici yedekleme diskini yanlışlıkla hedef olarak seçmesidir. ParsLinux Formatter, bunu engellemek için **5 bağımsız çekirdek düzeyinde doğrulama** uygular:

```
[Kullanıcı Hedef Diski Seçer]
         │
         ▼
[1. Basamak] Yol Doğrulaması (Yalnızca /dev/sd* veya mmcblk* izinli, sembolik bağlar engellenir)
         │  (Başarılı)
         ▼
[2. Basamak] Veriyolu Denetimi (/sys/block/*/device yolu 'usb' içermeli; dahili NVMe/SATA yasak)
         │  (Başarılı)
         ▼
[3. Basamak] Kritik Mount Koruması (/, /boot, /home, /var vb. sistem bağları mutlak kilitli)
         │  (Başarılı)
         ▼
[4. Basamak] Aktif Takas (Swap) Koruması (/proc/swaps taranır, aktif swap diski engellenir)
         │  (Başarılı)
         ▼
[5. Basamak] Kullanıcı Teyidi & Çift Aşamalı Güvenlik Uyarısı (Model, boyut ve silinecek etiket doğrulaması)
         │  (Kullanıcı Onayı)
         ▼
[Biçimlendirme Başlatılır]
```

---

## 2. Sıfırlama (Zero-Fill) ve Güvenli Silme

Standart hızlı biçimlendirme sadece dosya sistemi indeksini ve bölüm tablosunu siler. Eski verilerin kurtarılamamasını isteyen kullanıcılar için:
- **Tam Sıfırlama (`--fill`):** 4 MiB dinamik tamponlarla diskin her sektörüne `0x00` baytları yazılır.
- **Donanımsal TRIM (`--trim`):** SSD ve modern flash belleklerde `blkdiscard` komutu ile hücreler fabrika durumuna sıfırlanır.

---

## 3. Kullanıcıya Yönelik En İyi Uygulamalar (Best Practices)

1. **Doğru Diski Doğrulayın:** Biçimlendirme onay kutusunda görüntülenen aygıt adını (`/dev/sdb`), disk etiketini ve boyutunu mutlaka kontrol edin.
2. **Yedeklerinizi Alın:** Biçimlendirme işlemi başladığında disk üzerindeki tüm bölümler silinir; işlem geri alınamaz.
3. **İşlem Bitmeden Diski Çıkarmayın:** İlerleme durumu %100 olduktan ve sistem "Biçimlendirme tamamlandı, diski güvenle çıkarabilirsiniz" bildirimini verdikten sonra aygıtı sökün.
