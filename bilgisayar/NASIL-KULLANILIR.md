# Şifre Sızıntı Kontrolü — Nasıl kullanılır?

## Kurulum
1. Python yoksa python.org'dan indir (Windows'ta kurarken **"Add Python to PATH"** kutusunu işaretle).
2. Bu klasörü bilgisayarına kopyala.

## Çalıştırma
- **Windows:** `Baslat (Windows).bat` dosyasına çift tıkla.
- **Mac / Linux:** Terminalde `python3 sifre_kontrol.py`

Menüden **4 (Hepsini yap)** seç, en sonda **0** ile özeti gör.

## Ne yapar?
| Bölüm | Ne öğrenirsin |
|---|---|
| Şifre kontrolü | Şifren daha önce bir sızıntıda çıkmış mı? Şifren internete gönderilmez. |
| E-posta kontrolü | E-postan hangi sitelerin sızıntısında var? (haveibeenpwned.com'u açar) |
| Bilgisayar taraması | Açılışta çalışan şüpheli programlar, çerez çalabilen eklentiler, crack/hile dosyaları, kapatılmış antivirüs |

Program hiçbir şeyi silmez veya değiştirmez, sadece bakar ve anlatır.

## Sonucu nasıl yorumlarım?
- **Taramada kırmızı bulgu varsa:** Şifreler büyük ihtimalle bilgisayarındaki bir virüsten çalınıyor. Önce bilgisayarı temizle, **sonra** telefonundan şifreleri değiştir. Sıra önemli, yoksa yeni şifre de çalınır.
- **Tarama temiz ama şifre/e-posta sızıntıda çıktıysa:** Sebep büyük ihtimalle aynı şifreyi birden fazla sitede kullanmak. O şifreyi her yerde değiştir.
- **Her durumda:** Her siteye farklı şifre (Bitwarden gibi bir şifre yöneticisiyle), iki adımlı doğrulama (2FA) ve her hesapta "tüm cihazlardan çıkış yap".
