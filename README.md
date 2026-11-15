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
- **Yenileme başına ajan hamlesi:** Varsayılan 1 değerinde her ajanın hamlesi ayrı gösterilir. 1–20 arasında artırarak eğitimi hızlandırabilirsiniz; ajanların 1–3 hücrelik hızları değişmez. Yüksek değerlerde bütün hamleler yine sırayla hesaplanır, yalnızca son durum gösterilir.
- **Canlı durum:** Tamamlanan tur sayısını ve sıradaki ajanın hangi turda hamle yapacağını gösterir.
- **Öğrenme nasıl değişiyor?:** Son ajan hamlesinin ödülünü, önceki/yeni Q değerlerini ve öğrenme katsayılarını gösterir. Bağlantıdan bütün belleği JSON biçiminde açabilirsiniz.
- **Eğitim geçmişi:** Sıralı akışta tamamlanan bölümleri gösterir. Bölüm bilgisinin yanındaki **Bitiş turu**, bölümün kaç turda sona erdiğini belirtir. Tabloda ayrıca yiyecek sayısı, başlangıç seed değeri, uzaklık ölçüsü, α/γ/ε katsayıları ve ajanların ayrı skorları ile hızları bulunur. Aynı yiyecek sayısında yeterli bölüm varsa ilk ve son 10 bölümün ortalama ödülü de görünür.

Ajanlar her turda **1 → 2 → 3** sırasıyla oynar. Sırası gelen ajan, önceki hamlelerin değiştirdiği güncel tahtaya göre karar verir. Her hamleden sonra yeşiller kontrol edilir; son yeşil alındıysa sıradaki ajan oynamadan bölüm sonucu kaydedilir ve yeni bölüm ajan 1 ile başlar. Üç ajan da oynadıktan sonra sonraki tura geçilir. Yeşiller kalmışsa 4.000 tam tur sonunda bölüm sonlandırılır. Geçmişteki tur sayısı, yeşillerin bittiği son kısmi turu da içerir.

Uygulamayı tamamen kapatmak için terminalde `Ctrl+C` kullanın. Yalnızca tarayıcıyı kapatmak sunucuyu sonlandırmaz.

## İsteğe bağlı başlangıç ayarları

```powershell
.\.venv\Scripts\python.exe app.py --food-pairs 40 --seed 42 --paused
```

`--paused` duraklatılmış açar. `--seed` aynı başlangıç koşullarını yeniden üretmek içindir; arayüzde yapılan işlemler sonraki rastgele seçimlerin sırasını etkileyebilir. Sabit port gerekiyorsa `--port 8000` ekleyin.

## Öğrenme dosyası

Yeni sürüm `learning_memory.json` dosyasını otomatik oluşturur. Q değerleri, ziyaret sayıları ve bütün tamamlanan bölümler burada okunabilir JSON olarak tutulur. Bölüm sonunda, duraklatırken, yeni bölüm açarken ve `Ctrl+C` ile çıkarken kaydedilir; uygulama açılırken yüklenir. Kapanışta devam eden tahtanın konumları kaydedilmez; sonraki açılışta yeni tahta kurulur ve öğrenme belleği devam eder.

Geçmişte yalnızca sıralı akışın bölüm sonuçları tutulur; eski eşzamanlı kayıtlar bellek yüklenirken dosyadan temizlenir. Öğrenilmiş Q değerleri, ziyaret sayıları ve keşif oranını belirleyen toplam öğrenme sayacı korunarak eğitim sürdürülür. Her renkten 40 yiyecekle duraklatılmış açmak için:

```powershell
.\.venv\Scripts\python.exe app.py --food-pairs 40 --paused
```

Kullanılmayan eski `agent_memory.json` ve `training_results.csv` kaldırılmıştır. Uygulamanın kullandığı tek kalıcı öğrenme dosyası `learning_memory.json` dosyasıdır.

Projenin kavramları, matematiği ve kodun adım adım açıklaması için `report.md` dosyasını okuyun.
