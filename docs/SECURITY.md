# ParsLinux Formatter — Güvenlik Modeli ve Politikası (SECURITY.md)

Bu belge, **ParsLinux Formatter** uygulamasının ayrıcalık ayrımı (privilege separation), sistem diski koruma filtreleri, PolicyKit yetkilendirme modeli ve güvenlik açıklarını bildirme prosedürlerini açıklar.

---

## 🛡️ 1. Güvenlik Tasarım İlkeleri

ParsLinux Formatter, düşük seviyeli blok depolama aygıtlarına yazım ve formatlama gerçekleştirdiği için sistem güvenliğinde en üst düzeyde hassasiyet gözetilerek tasarlanmıştır:

1. **Ayrıcalıkların Ayrılması (Privilege Separation):**
   - Kullanıcı Arayüzü (GTK3 / GTK4) ve CLI istemcisi sıradan kullanıcı (`UID >= 1000`) izinleriyle çalışır.
   - Grafik arayüzü asla `sudo` veya `pkexec` ile doğrudan başlatılmaz.
   - Sadece arka plandaki biçimlendirme ve bölümleme motoru (`USBFormatter.py`) Polkit mekanizması (`pkexec`) ile kontrollü şekilde root yetkisine yükseltilir.

2. **Sıfır Güven Doğrulama (Zero-Trust Input Validation):**
   - Ön yüzden kök motora aktarılan hiçbir aygıt adı sorgulanmadan kabul edilmez.
   - Kök yetkili motor, aygıt yolunu `/proc/mounts`, `/sys/block` ve `lsblk` üzerinden bağımsız olarak doğrular.

3. **5 Kademeli Sistem Diski Kilidi:**
   - Kök dizini (`/`) barındıran fiziksel disk veya bölüntü.
   - Önyükleme bölümleri (`/boot`, `/boot/efi`).
   - Kullanıcı ana dizini (`/home`) veya sistem veri alanları (`/var`, `/usr`).
   - Takas alanı (`swap`) olarak kullanılan bölüntüler.
   - Dahili NVMe ve SATA ana sistem diskleri.
   Yukarıdaki kriterlerden herhangi birine uyan aygıtlar **asla** biçimlendirilemez ve işlem anında durdurulur (`Exit Code 3`).

4. **İşbirlikçi İptal ve Donanım Bütünlüğü:**
   - Tehlikeli `kill -9` veya yetkisiz `pkexec kill` çağrıları yerine, işlem iptal edildiğinde yazma döngüsü güvenle kırılır, `os.fsync()` ve `sync` çağrılarak blok tamponları diske boşaltılır ve aygıt tutarlı bir durumda bırakılır.

---

## 🔒 2. PolicyKit (Polkit) Yapılandırması

Uygulama, `/usr/share/polkit-1/actions/tr.org.parslinux.pkexec.parslinux-formatter.policy` altında tanımlanan yetki kuralını kullanır:

- **Eylem (Action ID):** `tr.org.parslinux.pkexec.parslinux-formatter`
- **Açıklama:** "Format USB storage devices" (USB Depolama Aygıtlarını Biçimlendir)
- **Yetki Seviyesi:** `auth_admin` (Yönetici şifresi gerektirir)
- **Korumalı İkili:** `/usr/share/parslinux/parslinux-formatter/src/USBFormatter.py`

---

## 🚨 3. Güvenlik Açığı Bildirimi

ParsLinux Formatter projesinde tespit ettiğiniz güvenlik açıklarını lütfen herkese açık sorun (Issue) kayıtlarında paylaşmayınız. 

- **E-posta Bildirimi:** [security@pars.org.tr](mailto:security@pars.org.tr) veya [dev@pars.org.tr](mailto:dev@pars.org.tr)
- **PGP/GPG:** İsteğe bağlı olarak şifrelenmiş e-posta gönderebilirsiniz.
- **Yanıt Süresi:** Güvenlik bildirimlerine en geç 48 saat içerisinde geri dönüş sağlanır ve yama süreci başlatılır.
