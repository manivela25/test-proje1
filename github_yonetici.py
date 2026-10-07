import os
import subprocess
import sys


def cmd(command):
    """Windows, Mac ve Linux'ta encoding hatası vermeden komut çalıştırır."""
    res = subprocess.run(
        command,
        shell=True,
        text=True,
        capture_output=True,
        encoding="utf-8",  # Windows Türkçe karakter çökmesini önler
        errors="replace",  # Okunamayan karakter olursa akışı durdurmaz
    )
    return res.returncode == 0, res.stdout.strip(), res.stderr.strip()


def klasor_boyutu_hesapla(dizin):
    """Proje klasörünün toplam boyutunu MB cinsinden hesaplar."""
    toplam_byte = 0
    for root, _, files in os.walk(dizin):
        if ".git" in root:
            continue
        for f in files:
            yol = os.path.join(root, f)
            try:
                toplam_byte += os.path.getsize(yol)
            except (OSError, FileNotFoundError):
                continue
    return toplam_byte / (1024 * 1024)


def buyuk_dosya_taramasi(dizin, limit_mb=99):
    """Tekil olarak 100 MB sınırına takılacak dosyaları tarar."""
    buyukler = []
    limit_byte = limit_mb * 1024 * 1024
    for root, _, files in os.walk(dizin):
        if ".git" in root:
            continue
        for f in files:
            yol = os.path.join(root, f)
            try:
                boyut = os.path.getsize(yol)
                if boyut > limit_byte:
                    boyut_mb = round(boyut / (1024 * 1024), 2)
                    buyukler.append((os.path.relpath(yol, dizin), boyut_mb))
            except (OSError, FileNotFoundError):
                continue
    return buyukler


def git_ag_ayarlarini_yapilandir():
    """Geniş çaplı yüklemelerde timeout ve buffer kopmalarını önler."""
    cmd("git config --global http.postBuffer 2097152000")  # 2 GB Buffer
    cmd("git config --global http.lowSpeedLimit 1000")
    cmd("git config --global http.lowSpeedTime 600")
    cmd("git config --global core.compression 0")


def klasor_sec():
    while True:
        print("\n" + "=" * 50)
        dizin = (
            input(
                "📁 Proje klasörünü sürükleyip buraya bırakın\n(veya mevcut klasör için Enter): "
            )
            .strip()
            .strip("\"'")
        )

        if not dizin:
            return True

        if os.path.isdir(dizin):
            os.chdir(dizin)
            print(f"-> Çalışma klasörü: {os.getcwd()}")
            return True
        else:
            print("[!] Klasör bulunamadı. Lütfen yolu kontrol edin.")


def repo_baglantisi_al():
    ok, out, _ = cmd("git remote get-url origin")
    if ok and out:
        return out

    print("\n🔗 Bu klasör henüz bir GitHub deposuna bağlı değil.")
    while True:
        url = input("GitHub Repository URL'sini girin: ").strip()
        if url.startswith("https://") or url.startswith("git@"):
            cmd("git remote remove origin")
            cmd(f"git remote add origin {url}")
            return url
        print("[!] Geçerli bir GitHub linki giriniz.")


def calistir():
    print("=" * 50)
    print("       🚀 GİTHUB YÜKLEME & GÜNCELLEME ARACI       ")
    print("=" * 50)

    # Git kurulu mu kontrol et
    git_var, _, _ = cmd("git --version")
    if not git_var:
        print("\n[!] Sistemde Git bulunamadı!")
        print("Lütfen Git'i kurun: https://git-scm.com/downloads")
        input("\nÇıkmak için Enter'a basın...")
        return

    if not klasor_sec():
        return

    # 1. Boyut ve Dosya Kontrolü
    print("\n🔍 Proje taranıyor ve dosya boyutları denetleniyor...")
    toplam_mb = klasor_boyutu_hesapla(os.getcwd())

    if toplam_mb >= 1024:
        print(f"-> Toplam Proje Boyutu: {toplam_mb / 1024:.2f} GB")
    else:
        print(f"-> Toplam Proje Boyutu: {toplam_mb:.2f} MB")

    if toplam_mb > 2048:
        print(
            "\n[!] BİLGİ: Toplam boyut GitHub'ın önerilen 2 GB depo sınırını aşıyor."
        )
        print("    Yükleme yapılabilir ancak GitHub ileride uyarı verebilir.")

    engeller = buyuk_dosya_taramasi(os.getcwd())
    if engeller:
        print("\n[!] DİKKAT: GitHub tek dosyada 100 MB sınırına sahiptir!")
        print("Aşağıdaki dosyalar yüklemeyi durduracaktır:")
        for dosya, boyut in engeller:
            print(f"  - {dosya} ({boyut} MB)")
        print(
            "\nÇözüm: Bu dosyaları .gitignore içine ekleyin veya Git LFS kullanın."
        )
        onay = (
            input("Yine de devam etmek istiyor musunuz? (e/h): ")
            .strip()
            .lower()
        )
        if onay != "e":
            print("İşlem iptal edildi.")
            return

    # 2. Ağ Ayarları
    git_ag_ayarlarini_yapilandir()

    if not os.path.exists(".git"):
        cmd("git init")
        cmd("git branch -M main")

    _, branch, _ = cmd("git branch --show-current")
    if not branch:
        branch = "main"
        cmd(f"git branch -M {branch}")

    repo_url = repo_baglantisi_al()

    _, status, _ = cmd("git status --short")
    if not status:
        print("\n✅ Değişen veya yeni eklenen dosya yok. Her şey güncel!")
        input("\nKapatmak için Enter'a basın...")
        return

    mesaj = (
        input("\n💬 Ne değiştirdiniz? (Açıklama girin veya Güncelleme için Enter): ").strip()
        or "Proje guncellemesi"
    )

    print("\n⏳ Dosyalar taranıyor ve Git paketine ekleniyor...")
    cmd("git add .")

    print("[+] Değişiklikler yerel olarak kaydedildi.")
    cmd(f'git commit -m "{mesaj}"')

    print(
        f"\n🚀 Veriler GitHub'a aktarılıyor (origin/{branch})...\nLütfen internet bağlantısını kesmeyin..."
    )

    basarili, out, err = cmd(f"git push -u origin {branch}")

    if not basarili:
        print("[i] Uzak depoyla senkronizasyon deneniyor...")
        cmd(f"git pull origin {branch} --allow-unrelated-histories --no-rebase")
        basarili, out, err = cmd(f"git push origin {branch}")

    print("\n" + "=" * 50)
    if basarili:
        print("🎉 TEBRİKLER! Projeniz başarıyla yüklendi/güncellendi.")
    else:
        print("❌ Yükleme sırasında hata oluştu:")
        print(err if err else out)
    print("=" * 50)

    input("\nKapatmak için Enter'a basın...")


if __name__ == "__main__":
    try:
        calistir()
    except KeyboardInterrupt:
        print("\nİşlem iptal edildi.")