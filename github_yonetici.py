import os
import subprocess
import sys


def cmd(command):
    """Komutu sessizce çalıştırır, (başarılı_mı, çıktı) döndürür."""
    res = subprocess.run(command, shell=True, text=True, capture_output=True)
    return res.returncode == 0, res.stdout.strip(), res.stderr.strip()


def git_kontrol():
    ok, _, _ = cmd("git --version")
    if not ok:
        print("\n[!] Bilgisayarınızda Git kurulu değil!")
        print("Lütfen önce Git kurun: https://git-scm.com/")
        input("\nÇıkmak için Enter'a basın...")
        sys.exit(1)


def klasor_sec():
    while True:
        print("\n" + "=" * 45)
        dizin = (
            input(
                "📁 Proje klasörünü sürükleyip buraya bırakın\n(veya mevcut klasör için doğrudan Enter'a basın): "
            )
            .strip()
            .strip("\"'")
        )

        if not dizin:
            print(f"-> Seçilen klasör: {os.getcwd()}")
            return True

        if os.path.isdir(dizin):
            os.chdir(dizin)
            print(f"-> Çalışma klasörü: {os.getcwd()}")
            return True
        else:
            print("[!] Klasör bulunamadı. Lütfen yolu kontrol edin.")


def repo_baglantisi_al():
    """Origin URL'sini alır veya kullanıcıdan girmesini ister."""
    ok, out, _ = cmd("git remote get-url origin")
    if ok and out:
        return out

    print("\n🔗 Bu klasör henüz bir GitHub deposuna bağlı değil.")
    while True:
        url = input(
            "GitHub Repository URL'sini yapıştırın (https://github.com/...): "
        ).strip()
        if url.startswith("https://") or url.startswith("git@"):
            cmd("git remote remove origin")
            cmd(f"git remote add origin {url}")
            return url
        print("[!] Geçerli bir GitHub linki giriniz.")


def tek_tus_calistir():
    git_kontrol()
    print("=" * 45)
    print("       🚀 GİTHUB YÜKLEME & GÜNCELLEME       ")
    print("=" * 45)

    # 1. Adım: Klasör Belirle
    if not klasor_sec():
        return

    # Git init kontrolü
    if not os.path.exists(".git"):
        cmd("git init")
        cmd("git branch -M main")

    # Dal (Branch) tespiti ve sabitleme
    _, branch, _ = cmd("git branch --show-current")
    if not branch:
        branch = "main"
        cmd(f"git branch -M {branch}")

    # 2. Adım: GitHub Bağlantısını Doğrula
    repo_url = repo_baglantisi_al()

    # 3. Adım: Değişiklik Kontrolü
    _, status, _ = cmd("git status --short")
    if not status:
        print("\n✅ Klasörde değişen veya yeni eklenen bir dosya yok. Her şey güncel!")
        input("\nKapatmak için Enter'a basın...")
        return

    print("\n📄 Tespit edilen yeni/değişen dosyalar hazırlandı.")

    # 4. Adım: Commit Açıklaması
    mesaj = input(
        "\n💬 Ne değiştirdiniz? (Açıklama girin veya 'Güncelleme' için Enter): "
    ).strip()
    if not mesaj:
        mesaj = "Proje guncellemesi"

    print("\n⏳ Dosyalar GitHub'a aktarılıyor, lütfen bekleyin...")

    # Git işlemleri
    cmd("git add .")
    cmd(f'git commit -m "{mesaj}"')

    # Önce uzaktaki son durumu çek (çakışmaları önlemek için)
    cmd(f"git pull origin {branch} --rebase")

    # Push dene
    basarili, _, err = cmd(f"git push -u origin {branch}")

    if not basarili:
        # Eğer ilk push ise veya dal uyumsuzluğu varsa zorlamadan önce basit push dene
        basarili, _, err = cmd(f"git push origin {branch}")

    print("\n" + "=" * 45)
    if basarili:
        print("🎉 TEBRİKLER! Projeniz başarıyla GitHub'a yüklendi.")
    else:
        print("❌ Yükleme sırasında bir hata oluştu.")
        print(f"Hata detayı:\n{err}")
        print("\nOlası Nedenler:")
        print("1. GitHub girişiniz eksik olabilir (Personal Access Token gerekebilir).")
        print("2. Repo linkini yanlış girmiş olabilirsiniz.")
    print("=" * 45)

    input("\nKapatmak için Enter'a basın...")


if __name__ == "__main__":
    try:
        tek_tus_calistir()
    except KeyboardInterrupt:
        print("\n\nİşlem iptal edildi.")
