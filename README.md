# BIL353 — Çalıştırma kılavuzu

Bu proje, `hw.txt` içindeki yiyecek toplama ortamını uygular. Python simülasyonu çalıştırır; HTML sayfasından eğitimi izler ve kontrol edersiniz. Harici paket gerekmez.

## Gereksinim

Python 3.10 veya üzeri. Komutları bu proje klasöründe, PowerShell üzerinden çalıştırın.

## İlk çalıştırma

Sanal ortamınız yoksa bir kez oluşturun:

```powershell
python -m venv .venv
```

Uygulamayı başlatın:

```powershell
.\.venv\Scripts\python.exe app.py
```

Tarayıcı otomatik açılır. Açılmazsa terminalde yazan `http://127.0.0.1:...` adresine gidin. `index.html` dosyasını çift tıklayarak açmak yerine Python sunucusunu kullanın.

## HTML üzerinden kullanım

- **Başlat / Duraklat:** Simülasyonu ve öğrenmeyi çalıştırır veya bekletir. Başlangıçta simülasyon çalışır.
- **Her renkten yiyecek sayısı:** 1–375 arasında tam sayı girin. Örneğin 125, 125 yeşil ve 125 kırmızı demektir.
- **Uygula / Yeni bölüm:** Girilen yiyecek sayısını uygular ve tahtayı yeniden oluşturur. Öğrenilmiş Q değerlerini korur. Yarım kalan bölüm, tamamlanmış bölüm olarak kaydedilmez.
- **Yenileme başına adım:** Eğitim hızını değiştirir; ajanların 1–3 hücrelik hızını değiştirmez.
- **Öğrenme nasıl değişiyor?:** Son adımın ödülünü, önceki/yeni Q değerlerini ve öğrenme katsayılarını gösterir. Bağlantıdan bütün belleği JSON biçiminde açabilirsiniz.
- **Eğitim geçmişi:** Her bölümün zamanını, yiyecek sayısını, başlangıç seed değerini, uzaklık ölçüsünü, α/γ/ε katsayılarını, adım sayısını ve ajanların ayrı skorları ile hızlarını gösterir. Aynı yiyecek sayısında yeterli bölüm varsa ilk ve son 10 bölümün ortalama ödülü de görünür.

Yeşiller bitince veya 4.000 adıma ulaşılınca sonuç kaydedilir ve yeni bölüm otomatik başlar. Uygulamayı tamamen kapatmak için terminalde `Ctrl+C` kullanın. Yalnızca tarayıcıyı kapatmak sunucuyu sonlandırmaz.

## İsteğe bağlı başlangıç ayarları

```powershell
.\.venv\Scripts\python.exe app.py --food-pairs 40 --seed 42 --paused
```

`--paused` duraklatılmış açar. `--seed` aynı başlangıç koşullarını yeniden üretmek içindir; arayüzde yapılan işlemler sonraki rastgele seçimlerin sırasını etkileyebilir. Sabit port gerekiyorsa `--port 8000` ekleyin.

## Öğrenme dosyası

Yeni sürüm `learning_memory.json` dosyasını otomatik oluşturur. Q değerleri, ziyaret sayıları ve bütün tamamlanan bölümler burada okunabilir JSON olarak tutulur. Bölüm sonunda, duraklatırken, yeni bölüm açarken ve `Ctrl+C` ile çıkarken kaydedilir; uygulama açılırken yüklenir. Kapanışta devam eden tahtanın konumları kaydedilmez; sonraki açılışta yeni tahta kurulur ve öğrenme belleği devam eder.

Hazırlanan sürümde, her renkten 40 yiyecekle çalıştırılmış 30 bölümün gerçek kayıtları vardır. Bunları görmek için uygulamayı bu ayarla açabilirsiniz:

```powershell
.\.venv\Scripts\python.exe app.py --food-pairs 40 --paused
```

Önceki sürümün `agent_memory.json` ve `training_results.csv` dosyaları korunmuştur. Yeni sürüm bunları değiştirmez veya yeni belleğe aktarmaz; eski dosyaların öğrenme yapısı farklıdır.

Projenin kavramları, matematiği ve kodun adım adım açıklaması için `report.md` dosyasını okuyun.
