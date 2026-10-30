#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Şifre Sızıntı Kontrolü
======================
Şifrelerinin nereden/nasıl çalınmış olabileceğini anlamana yardım eden,
sadece KENDİ hesapların ve KENDİ bilgisayarın için savunma amaçlı araç.

Ne yapar?
  1) Şifre kontrolü: Bir şifrenin bilinen veri sızıntılarında geçip geçmediğini
     söyler. Şifren internete GÖNDERİLMEZ (k-anonimlik: sadece SHA-1 özetinin
     ilk 5 karakteri gönderilir).
  2) E-posta kontrolü: E-postanın hangi sitelerin sızıntısında olduğunu listeler
     (Have I Been Pwned API anahtarı varsa). Yoksa kontrol edebileceğin
     ücretsiz siteyi açar.
  3) Bilgisayar taraması: Şifre çalan virüslerin (infostealer) sık bıraktığı
     izlere bakar: açılışta otomatik çalışan programlar, tarayıcı eklentileri,
     İndirilenler klasöründeki "crack/hile/keygen" tarzı dosyalar.
  4) Sonunda ne yapman gerektiğini sade bir dille anlatır.

Hiçbir şeyi silmez, değiştirmez. Sadece okur ve rapor verir.
Sadece Python 3.8+ gerekir, ek kurulum gerekmez.

Kullanım:
  python sifre_kontrol.py            (menülü mod)
  python sifre_kontrol.py --tara     (sadece bilgisayar taraması)
"""

import getpass
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

SISTEM = platform.system()  # "Windows", "Darwin" (macOS), "Linux"
EV = Path.home()
UA = "SifreSizintiKontrolu/1.0"

# Infostealer'ların en sık bulaştığı dosya adları (hile, crack, "bedava" yazılım).
SUPHELI_ADLAR = re.compile(
    r"(crack|keygen|patch|activator|kms|loader|cheat|hile|hack|injector|aimbot|"
    r"wallhack|free[-_ ]?robux|robux|vbucks|skin[-_ ]?changer|executor|spoofer|"
    r"setup[-_ ]?pass|password[-_ ]?1234|full[-_ ]?version|premium[-_ ]?free|"
    r"discord[-_ ]?nitro|nitro[-_ ]?gen|mod[-_ ]?menu)",
    re.IGNORECASE,
)
CALISTIRILABILIR = {".exe", ".scr", ".msi", ".bat", ".cmd", ".ps1", ".vbs", ".js",
                    ".jar", ".lnk", ".hta", ".com", ".pif", ".dmg", ".pkg", ".app",
                    ".sh", ".appimage", ".zip", ".rar", ".7z"}
# Şüpheli konumlar: normal programlar buradan açılışta pek çalışmaz.
SUPHELI_YOLLAR = re.compile(
    r"(\\temp\\|/tmp/|\\appdata\\local\\temp|\\appdata\\roaming\\[^\\]+\.exe|"
    r"\\users\\public\\|\\programdata\\[^\\]+\.exe|downloads|indirilenler|"
    r"powershell.*(-enc|-e |hidden|downloadstring|iex)|mshta|wscript|cscript|"
    r"rundll32.*\\appdata|regsvr32.*http|curl .*\| *sh|base64)",
    re.IGNORECASE,
)

bulgular = []  # (seviye, başlık, açıklama)


def renk(metin, kod):
    if SISTEM == "Windows" and not os.environ.get("WT_SESSION"):
        return metin
    return f"\033[{kod}m{metin}\033[0m"


def kirmizi(m): return renk(m, "91")
def sari(m): return renk(m, "93")
def yesil(m): return renk(m, "92")
def kalin(m): return renk(m, "1")


def bulgu(seviye, baslik, aciklama=""):
    bulgular.append((seviye, baslik, aciklama))
    isaret = {"YUKSEK": kirmizi("[!!]"), "ORTA": sari("[ !]"), "BILGI": "[ i]"}[seviye]
    print(f"  {isaret} {baslik}")
    if aciklama:
        print(f"       {aciklama}")


def http_get(url, basliklar=None, zaman_asimi=15):
    istek = urllib.request.Request(url, headers={"User-Agent": UA, **(basliklar or {})})
    with urllib.request.urlopen(istek, timeout=zaman_asimi) as yanit:
        return yanit.status, yanit.read().decode("utf-8", "replace")


# ---------------------------------------------------------------------------
# 1) Şifre kontrolü (Pwned Passwords, k-anonimlik)
# ---------------------------------------------------------------------------
def sifre_sizdi_mi(sifre):
    """Şifrenin kaç kez sızıntıda görüldüğünü döndürür. Şifre gönderilmez."""
    ozet = hashlib.sha1(sifre.encode("utf-8")).hexdigest().upper()
    on, son = ozet[:5], ozet[5:]
    _, govde = http_get(f"https://api.pwnedpasswords.com/range/{on}",
                        {"Add-Padding": "true"})
    for satir in govde.splitlines():
        parca, _, sayi = satir.partition(":")
        if parca.strip() == son:
            return int(sayi.strip() or 0)
    return 0


def sifre_kontrol_menusu():
    print(kalin("\n== Şifre kontrolü =="))
    print("Şifren ekranda görünmez ve internete gönderilmez.")
    print("Boş bırakıp Enter'a basınca bu bölümden çıkarsın.\n")
    while True:
        sifre = getpass.getpass("Kontrol edilecek şifre: ")
        if not sifre:
            return
        try:
            sayi = sifre_sizdi_mi(sifre)
        except Exception as hata:
            print(kirmizi(f"  İnternete bağlanılamadı: {hata}"))
            continue
        if sayi:
            bulgu("YUKSEK", f"Bu şifre sızıntılarda {sayi:,} kez görülmüş!".replace(",", "."),
                  "Bu şifreyi kullandığın HER hesapta hemen değiştir. "
                  "Saldırganlar sızmış şifreleri başka sitelerde de dener.")
        else:
            print(yesil("  [ok] Bu şifre bilinen sızıntılarda yok."))
            print("       (Yine de birden fazla sitede aynı şifreyi kullanma.)")
        del sifre


# ---------------------------------------------------------------------------
# 2) E-posta kontrolü (Have I Been Pwned)
# ---------------------------------------------------------------------------
def eposta_kontrol_menusu():
    print(kalin("\n== E-posta sızıntı kontrolü =="))
    eposta = input("E-posta adresin: ").strip()
    if not eposta:
        return
    anahtar = os.environ.get("HIBP_API_KEY", "").strip()
    if not anahtar:
        print("\n  Hangi sitelerden sızdığını otomatik görmek için Have I Been Pwned")
        print("  API anahtarı gerekiyor (ücretli). Anahtarın yoksa sorun değil:")
        print("  aynı bilgiyi ücretsiz olarak sitesinde görebilirsin.")
        url = "https://haveibeenpwned.com/account/" + urllib.parse.quote(eposta)
        print(f"  -> {url}")
        if input("  Tarayıcıda açayım mı? (e/h): ").strip().lower().startswith("e"):
            webbrowser.open(url)
        print("\n  İpucu: Sonuçta çıkan her site, şifrenin sızmış olabileceği bir yerdir.")
        print("  O sitelerde kullandığın şifreyi başka nerede kullandıysan oralarda da değiştir.")
        return
    url = ("https://haveibeenpwned.com/api/v3/breachedaccount/"
           + urllib.parse.quote(eposta) + "?truncateResponse=false")
    try:
        _, govde = http_get(url, {"hibp-api-key": anahtar})
        ihlaller = json.loads(govde)
    except urllib.error.HTTPError as hata:
        if hata.code == 404:
            print(yesil("  [ok] Bu e-posta bilinen sızıntılarda yok."))
            return
        print(kirmizi(f"  Hata: {hata.code} {hata.reason}"))
        return
    except Exception as hata:
        print(kirmizi(f"  İnternete bağlanılamadı: {hata}"))
        return
    ihlaller.sort(key=lambda i: i.get("BreachDate", ""), reverse=True)
    bulgu("YUKSEK", f"E-postan {len(ihlaller)} sızıntıda bulundu:")
    for i in ihlaller:
        veriler = ", ".join(i.get("DataClasses", [])[:5])
        print(f"       - {i.get('Title')} ({i.get('BreachDate')}): {veriler}")
    print("\n  En yeni tarihli ve 'Passwords' içeren sızıntılar en büyük şüphelilerdir.")


# ---------------------------------------------------------------------------
# 3) Bilgisayar taraması
# ---------------------------------------------------------------------------
def komut(args):
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=60,
                              errors="replace").stdout
    except Exception:
        return ""


def baslangic_ogeleri():
    """(isim, komut/yol) listesi döndürür."""
    ogeler = []
    if SISTEM == "Windows":
        import winreg
        anahtarlar = [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Run"),
        ]
        for kok, yol in anahtarlar:
            try:
                with winreg.OpenKey(kok, yol) as k:
                    i = 0
                    while True:
                        try:
                            ad, deger, _ = winreg.EnumValue(k, i)
                        except OSError:
                            break
                        ogeler.append((f"Kayıt defteri: {ad}", str(deger)))
                        i += 1
            except OSError:
                pass
        klasorler = [
            Path(os.environ.get("APPDATA", "")) / r"Microsoft\Windows\Start Menu\Programs\Startup",
            Path(os.environ.get("PROGRAMDATA", "")) / r"Microsoft\Windows\Start Menu\Programs\StartUp",
        ]
        for klasor in klasorler:
            if klasor.is_dir():
                for f in klasor.iterdir():
                    if f.name.lower() != "desktop.ini":
                        ogeler.append((f"Başlangıç klasörü: {f.name}", str(f)))
        # Microsoft dışındaki zamanlanmış görevler
        cikti = komut(["schtasks", "/query", "/fo", "CSV", "/v"])
        basliklar = None
        import csv
        for satir in csv.reader(cikti.splitlines()):
            if not satir:
                continue
            if basliklar is None or satir[0] == basliklar[0]:
                basliklar = satir
                continue
            kayit = dict(zip(basliklar, satir))
            ad = kayit.get("TaskName", satir[1] if len(satir) > 1 else "")
            calisan = kayit.get("Task To Run", "")
            if ad.startswith("\\Microsoft\\") or not calisan:
                continue
            ogeler.append((f"Zamanlanmış görev: {ad}", calisan))
    elif SISTEM == "Darwin":
        for klasor in [EV / "Library/LaunchAgents", Path("/Library/LaunchAgents"),
                       Path("/Library/LaunchDaemons")]:
            if klasor.is_dir():
                for f in klasor.glob("*.plist"):
                    try:
                        icerik = f.read_text(errors="replace")
                    except Exception:
                        icerik = ""
                    programlar = re.findall(r"<string>([^<]*/[^<]*)</string>", icerik)
                    ogeler.append((f"LaunchAgent: {f.name}", " ".join(programlar[:3]) or str(f)))
        cikti = komut(["osascript", "-e",
                       'tell application "System Events" to get the path of every login item'])
        for yol in cikti.strip().split(", "):
            if yol:
                ogeler.append(("Giriş öğesi", yol))
    else:
        for klasor in [EV / ".config/autostart", Path("/etc/xdg/autostart")]:
            if klasor.is_dir():
                for f in klasor.glob("*.desktop"):
                    try:
                        exe = re.search(r"^Exec=(.*)$", f.read_text(errors="replace"), re.M)
                    except Exception:
                        exe = None
                    ogeler.append((f"Autostart: {f.name}", exe.group(1) if exe else str(f)))
        for satir in komut(["crontab", "-l"]).splitlines():
            if satir.strip() and not satir.lstrip().startswith("#"):
                ogeler.append(("Cron görevi", satir.strip()))
        kullanici_servis = EV / ".config/systemd/user"
        if kullanici_servis.is_dir():
            for f in kullanici_servis.glob("*.service"):
                ogeler.append((f"Kullanıcı servisi: {f.name}", str(f)))
    return ogeler


def baslangic_tara():
    print(kalin("\n-- Bilgisayar açılınca otomatik çalışan programlar --"))
    ogeler = baslangic_ogeleri()
    supheli = 0
    for ad, deger in ogeler:
        if SUPHELI_YOLLAR.search(deger) or SUPHELI_ADLAR.search(ad + " " + deger):
            supheli += 1
            bulgu("YUKSEK", f"Şüpheli otomatik başlatma: {ad}",
                  f"Çalıştırdığı: {deger[:200]}")
    if not supheli:
        print(yesil(f"  [ok] {len(ogeler)} öğe incelendi, belirgin şüpheli bulunmadı."))
    print("\n  Tam liste (tanımadığın bir şey var mı bak):")
    for ad, deger in ogeler:
        print(f"    - {ad}  ->  {deger[:120]}")
    if not ogeler:
        print("    (boş)")


def tarayici_profilleri():
    """(tarayıcı adı, eklenti klasörü) listesi."""
    sonuc = []
    if SISTEM == "Windows":
        yerel = Path(os.environ.get("LOCALAPPDATA", ""))
        tabanlar = {
            "Chrome": yerel / "Google/Chrome/User Data",
            "Edge": yerel / "Microsoft/Edge/User Data",
            "Brave": yerel / "BraveSoftware/Brave-Browser/User Data",
            "Opera": Path(os.environ.get("APPDATA", "")) / "Opera Software/Opera Stable",
            "Opera GX": Path(os.environ.get("APPDATA", "")) / "Opera Software/Opera GX Stable",
            "Yandex": yerel / "Yandex/YandexBrowser/User Data",
        }
    elif SISTEM == "Darwin":
        destek = EV / "Library/Application Support"
        tabanlar = {
            "Chrome": destek / "Google/Chrome",
            "Edge": destek / "Microsoft Edge",
            "Brave": destek / "BraveSoftware/Brave-Browser",
            "Opera": destek / "com.operasoftware.Opera",
            "Yandex": destek / "Yandex/YandexBrowser",
        }
    else:
        tabanlar = {
            "Chrome": EV / ".config/google-chrome",
            "Chromium": EV / ".config/chromium",
            "Edge": EV / ".config/microsoft-edge",
            "Brave": EV / ".config/BraveSoftware/Brave-Browser",
            "Opera": EV / ".config/opera",
        }
    for ad, taban in tabanlar.items():
        if not taban.is_dir():
            continue
        if (taban / "Extensions").is_dir():  # Opera profili doğrudan tabandadır
            sonuc.append((ad, taban / "Extensions"))
        for profil in taban.iterdir():
            if (profil / "Extensions").is_dir() and (profil / "Preferences").exists():
                sonuc.append((f"{ad} ({profil.name})", profil / "Extensions"))
    return sonuc


def eklenti_adi(klasor, manifest):
    ad = manifest.get("name", "?")
    if ad.startswith("__MSG_"):
        anahtar = ad[6:-2]
        for dil in ("tr", "en", "en_US"):
            mesaj = klasor / "_locales" / dil / "messages.json"
            if mesaj.exists():
                try:
                    veri = json.loads(mesaj.read_text(encoding="utf-8-sig", errors="replace"))
                    for k, v in veri.items():
                        if k.lower() == anahtar.lower():
                            return v.get("message", ad)
                except Exception:
                    pass
    return ad


TEHLIKELI_IZINLER = {"<all_urls>", "cookies", "webRequest", "webRequestBlocking",
                     "debugger", "proxy", "clipboardRead", "nativeMessaging",
                     "declarativeNetRequest", "management", "*://*/*", "http://*/*",
                     "https://*/*"}


def eklenti_tara():
    print(kalin("\n-- Tarayıcı eklentileri --"))
    print("  Kötü eklentiler oturum çerezlerini çalarak şifre olmadan bile hesabına girebilir.")
    profiller = tarayici_profilleri()
    toplam = 0
    for tarayici, klasor in profiller:
        for eklenti in klasor.iterdir():
            surumler = sorted([d for d in eklenti.iterdir() if d.is_dir()]) if eklenti.is_dir() else []
            if not surumler:
                continue
            manifest_yolu = surumler[-1] / "manifest.json"
            try:
                manifest = json.loads(manifest_yolu.read_text(encoding="utf-8-sig", errors="replace"))
            except Exception:
                continue
            ad = eklenti_adi(surumler[-1], manifest)
            if eklenti.name in ("nmmhkkegccagdldgiimedpiccmgmieda", "ghbmnnjooekpmoecnnnilnnbdlolhkhi",
                                "pkedcjkdefgpdelpbcmbmeomcjbeemfm"):  # Google'ın kendi bileşenleri
                continue
            toplam += 1
            izinler = set(map(str, manifest.get("permissions", []) + manifest.get("host_permissions", [])))
            riskli = sorted(izinler & TEHLIKELI_IZINLER)
            bilgi = f"{tarayici}: {ad}  (kimlik: {eklenti.name})"
            if "update_url" in manifest and "google.com" not in manifest.get("update_url", "") \
                    and "microsoft.com" not in manifest.get("update_url", ""):
                bulgu("YUKSEK", f"Resmi mağaza DIŞINDAN kurulmuş eklenti: {bilgi}",
                      "Bunu sen kurmadıysan hemen kaldır.")
            elif {"cookies", "<all_urls>"} <= izinler or ("cookies" in izinler and riskli):
                bulgu("ORTA", f"Çerezlere ve tüm sitelere erişebilen eklenti: {bilgi}",
                      f"İzinler: {', '.join(riskli)}. Tanımıyorsan/kullanmıyorsan kaldır.")
            else:
                print(f"    - {bilgi}" + (f"  [izinler: {', '.join(riskli)}]" if riskli else ""))
    if not profiller:
        print("  Chromium tabanlı tarayıcı bulunamadı.")
    else:
        print(f"\n  Toplam {toplam} eklenti incelendi.")
    # Firefox
    if SISTEM == "Windows":
        ff = Path(os.environ.get("APPDATA", "")) / "Mozilla/Firefox/Profiles"
    elif SISTEM == "Darwin":
        ff = EV / "Library/Application Support/Firefox/Profiles"
    else:
        ff = EV / ".mozilla/firefox"
    if ff.is_dir():
        for profil in ff.iterdir():
            ext = profil / "extensions.json"
            if not ext.exists():
                continue
            try:
                veri = json.loads(ext.read_text(encoding="utf-8", errors="replace"))
            except Exception:
                continue
            for a in veri.get("addons", []):
                if a.get("location") != "app-profile":
                    continue
                ad = (a.get("defaultLocale") or {}).get("name", a.get("id"))
                if a.get("signedState", 2) <= 0:
                    bulgu("YUKSEK", f"Firefox: imzasız eklenti: {ad}", "Tanımıyorsan kaldır.")
                else:
                    print(f"    - Firefox ({profil.name}): {ad}")


def indirilenler_tara():
    print(kalin("\n-- İndirilen dosyalar (crack / hile / 'bedava' program) --"))
    print("  Şifre çalan virüslerin 1 numaralı kaynağı: crack'li oyun/program, hile, keygen.")
    klasorler = [EV / "Downloads", EV / "İndirilenler", EV / "Desktop", EV / "Masaüstü"]
    if SISTEM == "Windows":
        klasorler.append(Path(os.environ.get("USERPROFILE", EV)) / "OneDrive/Desktop")
    sinir = time.time() - 365 * 24 * 3600
    bulunan = 0
    gorulen = set()
    for klasor in klasorler:
        if not klasor.is_dir() or klasor.resolve() in gorulen:
            continue
        gorulen.add(klasor.resolve())
        for kok, dizinler, dosyalar in os.walk(klasor):
            if kok.count(os.sep) - str(klasor).count(os.sep) >= 2:
                dizinler[:] = []
            for ad in dosyalar:
                yol = Path(kok) / ad
                uzanti = yol.suffix.lower()
                if uzanti not in CALISTIRILABILIR:
                    continue
                try:
                    zaman = yol.stat().st_mtime
                except OSError:
                    continue
                if zaman < sinir:
                    continue
                if SUPHELI_ADLAR.search(ad) or re.search(r"\.(pdf|docx?|jpg|png|mp4)\.(exe|scr|js|vbs)$", ad, re.I):
                    bulunan += 1
                    tarih = time.strftime("%d.%m.%Y", time.localtime(zaman))
                    bulgu("YUKSEK", f"Şüpheli dosya ({tarih}): {yol}",
                          "Bunu çalıştırdıysan şifrelerin büyük ihtimalle buradan çalındı. "
                          "Tarih, şifrelerin ilk çalındığı zamanla uyuşuyor mu bak.")
    if not bulunan:
        print(yesil("  [ok] Son 1 yılda adı şüpheli çalıştırılabilir dosya bulunmadı."))


def windows_ek_kontroller():
    print(kalin("\n-- Windows güvenlik durumu --"))
    cikti = komut(["powershell", "-NoProfile", "-Command",
                   "Get-MpComputerStatus | Select-Object AntivirusEnabled,RealTimeProtectionEnabled | ConvertTo-Json"])
    try:
        durum = json.loads(cikti)
        if not durum.get("RealTimeProtectionEnabled"):
            bulgu("YUKSEK", "Windows Defender gerçek zamanlı koruma KAPALI.",
                  "Bazı virüsler Defender'ı kapatır. Ayarlar > Windows Güvenliği'nden aç.")
        else:
            print(yesil("  [ok] Windows Defender gerçek zamanlı koruma açık."))
    except Exception:
        print("  Defender durumu okunamadı (başka antivirüs kullanıyor olabilirsin).")
    hariç = komut(["powershell", "-NoProfile", "-Command",
                   "(Get-MpPreference).ExclusionPath -join ';'"]).strip()
    if hariç and "N/A" not in hariç and "admin" not in hariç.lower():
        bulgu("ORTA", "Defender'da taranmayan (hariç tutulan) klasörler var:",
              f"{hariç[:300]}  -- Bunları sen eklemediysen virüs eklemiş olabilir.")


def bilgisayar_tara():
    print(kalin(f"\n== Bilgisayar taraması ({SISTEM}) =="))
    print("Hiçbir şey silinmez, sadece okunur.")
    baslangic_tara()
    eklenti_tara()
    indirilenler_tara()
    if SISTEM == "Windows":
        windows_ek_kontroller()


# ---------------------------------------------------------------------------
# 4) Özet ve öneriler
# ---------------------------------------------------------------------------
def ozet():
    print(kalin("\n================ ÖZET ================"))
    yuksek = [b for b in bulgular if b[0] == "YUKSEK"]
    orta = [b for b in bulgular if b[0] == "ORTA"]
    print(f"  Ciddi bulgu: {len(yuksek)}   Dikkat edilecek: {len(orta)}\n")
    bilgisayar_supheli = any("dosya" in b[1] or "otomatik" in b[1] or "eklenti" in b[1].lower()
                             or "Defender" in b[1] for b in yuksek + orta)
    if bilgisayar_supheli:
        print(kirmizi("  Şifrelerin büyük ihtimalle BİLGİSAYARINDAKİ bir virüs tarafından çalınıyor."))
        print("  Bu durumda şifre değiştirmek tek başına yetmez; virüs yeni şifreyi de çalar.")
        print("  Doğru sıra:")
        print("   1. Önce bilgisayarı temizle: şüpheli dosya/eklentiyi kaldır, Windows Defender")
        print("      'Çevrimdışı tarama' veya Malwarebytes ile tam tarama yap.")
        print("      En garantisi: önemli dosyalarını yedekleyip Windows'u sıfırdan kurmak.")
        print("   2. SONRA, temiz bir cihazdan (ör. telefonundan) tüm şifrelerini değiştir.")
        print("      Önce e-posta, sonra Discord/Steam/Instagram/banka.")
        print("   3. Her hesapta 'tüm oturumlardan çıkış yap' de. Virüs çerez çaldıysa")
        print("      şifre değişse bile oturum açık kalabilir.")
    else:
        print("  Bilgisayarda belirgin bir virüs izi bulunmadı. En olası diğer sebepler:")
        print("   - Aynı şifreyi birçok sitede kullanmak (bir site sızınca hepsi açılır).")
        print("   - Sahte giriş sayfası (phishing): 'bedava Nitro/skin/takipçi' linkleri,")
        print("     sahte 'hesabın kapatılacak' mesajları.")
        print("   - Şifreyi tarayıcıya kaydedip başka birinin bilgisayarını kullanmak.")
        print("   - Ekran paylaşımı / 'şu kodu bana söyle' dolandırıcılığı.")
    print(kalin("\n  Her durumda yapman gerekenler:"))
    print("   - Her siteye FARKLI şifre. Bunu hatırlamak için şifre yöneticisi kullan")
    print("     (Bitwarden ücretsiz, iyi bir seçenek).")
    print("   - İki adımlı doğrulamayı (2FA) aç; SMS yerine Google/Microsoft Authenticator.")
    print("   - E-posta hesabın her şeyin anahtarı: ona en güçlü şifreyi ve 2FA'yı ver.")
    print("   - Gmail için: myaccount.google.com/security -> 'Cihazlarınız' bölümünden")
    print("     tanımadığın cihazları çıkar. Hesabında kurulu yönlendirme kurallarına da bak.")
    print("   - Crack'li program, hile, 'bedava' yazılım indirme.\n")


def menu():
    print(kalin("Şifre Sızıntı Kontrolü"))
    print("Sadece kendi hesapların ve kendi bilgisayarın için kullan.\n")
    while True:
        print("\n  1) Bir şifrem sızmış mı?")
        print("  2) E-postam hangi sızıntılarda var?")
        print("  3) Bilgisayarımda şifre çalan virüs izi var mı? (tarama)")
        print("  4) Hepsini yap")
        print("  0) Bitir ve özeti göster")
        secim = input("Seçimin: ").strip()
        if secim == "1":
            sifre_kontrol_menusu()
        elif secim == "2":
            eposta_kontrol_menusu()
        elif secim == "3":
            bilgisayar_tara()
        elif secim == "4":
            bilgisayar_tara()
            eposta_kontrol_menusu()
            sifre_kontrol_menusu()
        elif secim == "0":
            ozet()
            break


if __name__ == "__main__":
    try:
        if "--tara" in sys.argv:
            bilgisayar_tara()
            ozet()
        else:
            menu()
    except KeyboardInterrupt:
        print("\nÇıkıldı.")
    if SISTEM == "Windows":
        try:
            input("\nKapatmak için Enter'a bas...")
        except Exception:
            pass
