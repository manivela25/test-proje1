import os
import subprocess
import sys


def cmd(command):
    """Komutu calistirir, (basarili_mi, cikti, hata) dondurur."""
    res = subprocess.run(command, shell=True, text=True, capture_output=True)
    return res.returncode == 0, res.stdout.strip(), res.stderr.strip()


def buyuk_dosya_kontrol(dizin, limit_mb=99):
    """100 MB sinirina takilacak dosyalari tarar."""
    buyukler = []
    limit_byte = limit_mb * 1024 * 1024
    for root, _, files in os.walk(dizin):
        if ".git" in root:
            continue
        for f in files:
            yol = os.path.join(root, f)
            try:
                if os.path.getsize(yol) > limit_byte:
                    boyut_mb = round(os.path.getsize(yol) / (1024 * 1024), 2)
                    buyukler.append((os.path.relpath(yol, dizin), boyut_mb))
            except (OSError, FileNotFoundError):
                continue
    return buyukler


def git_ag_ayarlarini_yapilandir():
    """1.3 GB gibi yuklemelerde timeout ve buffer hatalarini engeller."""
    # 2 GB HTTP Post Buffer ayari
    cmd("git config --global http.postBuffer 2097152000")
    # Baglanti timeout surelerini uzat
    cmd("git config --global http.lowSpeedLimit 1000")
    cmd("git config --global http.lowSpeedTime 600")
    # Sikistirmayi ac
    cmd("git config --global core.compression 0")


def klasor_sec():
    while True:
        print("\n" + "=" * 45)
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
    print("   🚀 GİTHUB YÜKLEME ARACI (BÜYÜK VERİ DESTEKLİ)")
    print("=" * 50)

    if not klasor_sec():
        return

    # 1. Aşama: Büyük dosya kontrolü
    print("\n🔍 Dosya boyutları denetleniyor (100 MB sınırı)...")
    engeller = buyuk_dosya_kontrol(os.getcwd())
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

    # 2. Aşama: Git Ağ optimizasyonu
    print("[+] Git aktarım ayarları (2 GB Buffer) optimize ediliyor...")
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
        print("\n✅ Değişen dosya yok. Her şey güncel!")
        return

    mesaj = (
        input("\n💬 Commit açıklaması (Varsayılan: 'Büyük güncelleme'): ").strip()
        or "Büyük güncelleme"
    )

    print("\n⏳ 1.3 GB veri taranıyor ve paketleniyor (Bu biraz sürebilir)...")
    cmd("git add .")

    print("[+] Değişiklikler yerel olarak kaydediliyor...")
    cmd(f'git commit -m "{mesaj}"')

    print(
        f"\n🚀 Dosyalar GitHub'a aktarılıyor (origin/{branch})...\nLütfen internet bağlantısını kesmeyin..."
    )

    # Büyük dosyalarda rebase çakışma yaratabileceğinden sade push uygulanır
    basarili, out, err = cmd(f"git push -u origin {branch}")

    if not basarili:
        # Eğer uzak sunucuda değişiklik varsa önce çekmeyi dene
        print("[i] Uzak depoyla senkronizasyon deneniyor...")
        cmd(f"git pull origin {branch} --allow-unrelated-histories --no-rebase")
        basarili, out, err = cmd(f"git push origin {branch}")

    print("\n" + "=" * 50)
    if basarili:
        print("🎉 TEBRİKLER! 1.3 GB veriniz başarıyla yüklendi/güncellendi.")
    else:
        print("❌ Yükleme sırasında hata oluştu:")
        print(err if err else out)
    print("=" * 50)


if __name__ == "__main__":
    try:
        calistir()
    except KeyboardInterrupt:
        print("\nİşlem iptal edildi.")