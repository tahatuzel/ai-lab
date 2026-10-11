# BIL353 Yapay Zekâ Dönem Projesi

Bu proje, ödevdeki 50 × 50 tahtayı ve üç bağımsız ajanı Python ile simüle eder. Ajanlar yeşil yiyecekleri toplar, kırmızı yiyeceklerden kaçınır, başka ajanla aynı yeşil hücrede karşılaşınca Sol eyleminin önceliği uygulanır. Ajanlar yiyecekleri ve yalnızca en yakın rakibin konumunu gözlemler.

Uygulama iki şekilde çalışır: tarayıcı arayüzü üzerinden canlı simülasyon ve aynı başlangıç tahtalarını kullanan toplu algoritma eğitimi. Python standart kütüphanesi dışında paket kullanmaz; bağımlılık indirmez veya bilgisayarın genel Python ortamına paket kurmaz.

## Hızlı başlangıç

PowerShell'i bu proje klasöründe açın. Ortam yoksa proje klasörünün içinde oluşturun ve uygulamayı yalnızca bu ortamın Python'ı ile çalıştırın:

    python -m venv .venv
    .\.venv\Scripts\python.exe app.py

Uygulama varsayılan tarayıcıda yerel bir sayfa açar ve simülasyonu otomatik başlatır. Ajanlar, arayüz açıkken saniyede birden çok simülasyon adımı işler. Başlat/Duraklat düğmesi öğrenmeyi kontrol eder. Sunucu yalnızca bu bilgisayardaki 127.0.0.1 adresinde dinler. Uygulamayı kapatmak için başlatıldığı terminalde Ctrl+C kullanın; her bölüm sonunda bellek ayrıca kaydedilir.

Projede bulunan sanal ortamı doğrulamak için:

    .\.venv\Scripts\python.exe --version

Kodda yalnızca Python standart kütüphanesi kullanılır. pip install veya bilgisayarın genel ortamına kurulum gerekmez.

İlk açılış ayarları örneği:

    .\.venv\Scripts\python.exe app.py --food-pairs 200 --seed 42

--food-pairs her renkten yiyecek sayısını belirler; geçerli aralık 1–375'tir. --seed başlangıç tahtasını tekrarlanabilir kılar. Sunucu portunu otomatik seçer. Arayüzün duraklatılmış açılmasını istiyorsanız --paused ekleyin.

## Toplu eğitim ve algoritma kıyaslaması

Tarayıcıyı açmadan ajanları eğitmek ve dört yöntemi eşleştirilmiş tahtalarda kıyaslamak için:

    .\.venv\Scripts\python.exe app.py --train-episodes 20 --food-pairs 125 --seed 42

Bu komut her algoritma için 20 bölüm çalıştırır. Her turda A*, Dijkstra, Greedy Best-First ve Manhattan aynı seed değerinden üretilen yiyecek ve ajan başlangıçlarını kullanır. Böylece tek bir kolay veya zor tahta algoritmalardan birine avantaj sağlamaz. Ajanların eylem keşfi rastgele olduğundan her bölümün sonucu yine değişebilir.

Yalnızca bazı yöntemleri karşılaştırmak için:

    .\.venv\Scripts\python.exe app.py --train-episodes 20 --food-pairs 125 --seed 42 --algorithms "A*" Dijkstra Manhattan

Yiyecek sayısını azaltmak kısa deneme çalışmaları için kullanışlıdır:

    .\.venv\Scripts\python.exe app.py --train-episodes 5 --food-pairs 40 --seed 42

Komut her tamamlanan bölümden sonra ilerlemeyi terminalde gösterir. Bitince her algoritmanın ilk ve son bölüm grubundaki ortalama yeşil, kırmızı, toplam ödül ve planlama süresini yazar. Toplu eğitim sırasında da Q-tablosu ve CSV her bölümden sonra kaydedilir; işlem kesilse bile tamamlanan bölümler korunur. --train-episodes verilmezse canlı uygulama açılır.

Algoritma seçenekleri: A*, Dijkstra, Greedy Best-First, Manhattan.

## Tarayıcı arayüzü

- **Başlat / Duraklat:** Ajanların simülasyon adımlarını ve çevrimiçi öğrenmesini başlatır veya durdurur.
- **Yeni bölüm:** Ajanları ve yiyecekleri yeniden yerleştirir; öğrenilmiş değerleri silmez.
- **Her renkten yiyecek sayısı:** Yeni bölümdeki yeşil ve kırmızı yiyecek sayısını belirler.
- **Yol bulma algoritması:** Seçilen yöntem Yeni bölüm'e basıldığında devreye girer. Her yöntemin Q-tablosu ve keşif oranı ayrıdır.
- **Arayüz yenilemesi başına adım:** Her ekran güncellemesinde simüle edilen adım sayısını artırarak öğrenme hızını yükseltir.
- **Canlı durum:** Geçerli algoritmayı, bölüm ve adım numarasını, kalan yiyecekleri, ajan ödüllerini, keşif oranını ve öğrenilmiş durum-eylem sayısını gösterir.
- **Algoritma karşılaştırması:** Tablo her yöntemin son 10 tamamlanan bölümdeki ortalama yeşil, kırmızı, ödül ve planlama süresini gösterir. Grafik son 40 bölümün toplam ödülünü algoritma başına çizer.

Planlama süresi, ilgili bölümde eylem seçerken yol bulmaya harcanan Python işlem süresidir. Ekranda gösterilen ortalamalar küçük bölüm sayılarında gürültülü olur. Karşılaştırma için aynı seed ile daha çok bölüm çalıştırın ve yeşil, kırmızı, ödül ile süre ölçülerini birlikte değerlendirin.

### Son kısa ölçüm

11.10.2026 tarihinde seed 42 ile, her renkten 40 yiyecek bulunan aynı başlangıç tahtalarında algoritma başına beş bölüm çalıştırıldı. Beş bölümün ortalamaları:

| Algoritma | Yeşil | Kırmızı | Ödül | Planlama süresi |
|---|---:|---:|---:|---:|
| A* | 40 | 0 | 40 | 200 ms |
| Dijkstra | 40 | 0 | 40 | 631 ms |
| Greedy Best-First | 40 | 0 | 40 | 124 ms |
| Manhattan | 40 | 0 | 40 | 135 ms |

Bu küçük tahtalarda bütün yöntemler ödülün üst sınırına ulaştı; bu ölçüm ödül bakımından bir algoritmanın üstün olduğunu göstermiyor. Dijkstra daha uzun planlama yaptı. Daha zor tahtalarda veya daha çok yiyecekle kıyaslayın; her çalıştırma CSV'ye yeni satırlar ekler ve aşağıdaki arayüz güncel kayıtları gösterir.

Ardından, öğrenme belleği her algoritma için 30 bölüme ulaşmışken daha önce zorlayıcı çıkan seed 50 tahtası tekrar çalıştırıldı. Aynı tahtanın daha eski kaydı algoritma başına 9. bölümde alınmıştı:

| Algoritma | Eski kayıt: yeşil / adım | Son kayıt: yeşil / adım | Son planlama |
|---|---:|---:|---:|
| A* | 19 / 4.000 | 40 / 95 | 57 ms |
| Dijkstra | 19 / 4.000 | 40 / 96 | 135 ms |
| Greedy Best-First | 19 / 4.000 | 40 / 158 | 99 ms |
| Manhattan | 22 / 4.000 | 39 / 4.000 | 1.823 ms |

Bu karşılaştırmada hem Q belleği ilerledi hem de hız değerini kullanan rota araması ve erişilebilir alternatif hedef seçimi düzeltildi. Bu yüzden fark yalnızca öğrenmeye bağlanamaz. Son durumda üç rota yöntemi tahtayı tamamladı; Manhattan yöntemi bir yeşil yiyecekte takılıp adım sınırına ulaştı. Bu, yöntemlerin farklı senaryolarda farklı performans verdiğini gösterir ve sonraki denemelerde iyileştirilmesi gereken noktayı açık bırakır. CSV şu ana kadar dört yöntem için 30'ar bölüm, toplam 120 kayıt içeriyor.

Tahtadaki yeşil daireler yiyecekleri, kırmızı kareler zararlı yiyecekleri gösterir. Mavi, mor ve turuncu ajanlar sırasıyla 1, 2 ve 3 numaralıdır. Gri kesikli çizgiler her ajanın gözlemlediği en yakın rakibi gösterir.

## Ödev kurallarının uygulanması

- Tahta 50 × 50 hücredir.
- Her tahtada üç ajan bulunur. Ajanlar ve yiyecekler farklı hücrelere rastgele yerleştirilir.
- Yeşil ve kırmızı yiyecek sayısı eşittir. Toplam yiyecek hücresi sayısı 2.500 hücrenin en fazla %30'u olduğundan her renkten en çok 375 yiyecek bulunur.
- Her bölümde Manhattan veya Öklid uzaklığı rastgele seçilir. Bu ölçü, ajanın gözlemleyebildiği en yakın diğer ajanı belirler.
- Ajanlar bütün yeşil ve kırmızı yiyecek konumlarını görebilir; diğer ajanlardan yalnızca en yakınının konumunu görür.
- Her ajanın hızı her bölümün başında 1, 2 veya 3 hücre arasında rastgele seçilir. Ajan aynı eylem yönünde hız değeri kadar ilerler; tahta kenarında veya yiyeceğe çarpınca hareketi kesilir.
- Ayrık eylemler Yukarı, Aşağı, Sol, Sağ ve Eylemsiz'dir. Ödev metni “4 branches” ifadesini kullansa da aynı maddede beş hareket değeri listeler; uygulama listelenen beş eylemi kullanır.
- Yalnızca yiyeceği alan ajan +1 yeşil veya −1 kırmızı ödül alır.
- Aynı adımda birkaç ajan aynı yeşil hücreye girerse Sol eylemini yapan kazanır. Birden fazla Sol veya hiç Sol yoksa düşük ajan numarası kazanır.
- Bütün yeşil yiyecekler toplandığında veya 4.000 simülasyon adımına ulaşıldığında bölüm biter ve canlı arayüz yeni bölüme geçer.

## Yol bulma algoritmaları

Dört yöntem aynı gözlem, hedef seçimi, Q-öğrenme ve hareket kurallarını paylaşır. Yol planlayıcıları ve Q tablosu algoritma adına göre ayrı tutulur. Böylece bir yöntemin öğrendiği eylem tercihleri diğer yöntemin sonuçlarını kirletmez.

### A*: risk maliyetli sezgisel arama

A* her geçişin maliyetine Manhattan hedef uzaklığını ekler. Boş hücre maliyeti 1, kırmızı yiyeceğe girme maliyeti 16'dır. Kırmızı hücreler duvar sayılmaz; A* uygun olduğunda kırmızıdan dolaşan daha düşük riskli rotayı seçer. Manhattan uzaklığı bu geçiş maliyetini aşmadığı için arama hedefe yönelik kalır.

### Dijkstra

Dijkstra aynı hücre maliyetlerini kullanır, fakat hedefe kalan uzaklık kestirimini kullanmaz. Bu nedenle maliyeti en düşük rotayı bulur ve uygun koşullarda A* ile aynı rotayı seçer; daha çok hücreyi inceleyebildiği için planlama süresi farklı çıkabilir. Bu yöntem A* karşılaştırmasında sezgisel kestirimin etkisini gösterir.

### Greedy Best-First

Greedy Best-First sıradaki hücreyi hedefe Manhattan uzaklığı en az olana göre seçer. Birikmiş yol maliyetini eşitlik bozucu olarak kullanır; ancak ana önceliği hedefe yakınlıktır. Bu nedenle kısa görünen rota risk maliyetli en ucuz rota olmayabilir. Genelde daha az arama yapar, fakat kırmızılara yaklaşabilir veya daha uzun rotaya sapabilir.

### Manhattan

Manhattan yöntemi graf araması yapmaz. Her adımda olası eylemlerin hedefe kalan Manhattan uzaklığını karşılaştırır ve kırmızı yiyeceğe doğrudan çarpma için ceza uygular. Ucuz bir temel karşılaştırma sağlar; uzaktaki engelleri A*, Dijkstra veya Greedy gibi planlayamaz.

Planlayıcı arama grafiğinde ajanın gerçek hızını kullanır: bir kenar tek hücrelik değil, eylem sırasında kat edilebilecek en çok 1–3 hücrelik harekettir; yiyecek veya tahta sınırı hareketi erken bitirebilir. Bu sayede planlanan rota ajanın hızına uyar. Hız ve hücre konumuna göre bazı hedefler bir eylem dizisiyle erişilemez olabilir. Ajan önce puanlamada öne çıkan sekiz yeşil hedefi tek aramada dener; hiçbiri erişilemiyorsa diğer yeşil hedefler arasından erişilebilir olanı arar. Eylem adayları ayrıca ajanın hızla ilerlemesini, yiyecekte durmasını, duvara çarpmasını, o anki kırmızı hücreleri ve öğrenilmiş Q değerini hesaba katar.

## Hedef seçimi ve yiyecek kümeleri

Her ajan erişebildiği yeşil yiyecekleri hedef adayı olarak değerlendirir. İlk tahmin Manhattan uzaklığını hıza böler. Ajanın gördüğü en yakın rakip bir yiyeceğe daha önce ulaşabilecek görünüyorsa bu hedefe rekabet cezası eklenir; rakibin hızı gözlemlenmediğinden tahminde 2 hücre/tur varsayılır.

Hedefin üç hücrelik Manhattan çevresindeki yeşil yiyecekler sayılır. Yakın bir küme için küçük ve sınırlı bir bonus uygulanır. Bu, rastgele dağılımda tesadüfen oluşan kümeleri değerlendirmeye yarar; yiyeceklerin gizli bir yerleşim kuralı olduğunu varsaymaz. Ajanlar aynı hedefi seçebilir; gerçek hücreye girişte Sol önceliği kuralı çalışır.

## Zaman içinde öğrenme

Her ajan ve her planlayıcı için ayrı bir tablo tutulur. Durum özeti hedefin x/y yönünü, en yakın kırmızı yiyeceğe uzaklık aralığını, gözlemlenen rakibe göre hedef rekabetini ve ajanın hızını içerir. Durum-eylem değerleri beş hareket seçeneğini puanlar.

Q tablosu her hareketten sonra zamansal fark öğrenmesiyle güncellenir:

    δ = ödül + γ × sonraki durumun en yüksek Q değeri − mevcut Q değeri
    Q(s, a) ← Q(s, a) + α × δ × iz(s, a)

γ = 0.90 gelecekteki ödülün ağırlığıdır. λ = 0.75 uygunluk izlerinin sönümünü belirler; izler, son ödülün o ödüle giden önceki eylemlere de geri yayılmasını sağlar. Öğrenme oranı α, tekrar edilen durum-eylem çiftlerinde azalır:

    α = max(0.04, 0.30 / √(ziyaret sayısı + 1))

Eylem seçerken ajan çoğunlukla en yüksek puanlı hareketi kullanır; ε olasılığıyla yeni bir eylem dener. Her algoritmanın başlangıç ε değeri 0.18'dir. O algoritmanın son 100 bölümdeki ortalama takım ödülü pozitifse ε bölüm başına %3 azalır; negatifse %5 artar. ε değeri 0.02–0.25 arasında tutulur. Bu, başarılı yöntemde daha çok öğrenilmiş eylem kullanmayı, kötü sonuçta ise yeniden keşfetmeyi sağlar.

## Kalıcı dosyalar

### agent_memory.json

Proje kökünde otomatik oluşturulur. Şunları saklar:

- Dört algoritmanın ayrı Q durum-eylem değerleri ve ziyaret sayıları.
- Her algoritmanın bölüm sayısı, keşif oranı ve son 100 ödülü.
- Son 500 bölümün çizim ve özet için gereken sonuç satırları.

Dosya her bölüm sonunda geçici bir dosyaya yazılıp atomik olarak değiştirilir; uygulama açılırken yeniden yüklenir. Önceki sürümdeki tek A* Q tablosu yüklenirse A* tablosuna taşınır. Deneylere sıfırdan başlamak için uygulamayı kapatıp bu dosyayı silin.

### training_results.csv

Proje kökünde oluşturulur ve her tamamlanan bölüme yeni satır ekler. Excel veya metin düzenleyicide açılabilir. Sütunlar zaman damgası, algoritma, toplam ve algoritma içindeki bölüm numarası, seed, yiyecek sayısı, adım, yeşil/kırmızı yiyecek, ödül, ε ve planlama milisaniyesidir. Bu dosyayı silmediğiniz sürece önceki eğitim denemeleri de kayıtta kalır.

Her iki dosya da proje dışına yazılmaz. agent_memory.json çalışma zamanı verisidir ve .gitignore ile Git dışı bırakılmıştır; CSV özellikle deney geçmişini inceleyebilmeniz için proje klasöründe görünür kalır.

## Dosya yapısı

- app.py: Yerel Python HTTP sunucusu, tarayıcı API'si, toplu eğitim komutu.
- simulation.py: Tahta, ajan gözlemi ve hareketi, çarpışma/ödül kuralları, yol bulucular ve Q-öğrenme.
- index.html: Bağımlılıksız canlı tahta ve algoritma karşılaştırması.
- hw.txt: Verilen ödev metni.
- .venv/: Bu klasöre özel Python sanal ortamı.
- agent_memory.json: Kalıcı öğrenme belleği.
- training_results.csv: Bölüm bölüm performans günlüğü.

## Kontroller

Standart kütüphaneyle derleme kontrolü ve algoritma öz denetimi:

    .\.venv\Scripts\python.exe -m py_compile app.py simulation.py
    .\.venv\Scripts\python.exe simulation.py

Kısa, baştan sona eğitim çalışması:

    .\.venv\Scripts\python.exe app.py --train-episodes 2 --food-pairs 20 --seed 7

Eğitim komutu CSV'ye sonuç yazdığı için bu kısa çalışmadan sonra training_results.csv içinde yeni satırlar ve agent_memory.json içinde Q/episode değerleri görmelisiniz.
