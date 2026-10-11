# BIL353 Yapay Zekâ Dönem Projesi Raporu

## Bu raporun amacı

Bu belge, proje klasöründeki hw.txt ödevini nasıl yorumladığımızı ve Python uygulamasında nasıl gerçekleştirdiğimizi baştan sona açıklar. Amaç yalnızca kodu çalıştırmak değil; tahtanın nasıl oluştuğunu, ajanların ne gözlemlediğini, kararları hangi algoritmalarla verdiğini, nasıl öğrendiğini ve sonuçları nasıl değerlendirdiğimizi kendi cümlelerinizle anlatabilmenizi sağlamaktır.

Ödevin ana hedefi şudur: 50 × 50 hücreli bir tahtada üç ajan yeşil yiyecekleri toplamaya çalışırken kırmızı yiyeceklerden kaçınır. Ajanlar hareket eder, yiyecekleri gözler ve başka bir ajanla aynı yiyeceğe yönelirse rekabet eder. Biz bu ortamı Python ile kurduk; dört karar/yol bulma yöntemini kıyasladık ve her yöntemin deneyiminden öğrenmesini sağlayan bir Q-öğrenme tablosu ekledik.

## 1. Ödev metnini nasıl yorumladık?

Ödev metnindeki kuralların uygulamadaki karşılığı:

| Ödev şartı | Uygulamadaki karşılığı |
|---|---|
| 50 × 50 hücreli matris | Tahtanın genişliği ve yüksekliği 50. Koordinatlar 0–49 aralığında. |
| Yeşil ve kırmızı yiyecekler rastgele ve eşit sayıda | Her bölüm başında hücreler rastgele örneklenir. Önce yeşil, sonra aynı sayıda kırmızı ve ardından üç ajan için farklı başlangıç hücreleri seçilir. |
| Yiyecekler toplamda tahtanın en fazla %30’unu kaplar | 50 × 50 = 2.500 hücre. Bunun %30’u 750 hücredir. Renkler eşit sayıda olduğundan en çok 375 yeşil ve 375 kırmızı yiyecek bulunabilir. |
| Üç ajan rastgele yerleştirilir | Her yeni bölümde üç başlangıç hücresi yiyeceklerden ayrı ve rastgele seçilir. |
| Ajan yalnızca en yakın diğer ajanı bilir | Ajanın gözlemine kendi konumu/hızı, bütün yiyeceklerin konumları ve en yakın rakibin konumu girer. Diğer rakip gözlemde yer almaz. |
| En yakın ajan Manhattan veya Öklid uzaklığıyla belirlenir | Her bölümün başında bu iki ölçüden biri rastgele seçilir. Seçilen ölçü, hangi rakibin en yakın olduğunu belirler. |
| Hız 1–3 hücre arasında rastgele seçilir | Her ajana bölüm başında 1, 2 veya 3 hücre/tur hızı atanır. |
| Yukarı, aşağı, sol, sağ veya hareket etme | Beş ayrık eylem uygulanır. Ödev “4 branches” dese de aynı maddede beş eylemi açıkça listeler; bu nedenle listelenen beş hareketi esas aldık. |
| Yeşil yiyecek +1, kırmızı yiyecek −1 | Yiyeceğe ilk ulaşan ajan ilgili ödülü alır. Ödül ajan başına tutulur. |
| Aynı yeşil hücreye rekabette sola hareket eden kazanır | Aynı hücreye aynı anda gidenler arasından “Left” eylemini seçen öncelik kazanır. Birden fazla eşit aday varsa veya hiç kimse sola gitmiyorsa düşük ajan numarasıyla eşitliği bozuyoruz; ödev bu ek eşitlik durumunu açıklamadığı için sonuç tekrarlanabilir olsun diye bu kuralı ekledik. |

Bir bölüm varsayılan olarak her renkten 125 yiyecekle başlar. Bu sayı parametreyle değiştirilebilir; üst sınır her renkten 375’tir. Örneğin 40 yiyecek çifti demek tahtada 40 yeşil ve 40 kırmızı yiyecek olması demektir.

## 2. Projeyi sıfırdan nasıl kurduk?

### Adım 1: Ortamı ve kapsamı seçtik

Uygulama bu proje klasörünün içindeki Python sanal ortamında çalışır. Kod yalnızca Python standart kütüphanesini kullanır; üçüncü taraf paket veya genel Python ortamına kurulum gerektirmez.

İki temel Python dosyasını sorumluluklara ayırdık:

- simulation.py: Tahta, ajanlar, hareket, ödüller, yol arama ve Q-öğrenme.
- app.py: Tarayıcıya yerel sunucu sağlama ve toplu deneyleri çalıştırma.

index.html, tarayıcı arayüzüdür. README.md kullanım ve algoritma belgelerini, hw.txt verilen ödev metnini, training_results.csv deney geçmişini, agent_memory.json öğrenilmiş değerleri tutar.

### Adım 2: Tahtayı ve bölüm başlangıcını oluşturduk

Tahta 2.500 ayrı koordinat hücresinden oluşur. Bir seed değeri verilirse rastgele sayı üretimi aynı sırayla ilerler ve aynı başlangıç tahtası yeniden oluşturulabilir. Bu, algoritmaları karşılaştırırken önemlidir: algoritmaların farklı sonuçlarının yalnızca birine daha kolay tahta verilmesinden kaynaklanmasını istemeyiz.

Bölüm oluşturulurken önce rastgele uzaklık ölçüsü seçilir. Sonra yiyecek ve ajan başlangıçları çakışmayacak biçimde seçilir. Üç ajanın hızı 1–3 aralığında rastgele atanır.

### Adım 3: Her ajanın gözlemini sınırladık

Ortamın içinde bütün ajanların ve yiyeceklerin gerçek konumları bulunur; çarpışmaları doğru çözmek için simülasyon bunları bilmek zorundadır. Ancak karar veren ajana tüm ajanların konumunu göstermiyoruz. Her ajan için ayrı bir gözlem hazırlanır:

- kendi x/y konumu,
- kendi hızı,
- bütün yeşil yiyeceklerin konumları,
- bütün kırmızı yiyeceklerin konumları,
- yalnızca en yakın rakibin konumu.

Bu yapı ödevdeki “Vector Observation” fikrini Python’da bir Observation veri nesnesiyle temsil eder. Unity ML-Agents veya dış bir makine öğrenmesi paketi kullanmıyoruz.

## 3. Ajan hedefini nasıl seçiyor?

Ajanlar yiyecekleri görebildiği için ilk olarak olası yeşil hedefleri sıralıyoruz. Her hedefe yaklaşık bir maliyet puanı veriyoruz:

1. Ajanın hedefe Manhattan uzaklığı hıza bölünür. Böylece daha yakın veya daha hızlı ulaşabileceği hedefler öne çıkar.
2. En yakın rakibin de aynı hedefe daha önce ulaşabileceği görünüyorsa hedefe rekabet cezası eklenir. Rakibin hızı gözlemde verilmediği için bu tahminde 2 hücre/tur varsayılır.
3. Hedefin yakınındaki yeşil yiyecekler sayılır. Üç hücrelik Manhattan çevresinde yiyecek kümesi varsa küçük bir bonus verilir. Bonus sınırlıdır; büyük bir küme puanı tek başına ele geçiremez.
4. Eşitlikte uzaklık, ardından hücre koordinatları kullanılarak kararlı bir sıralama yapılır.

Bu küme bonusu gizli bir yerleşim düzeni varsaymaz. Ödev yiyeceklerin yerleşiminin rastgele olduğunu söylediği için “yiyecekler kesinlikle çizgi halinde veya belirli bölgelerde çıkar” gibi bir kural icat etmiyoruz. Yalnızca o tahtada tesadüfen birbirine yakın duran yiyecekleri birlikte toplamayı değerlendiren küçük bir kestirim kullanıyoruz.

Yol arayan üç yöntemde, öncelikli listedeki ilk sekiz yeşil hedef bir aramada denenir. Bu hedefler ajan hızına ve tahta yapısına göre erişilemiyorsa bütün yeşil hedefler içinde erişilebilir alternatif aranır. Manhattan yöntemiyse graf araması yapmayan karşılaştırma tabanıdır; hedefi puan sırasından seçer.

## 4. Dört karar/yol bulma yöntemini neden ekledik?

Aynı deney ortamında dört yöntemi seçilebilir yaptık. Her biri aynı tür yiyecekleri, aynı hareket kurallarını ve aynı Q-öğrenme çerçevesini kullanır. Aralarındaki temel fark hedefe giden yönü nasıl seçtikleridir.

### 4.1 A*: hedefe yönelen maliyetli arama

A* bir graf üzerindeki başlangıçtan hedefe giden rotayı arar. Arama sırasında iki değeri birleştirir:

- g(n): Başlangıçtan mevcut hücreye kadar biriken rota maliyeti.
- h(n): Mevcut hücreden hedefe kalan tahmini maliyet. Burada Manhattan uzaklığı kullanılır.

Öncelik f(n) = g(n) + h(n) olur. Düşük f değerli adaylar önce genişletilir. h(n), hedefe kalan hücre uzaklığını tahmin ettiği için A* aramayı hedefe doğru yönlendirir. Kullanılan h değeri, her hücrenin en az 1 maliyetli olduğu durumda gerçek maliyeti aşmayan bir kestirimdir.

Kırmızı hücre duvar değildir. Onun yerine kırmızıdan geçmenin maliyeti yükseltilir: boş hücre 1, kırmızı yiyecek hücresi 16 maliyetlidir. Böylece A* kırmızıdan dolaşan makul bir rota bulabiliyorsa onu tercih eder; zorunlu kalırsa kırmızı hücreden de geçebilir.

### 4.2 Dijkstra: kestirimsiz en düşük maliyetli arama

Dijkstra da aynı hücre maliyetlerini kullanır, ama hedefe kalan uzaklığı hesaplayan bir sezgisel değer kullanmaz. Yalnızca şimdiye kadarki rota maliyetine göre arama yapar; g(n) önceliklidir.

Graf ağırlıkları negatif olmadığı için ulaşılan hedefin maliyeti en düşük rotayı verir. Bunun bedeli çoğunlukla daha fazla hücreyi incelemesi ve daha uzun planlama süresidir. A* ile Dijkstra’yı birlikte ölçmek, hedefe yönelik sezgisel kestirimin hız farkını göstermeye yarar.

### 4.3 Greedy Best-First: en yakın görünen hedefe yönelme

Greedy Best-First, önce h(n), yani hedefe kalan Manhattan uzaklığı küçük olan arama hücrelerini seçer. Birikmiş rota maliyeti yalnızca eşitlik bozucudur. Uygulaması hedefe doğrudan yönelir ve çoğu zaman daha az arama yapar; ancak toplam maliyeti en düşük rotayı bulacağı garanti değildir. Kırmızı hücreleri veya dolambaçlı yolları A* kadar iyi değerlendirmeyebilir.

### 4.4 Manhattan: aramasız, yerel karşılaştırma

Manhattan yöntemi A*, Dijkstra ve Greedy gibi tahta üzerinde rota grafiği aramaz. Ajanın o an yapabileceği hareketleri projekte eder ve her hareketten sonra hedefe kalan Manhattan uzaklığını puanlar. Kırmızıya çarpma cezası ve öğrenilmiş Q değeri de karara katılır.

Bu yöntem, daha kapsamlı planlamanın katkısını ölçmek için basit bir taban çizgisidir. Yakın çevrede iyi karar verebilir; fakat uzaktaki engelleri veya uzun vadeli dolambaçları aramayacağı için takılabilir. Seed 50 deneyinde 4.000 adım sınırına ulaşıp 40 yeşilin 39’unu toplaması bu sınırlamaya bir örnektir.

## 5. Hız ve gerçek hareketi aramaya nasıl yansıttık?

Ajan bir eylem seçtiğinde yalnızca bir hücre değil, hızı kadar hücre ilerleyebilir. Örneğin hızı 3 olan “Right” eylemi, önünde yiyecek veya tahta kenarı yoksa üç hücre ilerler. Sadece bir hücrelik adımlardan oluşan bir yol araması ajanın gerçek hareketini yanlış modelleyebilir.

Bu nedenle A*, Dijkstra ve Greedy arama grafiğinde bir kenar, ajanın bir eylemde gidebildiği en fazla 1–3 hücrelik hareketi temsil eder. Hareket yeşil yiyeceğe, kırmızı yiyeceğe veya tahtanın kenarına ulaşınca erken biter. Arama maliyeti geçilen hücreleri hesaba katar.

Hız ve konuma göre bazı hücrelere bir rotayla erişmek zor olabilir. Ajan ilk tercihindeki hedefe gidemiyorsa başka yeşil hedef arar. Bu, planlayıcının erişilemeyen tek bir yiyeceği tekrar tekrar seçmesine karşı ek bir korumadır.

## 6. Planlanan rota ile Q-öğrenmeyi nasıl birleştirdik?

Yol bulma bir sonraki hareket yönünü önerir; Q tablosuysa ajanın deneyiminden öğrendiği hareket değerini ekler. Son karar böylece hem mevcut rotayı izler hem geçmişte ödül getiren eylemleri dikkate alır.

Her olası eylem için kabaca şu puan hesaplanır:

- Eylemden sonra hedefe kalacak uzaklık azaldıkça puan yükselir.
- Kırmızı hücreye giden hareketin puanı ciddi biçimde düşer.
- A*, Dijkstra ve Greedy’nin önerdiği ilk yön için ek rota bonusu verilir.
- “No Action”, hedef ajanın bulunduğu hücre değilse cezalandırılır.
- Öğrenilmiş Q değeri puana eklenir.
- Bazen keşif için daha düşük puanlı ama güvenli bir eylem rastgele seçilir.

Dolayısıyla Q tablosu tek başına yolu bulmaz; planlayıcıyla birlikte karar verir. Manhattan taban çizgisinde yol planlayıcı bonusu yoktur.

## 7. Hareket, yiyecek ve çarpışma kuralları

Her simülasyon adımında önce üç ajanın gözlemleri hazırlanır ve her ajan için bir eylem seçilir. Sonra hareketler eş zamanlı mikro-adımlar halinde yürütülür. Hızı 1 olan ajan bir hücre, hızı 3 olan ajan en fazla üç hücre ilerleyebilir. Bir ajan tahtanın dışına çıkamaz. Yiyeceğe ulaşınca o ajanın o turdaki hareketi durur.

Bir hedef hücreye aynı anda birden fazla ajan giderse:

1. Yeşil yiyecek için “Left” seçen ajan varsa o kazanır.
2. Birden fazla sol hareket varsa düşük ajan numarası kazanır.
3. Sol hareket yoksa düşük ajan numarası eşitliği bozar.

Kazanan yeşil yiyeceği alır ve +1 ödül kazanır. Kırmızı yiyeceği alan −1 alır. Yiyecek tahtadan silinir. Bir ajanın ödülü kendi içinde tutulur; bölüm karşılaştırmasında üç ajanın ödülleri toplanır.

Bölüm, bütün yeşil yiyecekler toplandığında veya 4.000 simülasyon adımına ulaşıldığında tamamlanır. İkinci sınır, başarısız veya takılan bir politikanın sonsuza dek çalışmasını önler.

## 8. Öğrenme: Q-learning ve eligibility trace

### 8.1 Durum tablosu

Her ajanın her algoritma için ayrı durum-eylem değerleri vardır. Durum çok büyük olmasın diye tüm tahtayı bir anahtara yazmıyoruz. Durum özeti şu özellikleri içerir:

- seçilen hedefin ajana göre x ve y yönü,
- en yakın kırmızı yiyeceğin uzaklık aralığı,
- rakibin hedefe daha önce ulaşma ihtimali için rekabet etiketi,
- ajanın kendi hızı.

Her eylem Yukarı, Aşağı, Sol, Sağ veya No Action olabilir. Q(s,a), ilgili durum s içinde eylem a seçildiğinde beklenen uzun vadeli ödülün öğrenilmiş tahminidir.

### 8.2 Zamansal fark güncellemesi

Hareketten sonra ajan aldığı ödülü ve yeni durumu kullanarak tahminini düzeltir:

    δ = r + γ × max(Q(s′, a′)) − Q(s, a)

Burada:

- r mevcut harekette alınan ödüldür: normal hareket için 0, yeşilde +1, kırmızıda −1.
- γ = 0.90 gelecekteki ödülün bugünkü karar için ağırlığıdır.
- s mevcut durum, s′ yeni durumdur.
- a mevcut eylem, a′ sonraki durumda değerlendirilen eylemdir.
- δ tahmindeki hatadır.

Basit Q-learning yalnızca son seçilen eylemi düzeltirdi. Bu projede eligibility trace kullanıyoruz: yakın geçmişteki durum-eylem çiftlerine de iz değeri bırakılır. İzler her adımda γ × λ ile küçülür; λ = 0.75’tir. Bir ödül geldiğinde, o ödüle giden yakın geçmişteki kararlar da bir miktar güncellenir. Böylece ajan ödülü yalnızca son harekete bağlamaz.

Öğrenme oranı ziyaret sayısı arttıkça azaltılır:

    α = max(0.04, 0.30 / √(ziyaret sayısı + 1))

Daha önce çok denenmiş bir kararın değeri daha küçük adımlarla değiştirilir. Öğrenilmiş Q değerleri sayısal kararlılık için −10 ile +10 arasında tutulur.

### 8.3 Keşif ve kullanma dengesi

Ajanın keşif olasılığı ε başlangıçta 0.18’dir. ε olasılığıyla yeni, mümkünse kırmızıya götürmeyen bir hareket dener; diğer zamanlarda en yüksek puanlı hareketi kullanır.

Her algoritmanın ε değeri ayrıdır. Son 100 bölümdeki ortalama takım ödülü pozitifse ε %3 azaltılır; negatifse %5 artırılır. Değer 0.02 ile 0.25 arasında tutulur. Başarılı politika daha çok kullanılmaya başlanır; uzun süredir kötü sonuç alıyorsa ajan tekrar keşfe yönelir.

Buradaki “zamanla akıllanma” bir sinir ağı eğitimi değildir. Tablo tabanlı Q-learning, her hareket sonrasında değerleri günceller. Süreç yinelemeli çalışır; 4.000 adımlık bölümleri Python fonksiyon çağrısıyla özyinelemeli biçimde yürütmüyoruz. Bu, hem daha anlaşılırdır hem de Python çağrı yığını sınırına takılmayı önler.

### 8.4 Neden tabloları ayırdık?

Q değeri anahtarı algoritmayı, ajan numarasını, durumu ve eylemi içerir. Bu sayede:

- A* ajanının öğrendikleri Dijkstra sonuçlarına karışmaz.
- Ajan 1’in deneyimleri doğrudan ajan 2’ye yazılmaz.
- Her yöntemin keşif oranı ve performansı ayrı izlenir.

Üç ajan aynı tahtada hareket etse de kendi ödülünü alır ve kendi Q değerlerini günceller. Bölüm puanı bu üç ödülün toplamıdır.

## 9. Deney düzeni ve karşılaştırma

Tek bir algoritmanın tek bir rastgele tahtadaki sonucuna bakmak güvenilir kıyaslama değildir. Eğitim komutu eşleştirilmiş seed kullanır. Aynı turdaki A*, Dijkstra, Greedy ve Manhattan aynı seed ile açılır; böylece yiyecek yerleri, ajan başlangıçları ve hızlar aynıdır. Sonraki turda seed bir artırılır.

Bellek algoritma başına ayrı olduğu için yöntemler geçmiş deneyimlerini korur ve birbirinin tablosuna yazmaz. Her tamamlanan bölümde sonuç CSV’ye eklenir ve Q belleği diske kaydedilir.

Performans ölçülerimiz:

- Yeşil: Toplanan yeşil yiyecek adedi.
- Kırmızı: Alınan kırmızı yiyecek adedi.
- Ödül: Üç ajanın toplam ödülü.
- Adım: Bölümün tamamlanması için geçen simülasyon adımı.
- Planlama süresi: Eylem kararı ve yol planlaması sırasında ölçülen Python işlem süresi.

Planlama süresi tüm uygulamanın çalışma süresi değildir. Tahtayı çizme veya tarayıcıda gösterme süresini değil, karar hesaplamalarının ölçülen süresini gösterir.

## 10. Şu ana kadarki deney sonuçları

Eğitim tamamlandığında kayıt dosyasında dört yöntem için 30’ar bölüm, toplam 120 bölüm vardı.

### Kolay karşılaştırma: seed 42

Her renkten 40 yiyecekle algoritma başına beş bölüm çalıştırıldı. Bu beş bölümde bütün algoritmalar ortalama 40 yeşil topladı ve sıfır kırmızı aldı. Ortalama planlama süreleri:

| Yöntem | Ortalama yeşil | Ortalama kırmızı | Ortalama ödül | Planlama |
|---|---:|---:|---:|---:|
| A* | 40 | 0 | 40 | 200 ms |
| Dijkstra | 40 | 0 | 40 | 631 ms |
| Greedy Best-First | 40 | 0 | 40 | 124 ms |
| Manhattan | 40 | 0 | 40 | 135 ms |

Burada ödül üst sınıra ulaştığı için “ödül bakımından en iyi algoritma budur” sonucunu çıkaramayız. Farkı daha çok planlama süresinde görüyoruz; Dijkstra bu örnekte daha uzun hesap yaptı.

### Zor karşılaştırma: seed 50

Aynı 40 yeşil/40 kırmızı tahtası önce her algoritmanın 9. bölümünde, sonra 30. bölümünde ölçüldü:

| Yöntem | 9. bölüm: yeşil / adım | 30. bölüm: yeşil / adım | Son planlama |
|---|---:|---:|---:|
| A* | 19 / 4.000 | 40 / 95 | 57 ms |
| Dijkstra | 19 / 4.000 | 40 / 96 | 135 ms |
| Greedy Best-First | 19 / 4.000 | 40 / 158 | 99 ms |
| Manhattan | 22 / 4.000 | 39 / 4.000 | 1.823 ms |

Her iki ölçümde de kırmızı yiyecek alınmadı. Son çalışmada üç rota yöntemi bütün yeşilleri topladı; Manhattan bir yiyecekte takılıp adım sınırına ulaştı.

Bu sonuç yalnızca “ajan öğrendiği için iyileşti” anlamına gelmez. İlk ölçümden sonra hızla uyumlu rota araması ve erişilebilir başka hedefe geçiş gibi kod düzeltmeleri de yapıldı; Q tablosu da bu sırada deneyim kazandı. Değişikliklerin ve öğrenmenin etkisini ayırmak için aynı kod sürümünü sabitleyip çoklu seed’lerde, yeterli sayıda tekrar çalıştırmak gerekir. Bu rapordaki ölçümler gözlem ve kıyaslama örneğidir; istatistiksel kesinlik iddiası değildir.

## 11. Sonuçlar hangi dosyalara kaydediliyor?

### agent_memory.json

Her algoritmanın Q değerlerini, ziyaret adetlerini, bölüm sayısını, ε değerini, son ödüllerini ve arayüz grafiği için son performans satırlarını saklar. Her bölüm tamamlanınca önce geçici dosyaya yazılır, sonra asıl dosyayla değiştirilir. Uygulama yeniden açılınca bu değerler yüklenir; öğrenme sıfırlanmaz.

### training_results.csv

Her tamamlanan bölüme bir satır ekler. Seed, algoritma, bölüm numarası, yiyecek adedi, adım, yeşil/kırmızı, ödül, ε ve planlama milisaniyesi sütunları vardır. Excel veya metin düzenleyiciyle incelenebilir.

### Arayüz

app.py yerel bir HTTP sunucusu açar ve tarayıcıyı 127.0.0.1 adresine yönlendirir. index.html tahtayı, ajanları, yiyecekleri ve rakip gözlem çizgilerini gösterir. Başlat/Duraklat, yeni bölüm, yiyecek sayısı ve algoritma seçimi bulunur. Ayrıca son bölümlerin algoritma karşılaştırma tablosu ve ödül grafiği gösterilir.

Sunucu bilgisayarın dış ağına değil kendi yerel adresine bağlanır. Bölüm tamamlandıkça veriler kaydedilir; uygulama Ctrl+C ile kapatılırken öğrenme belleğini tekrar yazar.

## 12. Projeyi çalıştırma

PowerShell’i ai-lab klasöründe açın. Ortam yoksa:

    python -m venv .venv

Tarayıcı arayüzünü başlatmak için:

    .\.venv\Scripts\python.exe app.py

Başlangıçta otomatik öğrenme çalışır. Terminaldeki işlemi durdurmak için Ctrl+C kullanılır.

Algoritmaları aynı seed’lerde toplu kıyaslamak için:

    .\.venv\Scripts\python.exe app.py --train-episodes 20 --food-pairs 125 --seed 42

Bu komut her yöntem için 20 bölüm çalıştırır; dört yöntem seçiliyse toplam 80 bölüm eder. Kısa deneme için yiyecek sayısını düşürebilirsiniz:

    .\.venv\Scripts\python.exe app.py --train-episodes 5 --food-pairs 40 --seed 42

Yalnız belirli algoritmaları seçmek için:

    .\.venv\Scripts\python.exe app.py --train-episodes 20 --food-pairs 125 --seed 42 --algorithms "A*" Dijkstra Manhattan

Kod kontrolleri:

    .\.venv\Scripts\python.exe -m py_compile app.py simulation.py
    .\.venv\Scripts\python.exe simulation.py

Yeni deneyler mevcut belleği sürdürür ve CSV’ye eklenir. Baştan eğitim yapmak istenirse uygulama kapatıldıktan sonra proje içindeki agent_memory.json silinebilir. CSV’yi silmek geçmiş ölçümleri de kaldırır.

## 13. Bilinen sınırlamalar ve geliştirme fikirleri

- Manhattan yerel ve açgözlü bir yöntemdir; zor seed 50’de son bir yeşil yiyeceği alamadı. Daha iyi takılma tespiti, hedefe ilerleme sayacı veya güvenli rota yenileme eklenebilir.
- Rakibin hızını gözlemlemiyoruz. Hedef rekabeti puanında 2 hücre/tur tahmini kullanılıyor; bu bir kestirimdir, ödev kuralı değildir.
- Küme bonusu küçük bir yerel kestirimdir. Yiyecekler rastgele dağıtıldığı için düzenli bir gizli örüntü öğrenmeye çalışmıyoruz.
- Beş tur gibi küçük örneklerde sonuçlar rastgeleliğe çok bağlıdır. Güçlü karşılaştırma için çok sayıda eşleştirilmiş seed ve ortalama/dağılım raporlanmalıdır.
- 4.000 adım sınırı, çözülemeyen bölümün sonsuz sürmesini önler. Bu sınıra ulaşmak bölümün başarıyla tamamlanmadığını gösterir.
- Ödev “4 branches” ile beş hareket değerini birlikte yazmıştır. Uygulama beş hareket değerini uyguladı; sunumda bu yorum kararını açıkça belirtin.
- Öğrenme tablosu küçük, özetlenmiş durumları kullanır. Hızlı ve bağımlılıksızdır; fakat büyük veya çok çeşitli senaryolarda her olası durumu ayrı öğrenmek genelleme sorununa yol açabilir.

## 14. Sunumda sorulabilecek sorular ve kısa yanıtlar

### Bu proje ne yapıyor?

50 × 50 tahtada üç ajanı aynı ortamda çalıştırıyor. Ajanlar görünen yeşil yiyecekleri toplamaya, kırmızılardan kaçınmaya çalışıyor. Dört karar yöntemi ve çevrimiçi Q-öğrenme uygulanıyor; sonuçlar JSON ve CSV’ye kaydediliyor.

### Neden dört algoritma kullandınız?

Tek bir yöntemin iyi veya kötü görünmesinin nedenini anlamak için. A* hedefe yönelik ve maliyet/risk değerlendiriyor; Dijkstra kestirimsiz en düşük maliyeti buluyor; Greedy hedefe yakınlığı önceleyip hız karşılaştırması sağlıyor; Manhattan yöntemiyse aramasız basit taban çizgisi.

### A* nasıl karar veriyor?

Her arama hücresi için başlangıçtan gelen gerçek maliyet g ile hedefe kalan uzaklığın kestirimi h toplanıyor. En düşük g+h değerli hücre önce inceleniyor. Kırmızı hücreye girmenin maliyeti 16 olduğu için algoritma güvenli bir dolaşma yolu varsa onu tercih ediyor.

### Dijkstra ile A* arasındaki temel fark ne?

İkisi de rota maliyetini kullanıyor. Dijkstra yalnızca g maliyetini değerlendiriyor; A* g’ye hedef uzaklığı h kestirimini ekliyor. Bu yüzden A* çoğu zaman hedef yönündeki hücreleri önce inceler ve daha az hesap yapabilir.

### Q-learning ajanı tam olarak ne öğreniyor?

Her özet durum ve eylem için bir Q değeri tutuyor. Hareketten sonra aldığı ödül ile sonraki durumda tahmin edilen en iyi ödülü karşılaştırıp bu değeri güncelliyor. Yeşil ve kırmızı etkileşimlerden sonra ödül bilgisi yakın geçmişteki eylemlere eligibility trace aracılığıyla da yayılıyor.

### Ajan zamanla nasıl daha iyi oluyor?

Q değerleri her simülasyon adımında güncelleniyor ve JSON dosyasına kaydediliyor. Uygulama yeniden açıldığında aynı değerleri yüklediği için öğrenme sürüyor. Başarılı sonuçlarda keşif olasılığı azalıyor; negatif ortalamada tekrar keşif artıyor. CSV’de bölüm sonuçları karşılaştırılabiliyor.

### Ajanlar birbirlerinin tamamını görebiliyor mu?

Hayır. Karar gözleminde yalnızca en yakın rakibin konumu var. Yiyecekleri ise hepsi görebiliyor. Simülasyon motoru çarpışmayı çözebilmek için bütün konumları bilir; bu bilgi ajan gözlemine verilmez.

### Neden yiyecek kümelerine küçük bonus verdiniz?

Yakın çevrede birden fazla yeşil varsa aynı bölgeye ilerlemek birden fazla yiyeceği verimli toplamaya yardımcı olabilir. Yiyeceklerin sabit bir yerleşim kuralı olduğunu varsaymıyoruz; yalnızca mevcut tahtadaki yakınlığı puanlıyoruz.

### Seed neden önemli?

Rastgele başlangıçların tekrar üretilebilir olmasını sağlar. Aynı seed bütün yöntemlere verilince yiyecekler, başlangıç konumları ve hızlar aynı olur. Böylece algoritmaları daha adil karşılaştırabiliriz.

### Seed 50’de hangi yöntem daha başarılıydı?

30. yöntem bölümündeki kayıtta A*, Dijkstra ve Greedy 40 yeşilin tamamını aldı. A* 95, Dijkstra 96, Greedy 158 adım kullandı. Manhattan 39’da kaldı ve 4.000 adım sınırına ulaştı. Tek bir seed ve küçük örnek tüm olası tahtalar için kesin üstünlük kanıtlamaz.

### Neden Manhattan başarısız oldu?

Manhattan her adımda yakın çevreye göre yön seçer; bütün tahtada rota aramaz. Bazı durumlarda yerel seçimler hedefe ilerlemeyebilir. Bu davranış basit taban çizgisinin sınırlamasını gösteriyor; takılma tespiti eklemek bir sonraki geliştirme olabilir.

### Kırmızı yiyecek neden duvar değil?

Ödev kırmızıdan kaçınmayı istiyor ama kırmızıyı engel ilan etmiyor. Bu yüzden kırmızı hücreyi tamamen yasaklamak yerine rota maliyetini yükseltiyoruz. Yol yoksa kırmızıya basmak mümkün kalıyor; bu durumda −1 ödül uygulanıyor.

### Çarpışmada sola hareket kuralı nasıl uygulanıyor?

Aynı yeşil hücreye aynı simülasyon adımında girenler arasından sol eylemini kullanan seçiliyor. Birden fazla sol varsa düşük numaralı ajan kazanıyor. Sol kullanan yoksa yine düşük numaralı ajan seçiliyor. Böylece sonuç her çalıştırmada aynı şekilde belirleniyor.

### Bu bir sinir ağı mı?

Hayır. Bu proje standart kütüphaneyle yazılmış tabular Q-learning kullanıyor. Öğrenilmiş Q değerlerini doğrudan JSON’da saklıyoruz; sinir ağı, Unity veya ML-Agents bağımlılığı yok.

### Sonuçlardan neyi kesin söyleyebiliriz?

Seed 42’deki kolay deneylerde tüm yöntemler üst ödüle ulaştı, bu yüzden orada ödül farkı ayırt edici değildi. Zor seed 50’de rota yöntemleri Manhattan’dan daha iyi sonuç verdi. Ölçümler kod düzeltmeleri ve öğrenme birlikte ilerlerken toplandığı için gelişmenin ne kadarının sadece öğrenmeden geldiğini ayıramayız.

## 15. Sözlü anlatım için kısa sunum metni

“Ödevdeki 50’ye 50 tahtayı Python ile simüle ettim. Her bölümde üç ajan, eşit sayıda rastgele yeşil ve kırmızı yiyecek, rastgele 1–3 hücre hızı ve Manhattan veya Öklid ile seçilen en yakın rakip gözlemi bulunuyor. Yiyecekleri görebiliyorlar ama diğer ajanların hepsini göremiyorlar.

Kararları karşılaştırmak için A*, Dijkstra, Greedy Best-First ve Manhattan yöntemlerini ekledim. A* rota maliyetiyle hedef kestirimini birleştiriyor, Dijkstra yalnızca rota maliyetine bakıyor, Greedy hedefe yakınlığı önceleyip Manhattan ise aramasız yerel karar veriyor. Kırmızı yiyeceği duvar yapmak yerine maliyetini artırdım. Ajanın 1–3 hücrelik hızını da rota aramasında modelledim.

Ayrıca her ajan ve algoritma için ayrı Q tablosu tuttum. Hareketlerden gelen ödüller Q-learning ve eligibility trace ile önceki kararlara aktarılıyor. Başarıya göre keşif olasılığı uyarlanıyor. Öğrenme belleği JSON’a, bölüm ölçümleri CSV’ye kaydediliyor.

Toplam 120 bölüm çalıştırdım. Zor seed 50’de A*, Dijkstra ve Greedy bütün 40 yeşili topladı; Manhattan bir yiyecekte takıldı. Bu sonuçlar karşılaştırma sağlıyor ama kod iyileştirmeleriyle öğrenme birlikte yapıldığı için farkı yalnız öğrenmeye bağlamıyorum.”
