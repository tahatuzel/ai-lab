# BIL353 — Çok Ajanlı Yiyecek Toplama Proje Raporu

Bu rapor, üç ajanın yiyecek toplamak için yarıştığı simülasyonun kurallarını, öğrenme yöntemini ve yazılım bileşenlerini açıklar. Her bileşenin ne olduğu, ne işe yaradığı ve projede nasıl kullanıldığı kısa kod parçaları ve sayısal örneklerle anlatılır. Kurulum ve çalıştırma komutları `README.md` dosyasında yer alır.

## 1. Projenin amacı ve kapsamı

Tahtada üç oyuncu, toplanacak yeşil yiyecekler ve kaçınılacak kırmızı yiyecekler var. Her oyuncuya **ajan** diyoruz. Ajan, çevresine ilişkin bilgi alıp bir eylem seçen yazılım bileşenidir.

Her ajan kendi eylemini seçer, sonucuna göre ödül alır ve bu deneyimi sonraki seçimlerinde kullanır. Bu yönteme **pekiştirmeli öğrenme** denir. Ajan, davranışlarının sonuçlarını aldığı ödüllerden öğrenir.

Projede tablo tabanlı **Q-öğrenmesi** kullanılır. Simülasyonu Python yürütür. HTML arayüzü tahtayı gösterir ve simülasyonun kontrol edilmesini sağlar.

### Ödev gereksinimlerinin uygulamadaki karşılığı

| Gereksinim | Uygulamadaki karşılığı | Kod konumu |
|---|---|---|
| 50 × 50 tahta | Koordinatlar 0 ile 49 arasındadır. Tahtada 2.500 hücre bulunur | `simulation.py`, `BOARD_SIZE` |
| Yeşil ve kırmızı yiyecekler eşit sayıda ve rastgele yerleştirilir. Toplam yiyecek sayısı hücrelerin en fazla %30'u kadardır | Her renkten en fazla 375 yiyecek yerleştirilir. Başlangıç hücreleri tekrarsız örneklemeyle seçilir | `MAX_FOOD_PAIRS`, `Simulation.new_episode()` |
| Üç ajan | Üç `Agent` nesnesi farklı hücrelerde başlar | `Simulation.new_episode()` |
| Yalnızca en yakın rakibin konumu gözlemlenir | Gözlemde bir rakibin koordinatı yer alır | `Simulation.observation_for()` |
| Manhattan veya Öklid uzaklığı rastgele seçilir | Her turun başında bir ölçüt seçilir ve tur boyunca bütün ajanlar bu ölçütü kullanır | `new_episode()`, `step()`, `observation_for()`, `state_values()` |
| Yiyecekler gözlemlenebilir | Gözlem, bütün yeşil ve kırmızı yiyeceklerin koordinatlarını içerir | `Observation` |
| Ajan hızı 1–3 hücre arasında rastgele seçilir | Hız, ajanın bir turda kaç ardışık adım atabileceğini belirler. Her adımda en fazla bir hücre ilerler | `new_episode()`, `step()` |
| Yukarı, aşağı, sol, sağ ve bekleme | Beş ayrık eylem vardır | `ACTIONS`, `DELTAS`, `move()` |
| Yeşil için +1, kırmızı için −1 ve bağımsız ödüller | Yiyeceği toplayan ajan ödülü alır. Adımın Q güncellemesi o ajanın değerlerine uygulanır | `Agent.reward`, `move()`, `LearningMemory.learn()` |
| İki ajan aynı yeşil yiyecek için yarıştığında sola hareket edene öncelik verilmesi | Uygulama farkı. Simülasyonda ajanlar 1 → 2 → 3 sırasıyla hareket eder ve hücreye ilk ulaşan ajan yiyeceği alır | `Simulation.step()` |

Her adım tahtaya hemen uygulanır. Sıradaki adımın kararı güncel tahta üzerinden verilir. Son yeşil yiyecek toplandığında bölüm sona erer.

## 2. Yazılım bileşenleri ve görevleri

| Dosya | Görevi |
|---|---|
| `simulation.py` | Ajanlar, tahta, gözlemler, hareket, ödüller, öğrenme ve JSON belleği |
| `app.py` | Yerel web sunucusu ve HTML sayfasıyla simülasyon arasındaki iletişim |
| `index.html` | Tahta çizimi, düğmeler, ayarlar, öğrenme göstergeleri ve bölüm sonuçları |
| `README.md` | Kurulum ve çalıştırma kılavuzu |
| `report.md` | Projenin kavramlarını, yöntemini ve bileşenlerini açıklayan rapor |
| `learning_memory_v5.json` | Uygulama çalışırken oluşturulan öğrenme verileri |

Simülasyonun durumu Python tarafında tutulur. Bir ajan hareket ettiğinde önce Python konumunu günceller, ardından HTML arayüzü ajanı yeni koordinatlarında çizer. Böylece tahta kuralları Python tarafında tek yerde tanımlanır.

## 3. Kodu okumak için kısa sözlük

- **Değişken** bir değeri adlandırır. `BOARD_SIZE = 50` ifadesi tahta boyutunu bir ad altında saklar.
- **Fonksiyon** belirli bir işi yapar. `manhattan(a, b)` iki konum alır ve aralarındaki uzaklığı döndürür.
- **Döngü** bir işlemi tekrar eder. Ajanların eylemlerini seçerken ajanlar üzerinde sırayla ilerlenir.
- **Sınıf ve nesne** bir kavramın verilerini ve davranışlarını bir araya getirir. `Agent` sınıfından üç ayrı ajan nesnesi oluşturulur.
- **Liste** öğeleri sırayla saklar. Bir durumun beş Q değeri, eylem sırasına göre bir listeye yazılır.
- **Demet** bu projede `(x, y)` gibi sabit koordinat çiftlerini temsil eder.
- **Küme** benzersiz öğeleri saklar. Yiyecek koordinatları kümelerde tutulduğu için bir hücrede yiyecek olup olmadığı hızlıca belirlenebilir.
- **Sözlük** bir anahtar üzerinden ilgili değeri bulur. Durum anahtarıyla o durumun Q değerleri listesine erişilir.
- **`dataclass`** ajanın konumu ve hızı gibi alanların kısa biçimde tanımlanmasını sağlar.
- **Tür açıklaması** beklenen veri türünü belirtir. `Position = tuple[int, int]` iki tam sayıdan oluşan bir demet beklendiğini ifade eder. Kullanıcı girdisini doğrulamak için ayrıca kod gerekir.

`simulation.py` dosyasındaki `json`, `math`, `random`, `dataclasses`, `datetime` ve `pathlib` modülleri ile `app.py` dosyasındaki HTTP sunucusu Python standart kütüphanesinden gelir. Proje standart kütüphane ile çalışır.

## 4. Tahta, hücreler ve koordinatlar

Tahta 50 sütun ve 50 satırdan oluşur. Her hücre `(x, y)` çiftiyle gösterilir.

- `x` soldan sağa doğru artar.
- `y` yukarıdan aşağıya doğru artar.
- Sol üst hücre `(0, 0)`, sağ alt hücre `(49, 49)` konumundadır.

Örneğin `(10, 8)` konumundaki bir ajan sağa giderse `(11, 8)`, yukarı giderse `(10, 7)` konumuna ulaşır. Ekran koordinatlarında yukarı gitmek `y` değerini azaltır.

```python
BOARD_SIZE = 50
Position = tuple[int, int]
```

Tahtayı temsil etmek için ajan konumlarını ve yiyecek koordinatı kümelerini saklamak yeterlidir. Bir hücre iki yiyecek kümesinde de yer almıyorsa o hücrede yiyecek yoktur.

## 5. Rastgele başlangıç tahtasının oluşturulması

### Yiyecek sayısında %30 sınırı

```text
50 × 50 = 2.500 hücre
2.500 × 0,30 = 750 yiyecek hücresi
750 / 2 = her renkten en fazla 375 yiyecek
```

Kodda bu üst sınır `MAX_FOOD_PAIRS` ile hesaplanır.

```python
MAX_FOOD_PAIRS = BOARD_SIZE * BOARD_SIZE * 30 // 100 // 2
```

Kullanıcı 125 girerse 125 yeşil ve 125 kırmızı olmak üzere toplam 250 yiyecek yerleştirilir. `food_pairs`, her bir rengin yiyecek sayısını belirtir.

### Ayrı hücrelerin seçilmesi

`Simulation.new_episode()` yiyecekler ve ajanlar için tekrarsız bir hücre listesi seçer.

```python
cells = self.rng.sample(range(BOARD_SIZE ** 2), self.food_pairs * 2 + 3)
positions = [(cell % BOARD_SIZE, cell // BOARD_SIZE) for cell in cells]
```

`range(2500)` hücreleri 0 ile 2499 arasında numaralandırır. `sample`, her numarayı en fazla bir kez seçer. Hücre numarası, bölüm ve kalan işlemleriyle koordinata dönüştürülür. Örneğin 102 numaralı hücrenin koordinatı şöyle bulunur.

```text
x = 102 % 50 = 2
y = 102 // 50 = 2
position = (2, 2)
```

İlk `food_pairs` hücre yeşil yiyeceklere, sonraki aynı sayıdaki hücre kırmızı yiyeceklere ayrılır. Son üç hücre ajanların başlangıç konumlarıdır. Böylece başlangıçta yiyecekler ve ajanlar ayrı hücrelere yerleşir.

Her ajanın hızı `randint(1, 3)` ile belirlenir. Hız, ajanın bir turda art arda kaç adım atabileceğini gösterir. Bölüm boyunca sabit kalır ve sonraki bölümün başında yeniden seçilir.

`random.Random(seed)` bir rastgele sayı üreteci oluşturur. Aynı rastgelelik tohumu (`seed`) ve aynı işlem sırası, seçimleri yeniden üretmeyi sağlar. Bu özellik test ve hata incelemelerinde kullanılır.

## 6. Manhattan uzaklığı

Manhattan uzaklığı, iki nokta arasındaki yatay ve dikey farkların mutlak değerlerini toplar. Izgara üzerindeki bir tahta için bu değer, iki nokta arasındaki yatay ve dikey hücre adımlarını sayar.

```text
d = |x₁ − x₂| + |y₁ − y₂|
```

Dikey çizgiler mutlak değeri gösterir. Örneğin `(2, 3)` ile `(5, 7)` arasındaki Manhattan uzaklığı 7'dir.

```text
|2 − 5| + |3 − 7| = 3 + 4 = 7
```

`simulation.py` dosyasındaki hesaplama şöyledir.

```python
def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])
```

Turun ölçütü Manhattan ise simülasyon bu hesabı en yakın rakibi belirlemek, yeşil yiyecekleri sıralamak, rakiple hedefe olan uzaklıkları karşılaştırmak ve bir adımın hedefe yaklaştırıp yaklaştırmadığını belirlemek için kullanır. Turun ölçütü Öklid olduğunda aynı hesaplamalar Öklid uzaklığıyla yapılır.

Bir hedefe kaç tam turda ulaşılacağı ajanın hızına ve üç ajanın seçtiği eylemlere de bağlıdır.

## 7. Öklid uzaklığı ve turun ölçütünün seçilmesi

Öklid uzaklığı, iki nokta arasındaki düz çizginin uzunluğudur.

```text
d = √((x₁ − x₂)² + (y₁ − y₂)²)
```

Önceki örnekte sonuç `√(3² + 4²) = 5` olur. Python'daki `math.dist` fonksiyonu bu hesabı yapar.

Ödevde en yakın rakibin belirlenmesi için iki uzaklık ölçütünden birinin rastgele seçilmesi istenir. Simülasyon turun ölçütünü rakip ve hedefle ilgili bütün uzaklık hesaplarında kullanır. Ajanlar adımlarını dört ana yönden veya bekleme eyleminden seçer.

Örneğin ajan `(0, 0)`, rakipleri ise `(3, 3)` ve `(0, 5)` konumlarında olsun.

| Rakibin konumu | Manhattan uzaklığı | Öklid uzaklığı |
|---|---:|---:|
| `(3, 3)` | 6 | Yaklaşık 4,24 |
| `(0, 5)` | 5 | 5 |

Manhattan ölçütüyle `(0, 5)` konumundaki rakip, Öklid ölçütüyle `(3, 3)` konumundaki rakip daha yakındır.

```python
# observation_for() ve state_values()
distance = DISTANCES[self.metric]
```

`DISTANCES`, `Manhattan` adını `manhattan` fonksiyonuna, `Euclidean` adını `math.dist` fonksiyonuna eşler. İlk ölçüt yeni bölüm açılırken seçilir. Tam tur bittiğinde ve bölüm sürüyorsa bir sonraki turun ölçütü yeniden rastgele seçilir. Bir tur içinde bütün ajanlar ve adımlar aynı ölçütü kullanır. İki rakip seçili ölçüte göre aynı uzaklıktaysa ajan numarası küçük olan rakip gözleme alınır.

## 8. Ajanın gözlem bilgileri

**Gözlem**, ajanın karar verirken kullanabildiği bilgileri bir araya getirir. `Observation` şu alanları içerir.

```python
position       # Ajanın kendi konumu
speed          # Ajanın kendi hızı
green_foods    # Bütün yeşil yiyeceklerin konumları
red_foods      # Bütün kırmızı yiyeceklerin konumları
nearest_agent  # En yakın rakibin konumu
```

Gözleme rakiplerden yalnızca en yakınının konumu eklenir. Ajanın hız bilgisi kendi hızıyla sınırlıdır. Yiyecek koordinatları değiştirilemez `frozenset` kümeleri olarak aktarılır. Ajan, kararını hazırlarken simülasyonun yiyecek verilerini değiştiremez.

Simülasyon, tahtayı yönetmek ve arayüzde çizmek için üç ajanın da konumunu tutar. `observation_for()`, karar koduna yalnızca ilgili ajanın kullanabildiği bilgileri gönderir.

## 9. Beş eylemin kodda gösterimi

```python
ACTIONS = ("Up", "Down", "Left", "Right", "No Action")
DELTAS = ((0, -1), (0, 1), (-1, 0), (1, 0), (0, 0))
```

`ACTIONS` ve `DELTAS` dizilerindeki aynı indisler birbirine karşılık gelir.

| İndis | Eylem | Konum değişimi |
|---:|---|---|
| 0 | Yukarı (`Up`) | `(0, -1)` |
| 1 | Aşağı (`Down`) | `(0, 1)` |
| 2 | Sol (`Left`) | `(-1, 0)` |
| 3 | Sağ (`Right`) | `(1, 0)` |
| 4 | Bekle (`No Action`) | `(0, 0)` |

Yön eylemlerinde `x` ve `y` koordinatlarından yalnızca biri değişir. Bu nedenle hareket yatay veya düşeydir. Ajan yerinde kalmak için `No Action` eylemini seçer.

Ödev metninde “4 branches” ifadesiyle birlikte beş eylem açıkça listelenir. Uygulama bu beş eylemi kullanır ve ajan her adımda bunlardan birini seçer.

## 10. Hızlı bir ajan adımlarını nasıl kullanır?

Hızı 3 olan ajan art arda en fazla üç adım yapar. Her adımda güncel tahtayı gözlemler, en fazla bir hücre ilerler ve yönü yeniden seçebilir.

Örneğin hızı 3 olan bir ajan `(4, 5)` konumunda başlasın. Tahtada `(5, 4)` konumunda ve başka hücrelerde yeşil yiyecek olsun. Ajan sağa giderek `(5, 5)` konumuna, ardından yukarı giderek `(5, 4)` konumuna ulaşabilir. Yiyeceği hemen toplar ve üçüncü adımında başka bir yiyeceğe yönelebilir. Son yeşil yiyecek toplandığında bölüm hemen biter.

`No Action` eylemini seçmek veya tahta sınırının dışına doğru hareket etmeye çalışmak bir adım hakkı kullanır ve ajan bulunduğu hücrede kalır. `project()`, tahta sınırını hesaba katarak aday eylemin sonunda ajanın bulunacağı hücreyi belirler. `move()` seçilen eylemi uygular, ulaşılan hücredeki yiyeceği tahtadan kaldırır ve o adımın ödülünü döndürür.

## 11. Sıralı adımlar ve yiyecek rekabeti

Her tam turda ajanlar **ajan 1 → ajan 2 → ajan 3** sırasıyla hareket eder. Bir sonraki ajan ancak sırası gelen ajan adım haklarını kullandığında hareket etmeye başlar.

`Simulation.step()`, sırası gelen ajanın bir adımını yürütür. Ajan bir yiyeceğe ulaşırsa yiyecek hemen tahtadan kaldırılır ve onu toplayan ajan yeşil için +1, kırmızı için −1 ödül alır. Sonraki adım güncel tahtaya göre seçilir. Ajanın hakkı varsa bir sonraki adım yine ona aittir. Hakları tükendiğinde sıra bir sonraki ajana geçer.

Örneğin 1. ve 2. ajan aynı yeşil yiyeceğe ulaşabilecek konumda olsun. 1. ajan yiyeceği topladığında 2. ajan kalan yiyeceklere göre seçim yapar. Toplanan yiyecek son yeşil ise kalan adımlar uygulanmadan bölüm biter.

Birden fazla ajan aynı hücrede bulunabilir. Birkaç ajan aynı yiyeceğe erişebildiğinde sabit sıra, önce hareket eden ajana avantaj sağlayabilir.

## 12. Ödül, durum ve Q değeri

- **Ödül (`r`)** adımın sonucudur. Ajan yeşil topladığında +1, kırmızı topladığında −1, yiyecek toplamadığında 0 alır.
- **Durum (`s`)** ajanın karar verirken karşılaştığı koşulları özetler. Örneğin hedef sağ üstte olabilir, ajanın hızı 2 olabilir ve solda kırmızı yiyecek riski bulunabilir.
- **Q değeri (`Q(s,a)`)** ajan `s` durumunda `a` eylemini seçtiğinde elde etmeyi beklediği toplam indirgenmiş ödülün tahminidir.

Puan, ajanın şimdiye kadar topladığı ödüllerle hesaplanır. Q değeri ise bir eylemin beklenen getirisini ifade eder. Örneğin ajanın puanı 7 iken belirli bir durumda sağa gitmenin Q değeri 0,35 olabilir.

`Agent.reward` ajanın puanını hesaplar.

```python
@property
def reward(self):
    return self.green - self.red
```

12 yeşil ve 3 kırmızı yiyecek toplayan ajanın puanı `12 − 3 = 9` olur. Arayüzde üç ajanın toplam puanı da gösterilir. Her ajan, yalnızca kendi topladığı yiyeceklerin ödülünden öğrenir.

## 13. Tahtanın durum anahtarıyla özetlenmesi

Olası her tahta düzeni için Q tablosunda ayrı bir kayıt açmak çok fazla bellek gerektirir. `Simulation.state_values()` bunun yerine daha küçük bir durum anahtarı oluşturur.

Ajan, turun uzaklık ölçütüne göre en yakın iki yeşil yiyeceği sıralar. Gördüğü rakip aynı ölçüte göre birinci yiyeceğe kendisinden daha yakınsa ikinciyi hedefler. Tahtada tek yeşil yiyecek varsa hedef o yiyecektir. Ajanın iki yiyeceğe uzaklığı eşitse koordinat sırası belirleyici olur. Durum anahtarı seçilen hedefi ve turun ölçütünü içerir.

| Parça | Anlamı | İşlevi |
|---|---|---|
| Ajan numarası | 1, 2 veya 3 | Ajanların Q kayıtlarını birbirinden ayırır |
| `sx,sy` | Hedefin yatay ve düşey yönü (`−1`, `0` veya `+1`) | Hedefe hangi yönde yaklaşılabileceğini özetler |
| `v` | Ajanın hızı | Ajanın tur başına kaç adım hakkı olduğunu belirtir |
| `m` | Yaklaşan adım dahil olmak üzere ajanın mevcut turunda kalan adım sayısı | Bir sonraki adımın aynı ajana mı, rakiplerden birine mi ait olacağını ayırt etmeye yarar |
| `r` | Dört hareket yönündeki kırmızı yiyecek riskinin bit maskesi | Yakındaki tehlikeleri gösterir |
| `g` | Bu adımda yeşil yiyecek toplanan yönlerin bit maskesi | Anında ödül getiren yönleri gösterir |
| `p` | Turun ölçütüne göre hedefe uzaklığı azaltan yönlerin bit maskesi | Tahta sınırı dahil olmak üzere her yöndeki tek adımın sonucunu özetler |
| `d` | Turun uzaklık ölçütü, `Manhattan` veya `Euclidean` | Farklı ölçütlerle oluşturulan Q durumlarını ayırır |

Örnek durum anahtarı

```text
1|1,-1|v2|m1|r4|g0|p9|dManhattan
```

Bu anahtar, hızı 2 olan 1. ajana aittir ve ajanın turunda bir adım hakkı kalmıştır. Hedef sağ üsttedir. Turun ölçütü Manhattan uzaklığıdır (`dManhattan`). Sola gidildiğinde kırmızı yiyeceğe ulaşılır (`r4`). Tek adımda yeşil yiyecek toplanamaz (`g0`). Yukarı ve sağ yönleri ajanı hedefe yaklaştırır (`p9 = 1 + 8`).

### Yön işaretleri nasıl hesaplanır?

```python
sx = (dx > 0) - (dx < 0)
```

Python’da bu işlemde `True` değeri `1`, `False` değeri `0` olarak kullanılır. `dx` pozitifse `1 − 0 = 1`, negatifse `0 − 1 = −1`, sıfırsa `0 − 0 = 0` elde edilir. Aynı işlem `y` koordinatı için de uygulanır.

### Bit maskesi nasıl çalışır?

Dört yöndeki evet/hayır bilgisi bir sayıda tutulur. Özelliğin geçerli olduğu yönlerin değerleri toplanır.

| Yön | Özellik geçerliyse eklenen değer |
|---|---:|
| Yukarı | 1 |
| Aşağı | 2 |
| Sol | 4 |
| Sağ | 8 |

Sol ve sağ yönler riskliyse `r = 4 + 8 = 12` olur. `1 << action` ifadesi ilgili eylemin değerini üretir. Üç bit maskesi de aynı kodlamayı kullanır. Örneğin sağda bir hücre uzaklıkta tek bir yeşil yiyecek varsa `g8` ve `p8` elde edilir. Yiyecek sağda iki hücre uzaklıktaysa `g0` ve `p8` elde edilir. Her iki durumda da ajan, hızı kaç olursa olsun o adımda en fazla bir hücre ilerler.

Rakip bilgisi, en yakın yeşil yiyeceğe olan uzaklıkları karşılaştırıp hedefi seçmek için kullanılır. Ajana rakibin hızı verilmez.

Farklı tahta düzenleri aynı anahtarı üretebilir. Örneğin hızı 1 olan bir ajan için iki hücre sağdaki hedef ile on hücre sağdaki hedef, diğer özellikler aynı kaldığında aynı durum anahtarını oluşturur. Ajanın göremediği rakibin adımları da tahtanın bir sonraki durumunu etkileyebilir.

## 14. Q tablosunun saklanması

`LearningMemory.q_values`, her durum anahtarını beş Q değerinden oluşan bir listeyle eşleştiren bir sözlüktür.

```json
{
  "1|1,-1|v2|m1|r4|g0|p9|dManhattan": [0.05, 0.0, 0.0, 0.05, 0.0]
}
```

Listenin sırası her zaman `Up`, `Down`, `Left`, `Right`, `No Action` biçimindedir. Örnekte yukarı ve sağa gitmek ajanı hedefe yaklaştırdığı için bu eylemlerin başlangıç değeri 0,05’tir. Kırmızı yiyecek riski durum anahtarında yer alır. Ajan ilgili eylemi denediğinde aldığı ödül Q değerine yansır.

Aynı anahtara ait `visits` listesi her eylemin kaç kez güncellendiğini saklar.

```json
{
  "1|1,-1|v2|m1|r4|g0|p9|dManhattan": [3, 0, 1, 7, 0]
}
```

Bu kayıtta yukarı 3, sol 1, sağ 7 kez güncellenmiştir. Ziyaret sayıları öğrenme sürecini incelemek için tutulur. Öğrenme oranı sabittir.

Ajan numarası durum anahtarında yer aldığı için 1. ajanın ödülü yalnızca 1. ajana ait kaydı etkiler. Kayıtlar tek bir sözlükte, ajan numarasına göre ayrı tutulur.

Bir sonraki durumun değerlerine bakılırken de yeni bir kayıt açılabilir. Dolayısıyla “Öğrenilen durum” sayısına, henüz eylem seçilmemiş ve güncelleme yapılmamış kayıtlar da dahildir. Arayüzdeki “Q güncellemesi” sayacı, `visits` listelerindeki tüm sayaçların toplamını gösterir.

## 15. Yeni bir durumda başlangıç tercihleri

Ajanı seçilen hedefe yaklaştıran eylemler 0,05 Q değeriyle başlar. Bekleme dahil diğer eylemlerin başlangıç değeri sıfırdır. Bu küçük fark, ajan henüz deneyim edinmemişken hedefe yaklaşmayı destekler.

Hedefe yaklaştıran bir eylemin başlangıç değeri, eylem yeşil veya kırmızı yiyecekle ya da boş hücreyle sonuçlansa da 0,05’tir. `g` ve `r` maskeleri bu durumları birbirinden ayırır. Ajan ödül aldıkça söz konusu durumlara farklı Q değerleri atayabilir.

`LearningMemory.values()`, bir durum ilk kez görüldüğünde başlangıç değerlerini kaydeder. Daha sonraki karşılaşmalarda tablodaki güncel Q değerleri kullanılır. Ortam, adımda toplanan yiyeceğe göre +1, −1 veya 0 ödül verir.

## 16. Eylem seçimi ve ε-açgözlü yöntem

Ajan çoğu zaman en iyi görünen eylemi seçer. Zaman zaman **keşif** yaparak başka eylemleri de dener.

`Simulation.choose_action()` eylemi şu şekilde seçer.

```python
if self.rng.random() < self.memory.epsilon:
    return self.rng.randrange(len(ACTIONS))
best = max(values)
return self.rng.choice([i for i, value in enumerate(values) if value == best])
```

- Ajan `ε` olasılıkla beş eylemden birini rastgele seçer.
- Kalan olasılıkla en yüksek Q değerine sahip eylemi seçer.
- En yüksek değeri birden fazla eylem paylaşıyorsa bu eylemler arasından rastgele seçim yapar.

Başlangıçta `ε = 0.20` olduğu için ortalama her beş adımdan birinde keşif yapılır. Her adım için seçim olasılığı bağımsız olarak uygulanır.

Keşif oranı tamamlanan bölüm sayısıyla azalır.

```python
max(0.05, 0.20 * 0.97 ** episodes)
```

İlk bölümde oran 0,20’dir. On bölüm tamamlandığında yaklaşık 0,147 olur. Alt sınır 0,05’tir. Ajan zamanla öğrendiği eylemleri daha sık seçer ve keşif yapmayı da sürdürür.

Üç ajanın Q değerleri ayrı, α, γ ve ε değerleri ortaktır. Keşif sırasında kırmızı yiyeceğe ulaşan ajan, aldığı negatif ödülden öğrenir.

## 17. Q-öğrenmesinin matematiği

`Q(s,a)`, ajanın `s` durumunda `a` eylemini seçtiğinde kendi adımları boyunca elde etmeyi beklediği toplam indirgenmiş ödülü tahmin eder. Ajan yeşil yiyeceği iki adım sonra toplarsa bu ödül bugünkü tahmine `γ² × 1` kadar katkı yapar. `γ = 0.90` olduğunda katkı 0,81’dir. Bu sayede yiyeceği hemen toplamasa da ajana avantaj sağlayan hazırlık adımları değerlendirmeye katılır.

Güncelleme önce hedef değeri, ardından zamansal farkı (`δ`) hesaplar.

```text
target = r + γ × max Q(s′,a′)
δ = target − Q_old(s,a)
Q_new(s,a) = Q_old(s,a) + α × δ
```

| Sembol | Anlamı | Bu projedeki karşılığı |
|---|---|---|
| `s` | Adım öncesindeki durum | Durum anahtarı |
| `a` | Seçilen eylem | Beş eylemden biri |
| `r` | Adımın ödülü | +1, −1 veya 0 |
| `s′` | Aynı ajanın bir sonraki karar anındaki durumu | Güncel tahta ve o anda kalan adım sayısı |
| `max Q(s′,a′)` | Yeni durumdan beklenen en yüksek getiri | Beş Q değerinin en büyüğü |
| `α` | Öğrenme oranı | 0,20 |
| `γ` | Gelecekteki ödüllerin ağırlığı | 0,90 |

### α ne işe yarar?

Öğrenme oranı α, eski Q tahmininin yeni hedefe ne kadar yaklaşacağını belirler. 0,20 değeri, eski tahmin ile hedef arasındaki farkın %20’sinin kapatılması anlamına gelir. Önceki deneyimlerin etkisi böylece korunur.

### γ ne işe yarar?

γ, sonraki adımlardan beklenen ödüllerin ağırlığını belirler. Örneğin yeni durumdaki en iyi Q değeri 0,4 ise bunun hedefe katkısı `0.9 × 0.4 = 0.36` olur.

### Ajan bir sonraki durumu ne zaman gözlemler?

Ajanın adım hakkı kaldıysa bir sonraki durum, az önce uyguladığı eylemden sonraki tahtaya göre belirlenir. Ajan turunu bitirdiyse diğer ajanlar kendi adımlarını tamamlayınca yeniden karar verir. Örneğin 1. ajan son adımında yeşil bir yiyeceğe yaklaşabilir ve 2. ajan, 1. ajanın sırası yeniden gelmeden o yiyeceği toplayabilir. 1. ajan önceki adımını karşısındaki güncel tahtaya göre günceller. Yiyeceği toplayan 2. ajan +1 ödül alır.

Bir sonraki karar anındaki Q değerleri `[0.1, 0.4, −0.2, 0.2, −0.05]` olsun. Gelecek getiri tahmini 0,4’tür. Ödül 0 ve eski Q 0,1 ise hedef 0,36, zamansal fark 0,26 ve yeni Q değeri `0.1 + 0.2 × 0.26 = 0.152` olur. Ajan keşif sırasında başka bir eylem seçse bile güncelleme 0,4’ü kullanır. Q-öğrenmesi bu nedenle **politika dışı (off-policy)** bir yöntemdir. Hedef hesabı tahmini en yüksek eylem değerini kullanır ve keşif sırasında fiilen seçilen eylemden bağımsızdır.

### Sayısal örnek — yeşil yiyecek

Eski Q değeri 0,1, ödül +1 ve yeni durumdaki en yüksek Q değeri 0,4 olsun.

```text
Hedef           = 1 + 0.9 × 0.4 = 1.36
Zamansal fark   = 1.36 − 0.1 = 1.26
Yeni Q          = 0.1 + 0.2 × 1.26 = 0.352
```

Ajan aynı durum anahtarıyla yeniden karşılaştığında bu eylemin Q değeri 0,352 olur.

### Sayısal örnek — kırmızı yiyecek

Eski Q ve gelecek Q değerleri aynı kalsın, ödül −1 olsun.

```text
Hedef   = −1 + 0.9 × 0.4 = −0.64
Yeni Q  = 0.1 + 0.2 × (−0.64 − 0.1) = −0.048
```

Eylemin Q değeri düşer. Benzer deneyimler tekrarlandıkça kırmızı yiyeceğe götüren eylemin değeri yeniden değişebilir.

### Bölüm bitince ne değişir?

Bölüm sonunda daha sonra alınacak ödül kalmadığı için `future = 0` kullanılır. Son yeşili toplayan ajanın seçtiği eylemin eski Q değeri 0,1 ise güncelleme şöyle olur.

```text
Hedef   = 1
Yeni Q  = 0.1 + 0.2 × (1 − 0.1) = 0.28
```

Bölüm son yeşil toplandığında veya 4.000 tam tur tamamlandığında biter. Güncellenmeyi bekleyen her adım için kendi anlık ödülü ve sıfır gelecek Q değeri kullanılır. Örneğin başka bir ajan son yeşili topladığında bekleyen bir adımın ödülü 0 ise o adımın hedefi de 0 olur.

### Kodda Q güncellemesi

Güncellemeyi `LearningMemory.learn()` yapar.

```python
old = values[action]
future = 0.0 if terminal else max(next_values)
target = reward + GAMMA * future
values[action] += ALPHA * (target - old)
self.visits[key][action] += 1
```

Arayüz, son adımda yapılan güncellemelerde hesaplanan eski Q, ödül, gelecek Q, hedef ve yeni Q değerlerini gösterir. Yalnızca güncellenen durum-eylem çiftinin ziyaret sayısı 1 artar.

### Neden tablo tabanlı Q-öğrenmesi?

Her ajanın beş ayrık eylemi ve özetlenmiş bir gözlemi vardır. Dolayısıyla her durum için beş sayı saklamak yeterlidir. Bir adımın Q değerlerini nasıl değiştirdiği arayüzden ve JSON dosyasından izlenebilir. Algoritma doğrudan gözlenen geçişlerden öğrenir. Rakiplerin karar kuralları ve tahtadaki geçiş olasılıkları için ayrı bir model kurmaya gerek kalmaz.

| Yöntem | Bu proje açısından değerlendirme |
|---|---|
| En yakın yeşile yönelen sabit sezgisel kural | Uygulaması kolaydır ve karşılaştırma için başlangıç noktası sağlar. Ajan her kararda aynı kuralı uygular. |
| SARSA | Benzer bir Q tablosu kullanır. Hedef hesabına, bir sonraki adımda gerçekten seçilen eylemin Q değeri girer. Bu projede Q-öğrenmesi, keşif sürerken tahmini en iyi eylemin değerini öğrenmek için seçildi. |
| Monte Carlo öğrenmesi | Bir adımın değeri, bölüm bittiğinde gözlenen toplam ödülle güncellenebilir. Bölümler 4.000 tura kadar sürebildiği için bu projede güncelleme, aynı ajanın bir sonraki kararında yapılır. |
| Derin Q Ağı (DQN) | Değerleri bir sinir ağıyla tahmin eder. Ham tahta verileri veya daha geniş gözlemler için değerlendirilebilir. Mevcut durum özeti, her güncellemenin doğrudan incelenebildiği bir tabloya sığar. |

Tahtanın tamamı ile diğer ajanların kararları durum anahtarına sığmadığı için aynı gözlem farklı sonuçlar verebilir. Bu nedenle öğrenmeyi değerlendirirken yeni tahtalardaki performans, eğitim öncesindeki başlangıç politikasıyla karşılaştırılır.

## 18. Adım, tur ve bölüm akışı

Bir **adım**, ajanın bir eylem seçip sonucunu almasıdır. Her hareket adımında en fazla bir hücre ilerlenir. Bir **tur**, üç ajanın sırayla kendi adım haklarını kullanmasıyla tamamlanır. Bir **bölüm** yeni bir tahtayla başlar ve son yeşil yiyecek toplandığında veya 4.000 tam tur tamamlandığında biter.

`Simulation.step()` tek bir adımı yürütür. Arayüz her adımı ayrı ayrı gösterebilir.

1. Sıradaki ajan için güncel gözlemi ve Q değerlerini hazırla. Durum anahtarına kalan adım sayısını da ekle.
2. Ajanın güncellenmeyi bekleyen bir önceki adımı varsa bu gözlemdeki Q değerlerini kullanarak güncelle.
3. Ajan, Q değerlerini ve ε'yı kullanarak yeni bir eylem seçer. `move()` eylemi uygular ve ajanın ödülünü döndürür. Ajanın bir adım hakkı harcanır ve adım, sonraki Q güncellemesi için beklemeye alınır.
4. Yeşil yiyecek kalmadıysa veya 3. ajanın son adımı 4.000. tam turu tamamladıysa bölümü bitir. Bekleyen bütün adımları gelecek Q değeri sıfır olacak şekilde güncelle, sonucu kaydet ve 1. ajanla yeni bir tahta başlat.
5. Bölüm sürüyorsa ajan kalan adım haklarını kullanır. Adım hakkı bittiğinde sıradaki ajana geçilir.

Her adım için yeni bir gözlem hazırlanır. 2. ajan, tahtayı 1. ajan bütün adımlarını kullandıktan sonra görür. 3. ajan ise ilk iki ajanın adımları bittikten sonraki tahtayı görür.

Bölüm sırasında `step_count` tamamlanan tam turları sayar. Sonuçtaki `steps` alanı, son yeşilin toplandığı kısmi turu da sayar. Örneğin ilk turda 2. ajanın adımında biten bir bölüm 1 tur olarak kaydedilir.

### Aynı ajanın art arda iki adımı

1. ajanın `(4, 5)` konumunda olduğunu, hızının 2 ve son yeşil yiyeceğin `(5, 4)` konumunda olduğunu düşünelim. Ajan sağa, ardından yukarı giderek yiyeceğe ulaşabilir.

- İlk adımda sağa gidip `(5, 5)` konumuna gelir ve 0 ödül alır.
- Bir adım hakkı daha vardır. Güncel tahtayı gözlemler ve sağa gittiği adımı bu durumun Q değerleriyle günceller.
- Yukarı gider, `(5, 4)` konumundaki yeşili toplar ve +1 ödül alır. Bölüm sona erer.
- Son adımın güncellemesinde gelecek Q değeri sıfırdır. Yukarı eyleminin başlangıç Q değeri 0,05 ise yeni değeri `0,05 + 0,2 × (1 − 0,05) = 0,24` olur.
- Bölüm sonucu geçmişe eklenir ve yeni tahta 1. ajanla başlar.

Yeni bölüme başlarken mevcut Q tablosu kullanılır.

## 19. Öğrenme verileri JSON'a nasıl kaydedilir?

**JSON**, sözlükleri ve listeleri saklamak için kullanılan yaygın bir metin biçimidir. Uygulama kapanınca bellekteki Python nesneleri silinir. Bunları bir dosyaya yazarak sonraki çalıştırmada geri yükleyebiliriz.

`LearningMemory.save()` aşağıdaki alanları kaydeder.

| Alan | İçerik |
|---|---|
| `version` | Dosya biçiminin sürümü |
| `episodes` | Tamamlanan bölüm sayısı |
| `q_values` | Ajanların durum-eylem değerleri |
| `visits` | Her durum-eylem çifti için güncelleme sayısı |
| `history` | Tamamlanan bölümlerin ayarları ve sonuçları |

Geçmişteki her satırda tarih, bölüm numarası, renk başına yiyecek sayısı, başlangıçtaki rastgelelik tohumu (`seed`), son turun uzaklık ölçütü (`metric`), α/γ/ε değerleri, tur sayısı, toplanan yeşil ve kırmızı yiyeceklerin sayısı, toplam ödül ve her ajanın hızı ile puanı yer alır. Geçmişe yalnızca `turn_order: "sequential"` işaretli sonuçlar alınır. Q değerleri, güncelleme sayıları ve keşif oranını belirleyen toplam bölüm sayacı, geçmişteki kayıt sayısından bağımsız olarak saklanır.

Q değeri listesindeki her sıranın hangi eyleme karşılık geldiğini `ACTIONS` belirler. `/api/memory` yanıtı, eylem adlarını ve güncel katsayıları da içerir.

### Her adımda tahta kaydediliyor mu?

Öğrenmeye devam etmek için güncel Q değerleri ve güncelleme sayıları yeterlidir. Her adımda bütün konumları kaydetmek dosya boyutunu artırır. Uygulama şu verileri tutar.

- Ajanın önceki adımına ait durum geçişi tamamlandığında bellekteki Q tablosu güncellenir.
- Arayüzde son adımda yapılan güncellemeler gösterilir.
- Tamamlanan bütün bölümlerin sonuçları geçmişe eklenir.
- Her adıma ait eski Q değerleri ve tahta görüntüleri ayrı ayrı arşivlenmez.

### Dosyanın yarım yazılması nasıl önlenir?

Uygulama önce `learning_memory_v5.json.tmp` dosyasına yazar, ardından geçici dosyayı asıl dosyanın yerine koyar.

```python
temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
temporary.replace(path)
```

`indent=2` satır ve girintilerle dosyanın okunmasını kolaylaştırır. `ensure_ascii=False` Unicode karakterlerini, örneğin Türkçe harfleri, doğrudan okunabilir biçimde saklar. Önce geçici dosyaya yazmak, asıl dosyanın yarım kalma riskini azaltır.

Veriler bölüm sonunda, simülasyon duraklatıldığında, yeni bölüm düğmesine basıldığında ve Ctrl+C ile çıkıldığında kaydedilir. Uygulama zorla kapatılırsa son kayıttan sonraki güncellemeler kaybolabilir.

`LearningMemory.load()` dosya varsa verileri okur, dosya yoksa boş bir bellekle başlar. Yükleme sırasında sıralı çalıştırmalara ait olmayan geçmiş kayıtları ayıklanır ve temizlenen veri kaydedilir. Dosya bozuksa veya sürümü desteklenmiyorsa yükleme hata verir.

Turun uzaklık ölçütünü ve kalan adım sayısını içeren durum anahtarları `learning_memory_v5.json` dosyasında saklanır. Bu dosya yoksa eğitim boş bir Q tablosu ve bölüm geçmişiyle başlar. Ölçütün bölüm başında bir kez seçildiği önceki sürüm `learning_memory_v4.json`, sabit yönlü hareketin kullanıldığı daha eski sürüm ise `learning_memory_v3.json` dosyasına kaydeder. Uygulama yeniden açıldığında veya kullanıcı yeni bölüm başlattığında, simülasyon kayıtlı Q değerleriyle yeni bir tahta oluşturur ve güncellenmeyi bekleyen adımları temizler.

### Rastgelelik tohumu nasıl yorumlanır?

Rastgelelik tohumu (`seed`), rastgele sayı üretecinin başlangıç değeridir. Otomatik bölümler tek bir `Simulation` örneğinde art arda çalıştığında üreteç kaldığı yerden devam eder. Geçmişte aynı tohumla etiketlenen otomatik bölümler farklı tahtalar kullanabilir.

Kontrollü bir karşılaştırmada aynı başlangıç tahtasını, hızları ve ilk turun ölçütünü yeniden oluşturmak için her bölümde aynı tohumla yeni bir `Simulation` örneği oluşturulur. Sonraki seçimleri yeniden üretmek için rastgele sayı üretecini kullanan işlemlerin sırası da eşleşmelidir. Öğrenme belleği ayrı tutulabilir ve bölümler arasında paylaşılabilir. Varsayılan rastgele başlangıçta tohum alanı `null` değerini alır ve arayüzde **Rastgele** görünür.

## 20. Python ile HTML nasıl haberleşir?

Tarayıcı, Python işlevlerini HTTP istekleri üzerinden kullanır. `app.py`, bu bilgisayarı gösteren `127.0.0.1` adresinde küçük bir **HTTP sunucusu** başlatır. Tarayıcı bir adrese istek gönderir ve sunucunun yanıtını alır.

**API**, HTML sayfasının hangi adreslere hangi veri biçimiyle istek göndereceğini belirler.

| Adres | Yöntem | İşlev |
|---|---|---|
| `/` | GET | HTML sayfasını döndürür |
| `/api/state` | GET | Güncel tahtayı ve istatistikleri döndürür |
| `/api/tick` | POST | Simülasyon çalışıyorsa sırayla 1–20 tek hücrelik adım yürütür |
| `/api/control` | POST | Simülasyonu başlatır, duraklatır veya ayarları uygulayarak yeni bir bölüm oluşturur |
| `/api/memory` | GET | Güncel Q belleğini, güncelleme sayılarını ve geçmişi JSON olarak döndürür |

Bu projede GET veri almak, POST işlem başlatmak için kullanılır. Örneğin HTML sayfası yeni bölüm için şu veriyi gönderir.

```json
{"action": "new_episode", "food_pairs": 40}
```

`app.py` içindeki `Handler.control()` isteği doğrular, güncel öğrenme verilerini kaydeder, yiyecek sayısını değiştirir ve `new_episode()` işlevini çağırır. Yanıt yeni tahtayı içerir.

`integer()` işlevi değerin tam sayı olup olmadığını ve sınırlar içinde kalıp kalmadığını denetler. `12.5`, `true`, `"12"`, `0` ve `376` yiyecek sayısı olarak kabul edilmez. HTML'deki sayı alanı girişleri doğrular. API'ye tarayıcı arayüzü dışından da istek gönderilebildiği için sunucu aynı sınırları denetler.

Uygulama `main()` işlevinden başlar. Bu işlev komut satırı ayarlarını okur, JSON belleğini yükler, simülasyonu ve sunucuyu oluşturur, ardından tarayıcıyı açar. Ctrl+C ile çıkıldığında belleği kaydeder ve sunucuyu kapatır.

## 21. HTML dosyasının bölümleri

`index.html` dosyası üç bölümden oluşur.

- **HTML** düğmelerin, giriş alanlarının, tabloların ve çizim alanının yapısını tanımlar.
- **CSS** renkleri, boyutları, sütunları ve dar ekranlardaki yerleşimi belirler.
- **JavaScript** sunucuyla haberleşir, tahtayı çizer ve ekrandaki değerleri günceller.

### `request()`

`fetch()` ile HTTP isteği gönderir ve yanıtı JSON olarak okur. Sunucu hata bildirirse kullanıcıya gösterilecek hata iletisini hazırlar.

### `update()`

İstekleri bir **Promise** zincirine ekler. Promise, daha sonra sonuçlanacak bir işlemi temsil eder. Zincir, bir isteğin yanıtı işlendikten sonra sıradaki isteği başlatır.

Yenileme ve kontrol istekleri aynı sırayı paylaşır. Bu sıra, yeni bir bölüm oluşturulduktan sonra eski bir adım yanıtının önceki tahtayı yeniden çizmesini önler.

### `control()`

Kontrol isteği sürerken düğmeleri geçici olarak devre dışı bırakır. İstek tamamlanınca düğmeleri yeniden etkinleştirir. Yeni bölüm isteğinde, giriş alanındaki yiyecek sayısı gönderilir.

### `render()`

Sunucudan gelen puanları ve tahta durumunu ekrandaki metne ve tabloya dönüştürür. Tamamlanan tur sayısını, **Turun uzaklık ölçütü** bilgisini, sıradaki ajanı, adım numarasını ve son adımda yapılan güncellemelerin eski ve yeni Q değerlerini gösterir.

Yeni bir bölüm sonucu kaydedildiğinde eğitim geçmişi tablosu yeniden oluşturulur. Her satırda bölüm ayarları ve üç ajanın ayrı ayrı ödül ve hız bilgileri yer alır. Bölüm numarasının yanındaki **Bitiş turu** sütunu, son kısmi turu da sayan `steps` alanını gösterir. **Son turun ölçütü**, bölümün son ölçütünü verir. Toplam puan, tüm ajanların ödüllerinin toplamıdır.

Güncel yiyecek sayısıyla eşleşen, `turn_order` değeri `sequential` olan en az 20 tamamlanmış bölüm varsa ilk ve son 10 bölümün ortalama toplam ödülü gösterilir. Bu özet eğitim geçmişini izlemeye yarar. Kontrollü karşılaştırma için başlangıç koşullarının ayrıca eşleştirilmesi gerekir.

### `draw()` ve Canvas

**Canvas**, JavaScript ile çizim yapılabilen bir HTML alanıdır. Çizim çözünürlüğü 600 × 600 pikseldir. Tahta 50 × 50 olduğundan her hücre `600 / 50 = 12` piksel genişliğindedir.

Hücrenin merkez koordinatları şöyle hesaplanır.

```javascript
const x = (agent.x + 0.5) * cell;
const y = (agent.y + 0.5) * cell;
```

`0.5` değeri, hesabı hücrenin sol üst köşesinden merkezine kaydırır. Yeşil yiyecekler daireyle, kırmızı yiyecekler kareyle, ajanlar numaralı ve renkli dairelerle çizilir. Kesikli çizgi, Python'dan gelen en yakın rakip konumunu gösterir.

### Eğitim hızı ve ajan hızı

Tarayıcı yaklaşık 100 milisaniyede bir tahtayı yenilemeye çalışır. Kaydırma çubuğu, her istekte kaç tek hücrelik adım yürütüleceğini belirler. Değer 1 iken her adım, daha yüksek değerlerde 20 adıma kadar grubun sonundaki tahta gösterilir. Simülasyon her adımın ardından yeşil yiyecek kalıp kalmadığını kontrol eder. Tarayıcı yeni bir istek göndermeden önce mevcut isteğin tamamlanmasını bekler.

Ajanın hızı, sıra kendisine geldiğinde art arda kaç adım hakkı olduğunu belirler. Eğitimin ilerleme hızı hesaplama süresine ve tarayıcının zamanlayıcısına bağlıdır. Tarayıcı sekmesi kapatıldığında simülasyonu ilerleten istekler durur.

## 22. Öğrenme başarısı nasıl ölçülür?

Değerlendirme, ajanların davranışını ölçülebilir sonuçlar üzerinden inceler. Q tablosunun büyümesi veya güncellemelerin artması, ölçülen performansla birlikte yorumlanır.

Ölçümler bölümler arasında hangi davranışların değiştiğini ve bu değişikliklerin ödülleri nasıl etkilediğini gösterir. Ajanlar ortak yiyecekler için yarıştığından toplam puanla birlikte her ajanın puanını incelemek gerekir.

Arayüz, tamamlanan bölümlerin sonuçlarını geçmiş tablosunda gösterir. Karşılaştırmada şu ölçümler kullanılır.

| Ölçüm | Yorum |
|---|---|
| Toplanan yeşil yiyecek | Ajanların hedef yiyeceklere ne ölçüde ulaştığını gösterir |
| Toplanan kırmızı yiyecek | Ajanların kaçınması gereken yiyeceklerle temasını gösterir |
| Toplam ödül | Yeşil ve kırmızı yiyeceklerden gelen ödüllerin toplamıdır |
| Tur sayısı | Sonuca kaç turda ulaşıldığını gösterir |
| Ajan başına ödül | Rekabetin her bir ajanı nasıl etkilediğini gösterir |
| Tüm yeşillerin toplanması | Bölümün hedefine ulaşıp ulaşmadığını gösterir |

Sıralı hareketle ve aynı yiyecek sayısıyla tamamlanan en az 20 bölüm varsa ilk ve son 10 bölümün ortalama toplam ödülü karşılaştırılır. Karşılaştırmada bölümler yiyecek sayısına göre gruplanır. Geçmiş yalnızca sıralı çalıştırmaların sonuçlarını içerir.

Rastgele yerleşim, ajan hızları, tur başına seçilen uzaklık ölçütü ve zamanla azalan keşif oranı da sonuçları etkiler. Geçmiş tablosu bu koşullardaki ilerlemeyi gösterir.

### Önceki bölüm başına sabit ölçüt denemesi

Bu denemede ajanlar ayrı tek hücrelik adımlar kullandı ve en yakın rakibi belirleyen ölçüt her bölüm boyunca sabit kaldı. Hedef seçimi ve ilerleme hesabı Manhattan uzaklığıyla yapıldı. Her renkten 125 yiyecekle, boş Q tablosundan ve `seed=42` ayarından başlayarak 10 bölüm art arda çalıştırıldı. On bölümün tamamında bütün yeşiller toplandı. Bölüm başına ortalama 23,7 kırmızı yiyecek toplandı, net ödül 101,3 ve tur sayısı 189,6 oldu. Bu sonuçlar tek bir rastgele sayı dizisindeki çalıştırmayı özetler.

### Önceki sabit yönlü hareket deneylerinin sonuçları

Önceki sabit yönlü hareket kuralıyla, her renkten 40 yiyecek ve 42 başlangıç tohumu kullanılarak yapılan bir çalıştırmada ortalama net ödül, ilk 10 bölümde 29,8 iken 51–60. bölümlerde 36,6'ya yükseldi. Toplanan ortalama kırmızı yiyecek sayısı 10,2'den 3,4'e düştü. Her iki gruptaki bütün bölümlerde 40 yeşil yiyeceğin tamamı toplandı.

Ayrı bir kontrollü deneyde de sabit yönlü hareket kullanıldı. Bu deneyde daha eski bir hedef seçme kuralı ve daha güçlü başlangıç Q değerleri uygulandı. Eğitim, her renkten 40 yiyecek bulunan tahtalarda yapıldı. Eğitim bölümlerinde 0–59, test tahtalarında 100–111 tohumları kullanıldı. Her politika aynı başlangıç tahtalarında, Q değerleri sabit tutularak ve %5 keşif oranıyla değerlendirildi. Eğitim almamış politikanın başlangıç Q değerlerinde önceki yeşil bonusu ve kırmızı cezası vardı.

| Önceki eğitim bölümü sayısı | Ortalama yeşil | Ortalama kırmızı | Ortalama net ödül | Ortalama tur | Tüm yeşillerin toplandığı tahta |
|---:|---:|---:|---:|---:|---:|
| 0 | 36,25 | 1,92 | 34,33 | 1.171,58 | 9/12 |
| 20 | 39,67 | 2,75 | 36,92 | 650,00 | 11/12 |
| 60 | 40,00 | 1,67 | 38,33 | 678,00 | 12/12 |

Bu deneyde 60 bölümlük eğitim ortalama net ödülü 4 puan artırdı ve 12 tahtanın tamamında tüm yeşiller toplandı. 20 bölüm eğitim alan politika ortalama daha az tur kullandı ve daha fazla kırmızı topladı. Bu bulgular, önceki hareket ve öğrenme düzeni, bu yiyecek yoğunluğu ve kullanılan 12 tahta için geçerlidir.

## 23. Sınırlamalar ve tasarım kararları

- Ajanlar tablo tabanlı Q-öğrenmesi kullanır. Bu sürümde rota planlama yöntemleriyle karşılaştırma veya sinir ağı deneyi yapılmadı.
- α ve γ sabittir. ε, tamamlanan bölüm sayısı arttıkça düşer. Kullanıcı arayüzü temel simülasyon ayarlarını sunar.
- Yiyecekler rastgele dağıtılır. Ajanlar bir yerleşim örüntüsü varsaymadan karar verir.
- Durum anahtarı tahtayı özetler. Bu özet bellek kullanımını azaltırken bazı bilgileri dışarıda bırakır.
- Tur için seçilen ölçüt uzaklık hesaplarını belirler. Hareketler dört ana yönle sınırlıdır.
- 4.000 turluk sınır, bir bölümün süresiz devam etmesini önlemek için uygulamada belirlenmiştir.
- Ajan bir adımda en fazla bir hücre ilerleyebilir. Tahta dışına çıkmaya çalışırsa yerinde kalır ve bir adım hakkı kullanır. Kırmızı yiyecek temas edildiğinde toplanır ve −1 ödül verir.
- Birden fazla ajan aynı hücrede bulunabilir. Ödev metni, yiyecek için yarışan ajanlar arasındaki önceliğe ilişkin bir kural verir.
- Birden fazla ajan aynı yiyeceğe ulaşabiliyorsa sabit 1 → 2 → 3 sırası, önce hareket eden ajana avantaj sağlayabilir.
- Öğrenme belleği dosyaya kaydedilir. Uygulama her yeniden başlatmada yeni bir tahta oluşturur.

## 24. Bileşenlerin akışı ve sunum özeti

`simulation.py` içindeki `ACTIONS`, `DELTAS`, `Agent` ve `Observation` ortamın temelini oluşturur. `new_episode()` tahtayı oluşturur. `observation_for()` gözlemi hazırlar, `project()` olası bir hareketi hesaplar ve `move()` seçilen eylemi uygular. `state_values()`, `choose_action()` ve `LearningMemory.learn()` öğrenme akışını oluşturur. `step()` bu parçaları sıralı hareket akışında birleştirir.

`app.py` içinde `main()` ve `make_handler()` sunucuyu hazırlar. `state()`, `do_POST()` ve `control()` arayüzü simülasyona bağlar. `index.html` içindeki `request()`, `update()`, `control()`, `render()` ve `draw()` ise iletişimi, kullanıcı kontrollerini ve çizimi yürütür.

Arayüzdeki bir düğmeden başlayıp Q güncellemesine uzanan akış şu şekildedir.

```text
HTML düğmesi veya zamanlayıcı
    → HTTP isteği
    → app.py isteği doğrular
    → Simulation.step()
    → sıradaki ajan tahtayı gözlemler → önceki adımın Q değeri güncellenir
    → bir eylem seçilir → ajanın ödülü hesaplanır → adım sonraki Q güncellemesi için tutulur
    → yeşil kaldı mı ve tur sınırına ulaşıldı mı diye kontrol edilir
    → adım hakkı varsa aynı ajanla, tükendiyse sıradaki ajanla devam edilir
    → bölüm bittiyse bekleyen adımlar güncellenir ve geçmiş JSON dosyasına kaydedilir
    → HTTP yanıtı
    → arayüzdeki metin güncellenir ve tahta yeniden çizilir
```

Demoda hızı 2 veya 3 olan bir ajanın art arda kullandığı adımları izleyebilirsin. Q panelinde önceki adımın ödülü ve yeni gözlemden hesaplanan gelecek Q değeri gösterilir. Ajan turdaki son adımını kullandıysa sonraki gözlemini diğer ajanlar hareket ettikten sonra alır. Son yeşil toplandığında bekleyen adımlar, gelecek Q değeri sıfır alınarak güncellenir.
