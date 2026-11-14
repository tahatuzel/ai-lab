# BIL353 projesi: sıfırdan kodu anlayarak ilerleme

Bu rapor, projeyi daha önce yapay zekâ veya web programlama görmemiş birinin okuyabileceği sırayla açıklar. Her bölümde üç soruya cevap arıyoruz: **Kavram nedir? Projede neden gerekiyor? Kodda nasıl yaptık?** Çalıştırma komutları için `README.md` dosyasını kullanın.

## 1. Önce yaptığımız işi anlayalım

Bir oyun tahtası düşünün. Tahtada üç oyuncu, toplanabilecek yeşil yiyecekler ve kaçınılacak kırmızı yiyecekler var. Oyuncuların her birine **ajan** diyoruz. Ajan, çevresinden bilgi alıp bir hareket seçen yazılım parçasıdır.

Bizim görevimiz oyuncuları elle yönetmek değil. Her ajanın hareket seçmesini, sonucunda ödül almasını ve bu deneyimle sonraki hareketlerini değiştirmesini sağlıyoruz. Buna **pekiştirmeli öğrenme** denir: önceden doğru hareket listesini vermek yerine, davranışın sonucunu ödülle bildiririz.

Projede tek öğrenme yöntemi, tablo tabanlı **Q-learning** kullanılır. Bir sinir ağı veya dil modeli eğitmiyoruz. Temel ortam Python ile çalışır; HTML sayfası ortamı gösterir ve kontrol eder.

### Ödev şartları nerede karşılanıyor?

| İstenen | Bizim uygulamamız | Kodun yeri |
|---|---|---|
| 50 × 50 tahta | Koordinatlar 0–49; toplam 2.500 hücre | `simulation.py`: `BOARD_SIZE` |
| Yeşil ve kırmızı eşit, rastgele ve toplam en çok %30 | Her renkten en çok 375; tekrar etmeyen rastgele hücreler | `MAX_FOOD_PAIRS`, `Simulation.new_episode()` |
| Üç ajan | Farklı başlangıç hücrelerinde üç `Agent` | `Simulation.new_episode()` |
| Yalnızca en yakın rakibin konumu | Gözlemde tek rakip koordinatı | `Simulation.observation_for()` |
| Manhattan veya Öklid rastgele | Bölüm başında bir ölçü seçilir | `new_episode()`, `observation_for()` |
| Yiyecekler gözlemlenebilir | Bütün yeşil ve kırmızı koordinatlar gözleme verilir | `Observation` |
| Hız rastgele 1–3 hücre | Her ajana bölüm başında hız atanır | `new_episode()` |
| Yukarı, aşağı, sol, sağ, eylemsiz | Beş ayrık seçenek | `ACTIONS`, `DELTAS`, `move()` |
| Yeşil +1, kırmızı −1; bağımsız ödül | Yalnızca yiyeceği alan ajanın sayacı ve Q değeri güncellenir | `Agent.reward`, `move()`, `LearningMemory.learn()` |
| Yeşil için rekabette sol kazanır | Aynı hücreye aynı mikro-adımda gelenler arasında `Left` önceliklidir | `move()` |

Ödev öğrenmenin hangi algoritmayla yapılacağını zorunlu kılmıyor. Az kodla gerçek ödül güncellemesi yapabildiğimiz için Q-learning seçtik. Ödevdeki ek 20 puanlık yaratıcı davranış bölümü için ayrıca bir örüntü bulucu veya yeni algoritma eklemedik. Bu sürüm temel kuralları karşılamaya odaklanır; puan garantisi vermez.

## 2. Dosyaları ve görevlerini ayıralım

| Dosya | Görevi |
|---|---|
| `simulation.py` | Ajanlar, tahta, gözlem, hareket, ödül, öğrenme ve JSON belleği |
| `app.py` | Yerel web sunucusu; HTML ile simülasyon arasındaki iletişim |
| `index.html` | Tahtayı çizme, düğmeler, ayarlar, öğrenme ve bölüm sonuçları |
| `hw.txt` | Verilen özgün ödev metni |
| `README.md` | Kurulum ve çalıştırma kılavuzu |
| `report.md` | Şu anda okuduğunuz açıklama |
| `learning_memory.json` | Çalıştırınca oluşan öğrenme verisi |

Python, oyunun gerçek durumunu tutar. HTML üzerindeki bir daireyi çizmek o ajanı hareket ettirmez; önce Python konumu değiştirir, sonra HTML yeni koordinatı ekranda gösterir. Böylece oyun kuralları tek yerde bulunur.

## 3. Kodu okumak için gerekli küçük sözlük

- **Değişken:** Bir değere verdiğimiz isim. `BOARD_SIZE = 50`, tahta boyutunu bir isim altında tutar.
- **Fonksiyon:** Bir işi yapan kod grubu. `manhattan(a, b)`, iki konumu alıp bir uzaklık döndürür.
- **Döngü:** Aynı işi tekrarlar. Üç ajan için hareket seçmek üzere ajanları dolaşırız.
- **Sınıf / nesne:** Bir kavramın verilerini ve davranışlarını bir araya getirir. `Agent` sınıfından üç ayrı ajan nesnesi oluştururuz.
- **Liste:** Sıralı koleksiyon. Bir durumun beş Q değeri eylem sırasıyla listede tutulur.
- **Tuple:** Burada `(x, y)` gibi sabit koordinat çifti için kullanılır.
- **Set / küme:** Tekrarsız öğeler içerir. Bir hücrede yiyecek var mı diye hızlıca bakmak için yiyecekleri kümelerde tutarız.
- **Dictionary / sözlük:** Anahtardan değere ulaşır. Bir durum anahtarından onun Q listesine erişiriz.
- **`dataclass`:** Ajanın konum ve hız gibi alanlarını az kodla tanımlamayı sağlar.
- **Tip açıklaması:** `Position = tuple[int, int]` gibi ifadeler beklenen veri biçimini anlatır; tek başına kullanıcı girdisini doğrulamaz.

`simulation.py` içindeki `json`, `math`, `random`, `dataclasses`, `datetime` ve `pathlib`; `app.py` içindeki HTTP sunucusu da Python standart kütüphanesinden gelir. Ek paket kurmuyoruz.

## 4. Tahta, hücre ve koordinat nedir?

Tahta 50 sütun ve 50 satırdır. Bir hücreyi `(x, y)` ile gösteriyoruz:

- `x`, soldan sağa arttıkça büyür.
- `y`, yukarıdan aşağıya arttıkça büyür.
- Sol üst `(0, 0)`, sağ alt `(49, 49)` olur.

Örneğin `(10, 8)` konumundaki ajan sağa giderse `(11, 8)`, yukarı giderse `(10, 7)` olur. Ekran koordinatlarında yukarı gitmek `y` değerini azaltır.

Kodda:

```python
BOARD_SIZE = 50
Position = tuple[int, int]
```

Tahta için 2.500 elemanlı büyük bir nesne matrisi oluşturmuyoruz. Ajan konumlarını ve yiyeceklerin koordinat kümelerini bilmek yeterli. Bir koordinat bu kümelerde yoksa o hücrede yiyecek yoktur.

## 5. Rastgele başlangıcı nasıl kurduk?

### Önce %30 sınırı

```text
50 × 50 = 2.500 hücre
2.500 × 0,30 = 750 yiyecek hücresi
750 / 2 = her renkten en çok 375
```

Bu yüzden `MAX_FOOD_PAIRS`:

```python
MAX_FOOD_PAIRS = BOARD_SIZE * BOARD_SIZE * 30 // 100 // 2
```

Kullanıcı 125 girerse 125 yeşil ve 125 kırmızı yerleştiririz; toplam 250 yiyecek olur. `food_pairs`, iki rengin her birinden kaç tane bulunduğunu belirtir.

### Tekrarsız hücre seçimi

`Simulation.new_episode()` şu işi yapar:

```python
cells = self.rng.sample(range(BOARD_SIZE ** 2), self.food_pairs * 2 + 3)
positions = [(cell % BOARD_SIZE, cell // BOARD_SIZE) for cell in cells]
```

`range(2500)`, hücreleri 0–2499 arasında numaralandırır. `sample`, aynı numarayı iki kez seçmez. Numara, bölüm ve kalan işlemleriyle koordinata çevrilir. Örneğin 102 numaralı hücre:

```text
x = 102 % 50 = 2
y = 102 // 50 = 2
konum = (2, 2)
```

İlk `food_pairs` hücre yeşil, sonraki aynı sayıda hücre kırmızı, son üç hücre ajan başlangıcı olur. Böylece başlangıçta yiyecekler ve ajanlar birbirleriyle çakışmaz.

Her ajanın hızı `randint(1, 3)` ile belirlenir. Hız bölüm boyunca sabittir; yeni bölümde tekrar seçilir. Ödev hızın hangi sıklıkta seçileceğini belirtmediği için bölüm başını kullandık.

`random.Random(seed)` rastgele üreticidir. Aynı seed ve aynı işlem sırası, aynı seçimleri yeniden üretmeye yarar. Bu, test ve hata araştırmasında kullanışlıdır.

## 6. Manhattan uzaklığı nedir?

Manhattan bir uzaklık ölçüsüdür. Sokakların kareli olduğu bir şehirde yatay ve dikey olarak kat edeceğimiz hücre sayısını düşünürüz:

```text
d = |x₁ − x₂| + |y₁ − y₂|
```

Dikey çizgiler mutlak değer demektir: sonucun işaretini kaldırırız. `(2, 3)` ile `(5, 7)` arasında:

```text
|2 − 5| + |3 − 7| = 3 + 4 = 7
```

`simulation.py` içindeki uygulaması:

```python
def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])
```

Projede iki amaçla kullanıyoruz:

1. Bölümün rakip ölçüsü Manhattan seçildiyse en yakın diğer ajanı belirlemek.
2. Ajanın hedef yiyeceğini seçmek ve hedef için rekabet durumunu özetlemek.

Bu fonksiyon bir rota çizmez. İki nokta arasındaki yatay/dikey uzaklığı hesaplar. Hızın 2 veya 3 olması, yiyecekte durma ve diğer ajanların yiyecek toplaması nedeniyle bu sayı gerçek tamamlanma süresinin kesin hesabı değildir.

## 7. Öklid uzaklığı nedir, çapraz hareket yokken neden var?

Öklid uzaklığı iki nokta arasındaki düz çizgi uzunluğudur:

```text
d = √((x₁ − x₂)² + (y₁ − y₂)²)
```

Aynı örnekte sonuç `√(3² + 4²) = 5` olur. Python'da ayrıca formül yazmak yerine standart `math.dist` fonksiyonunu kullanıyoruz.

**Uzaklık ölçmek ile hareket etmek farklı işlerdir.** Öklid seçildiğinde ajan çapraz hareket etmez. Yalnızca hangi rakibin en yakın sayılacağı değişir. Son esas aldığımız ödev metni iki ölçü arasından rastgele seçim istediği için ikisini de koruduk.

Örneğin ana ajan `(0, 0)`, diğerleri `(3, 3)` ve `(0, 5)` olsun:

| Rakip | Manhattan | Öklid |
|---|---:|---:|
| `(3, 3)` | 6 | yaklaşık 4,24 |
| `(0, 5)` | 5 | 5 |

Manhattan ikinci rakibi, Öklid birinci rakibi daha yakın bulur.

Kodun iki parçası:

```python
# new_episode()
self.metric = self.rng.choice(("Manhattan", "Euclidean"))

# observation_for()
distance = manhattan if self.metric == "Manhattan" else math.dist
```

Seçim bölüm başında bir kez yapılır. Aynı uzaklıkta iki rakip varsa düşük ajan numarasıyla eşitlik bozulur. Ödev bu eşitliği açıklamadığı için tutarlı bir sonuç seçtik.

## 8. Ajan neyi biliyor, neyi bilmiyor?

**Gözlem**, ajanın bir karar verirken kullanmasına izin verilen bilgidir. `Observation` içinde şunlar vardır:

```python
position       # Kendi konumu
speed          # Kendi hızı
green_foods    # Bütün yeşil yiyeceklerin konumları
red_foods      # Bütün kırmızı yiyeceklerin konumları
nearest_agent  # Tek bir rakibin konumu
```

Diğer rakibin konumu ve iki rakibin hızları bu nesnede bulunmaz. `frozenset`, yiyecek koordinatlarını değiştirilemeyen bir görünüm olarak taşır; karar hazırlığı sırasında ajan tahtadaki yiyecekleri değiştiremez.

Simülasyon motoru bütün ajanları bilmek zorundadır; aksi halde hareket ve çarpışmaları yönetemez. `observation_for()` bu geniş bilgiyi daraltır ve karar koduna yalnızca izin verilen gözlemi gönderir. Ekranda bütün ajanların görünmesi, ajan kararına hepsinin verildiği anlamına gelmez.

## 9. Beş eylemi kodda nasıl gösterdik?

```python
ACTIONS = ("Up", "Down", "Left", "Right", "No Action")
DELTAS = ((0, -1), (0, 1), (-1, 0), (1, 0), (0, 0))
```

Aynı sıradaki elemanlar birbirini karşılar:

| İndeks | Eylem | Konum değişimi |
|---:|---|---|
| 0 | Yukarı | `(0, -1)` |
| 1 | Aşağı | `(0, 1)` |
| 2 | Sol | `(-1, 0)` |
| 3 | Sağ | `(1, 0)` |
| 4 | Eylemsiz | `(0, 0)` |

Hiçbir değişimde hem x hem y aynı anda değişmez; çapraz hareket yapılamaz. “No Action” bir karar seçeneğidir, otomatik bekleme durumu değildir.

Ödev aynı maddede “4 branches” ifadesini ve beş eylemi birlikte veriyor. Uygulama, açıkça listelenen beş eylemi kullanır. Beş ayrı eşzamanlı hareket değil, her adımda bu listeden tek seçim yapılır.

## 10. Hızlı ajan yiyeceğin üzerinden atlıyor mu?

Hayır. Hızı 3 olan bir ajanı bir anda üç hücre ileri ışınlamıyoruz. `Simulation.move()` hareketi **mikro-adımlara**, yani tek hücrelik parçalara böler.

Örneğin ajan `(4, 5)` konumunda, hızı 3 ve sağa gidiyor olsun. `(6, 5)` hücresinde yiyecek varsa:

```text
1. mikro-adım: (5, 5)
2. mikro-adım: (6, 5) → yiyecek alınır ve hareket durur
3. mikro-adım: bu ajan hareket etmez
```

Tahta dışına çıkmak da hareketi durdurur. `(0, 5)` konumundan sola giden ajan `(−1, 5)` noktasına geçemez.

`project()` aynı sınır/yiyecek kurallarıyla tek bir aday hareketi önceden hesaplar. Gerçek tahtayı değiştirmez; ajanın bir yönde kırmızı yiyeceğe çarpıp çarpmayacağını anlamak için kullanılır. Gerçek eşzamanlı hareket ve ödül dağıtımı `move()` içindedir.

## 11. Aynı yiyeceğe giden ajanları nasıl çözdük?

Her mikro-adımda hareket eden ajanların varış hücreleri `claims` sözlüğünde toplanır. Bir hücreye giden iki ajan varsa o hücrenin aday listesi ikisini de içerir.

Yeşilde kazanan:

```python
winner = min(claimants,
             key=lambda index: (ACTIONS[actions[index]] != "Left", index))
```

Python'da `False`, sıralamada `True` değerinden önce gelir. Sol eylemi için `!= "Left"` sonucu `False` olur; dolayısıyla sol hareket öncelik alır. Birden fazla sol varsa veya hiç sol yoksa düşük indeks kazanır; indeksler ajan numarası sırasındadır.

Yalnızca kazanan +1 alır. Yiyecek bir kez silinir. Yiyeceğe aynı anda ulaşan bütün adaylar o tur için durdurulur; kaybeden de artık aynı hücreye gelmiştir.

Kırmızıda da yiyecek bir kez tüketilir ve yalnızca bir ajan −1 alır. Ödev kırmızıdaki eşitlik kuralını belirtmediğinden düşük ajan numarası kullanılır.

Bu kural **aynı mikro-adımda varış** için geçerlidir. Başka bir ajan daha erken mikro-adımda yiyeceği almışsa daha sonra gelen ajan onu geri alamaz. Ajanları birbirine duvar yapmadık; ödev böyle bir engel kuralı tanımlamıyor.

## 12. Ödül, durum ve Q değeri arasındaki fark

Öğrenmeyi anlayabilmek için bu üç kavramı ayıralım:

- **Ödül `r`:** Az önce ne oldu? Yeşil alındıysa +1, kırmızı alındıysa −1, yiyecek alınmadıysa 0.
- **Durum `s`:** Ajan hangi koşullar altında karar verdi? Örneğin hedef sağ üstte, hız 2 ve solda kırmızı riski var.
- **Q değeri `Q(s,a)`:** Bu durumda bu hareketi seçmek gelecekte ne kadar ödül getirebilir? Ajanın öğrendiği tahmindir.

Q değeri gerçek skor değildir. Ajanın 7 puanı olabilir ama belirli bir durumdaki sağ hareketinin Q değeri 0,35 olabilir. Biri geçmişte topladığı gerçek ödül, diğeri geleceğe ilişkin tahmindir.

`Agent.reward` gerçek skoru hesaplar:

```python
@property
def reward(self):
    return self.green - self.red
```

Örneğin 12 yeşil, 3 kırmızı alan ajanın skoru `12 − 3 = 9` olur. Takımın toplamı arayüzde özetlenir; öğrenme sırasında bu toplamı her ajana ödül olarak dağıtmıyoruz. Her biri kendi aldığı yiyecekten öğrenir.

## 13. Bütün tahtayı ezberletmeden durumu nasıl özetledik?

Tahtanın her olası düzeni için ayrı öğrenme tablosu açmak çok büyük bir bellek gerektirirdi. `Simulation.state_values()` daha küçük bir durum anahtarı üretir.

Önce Manhattan'a göre en yakın yeşil hedefi buluruz. Eşit uzaklıkta koordinat çiftiyle sıralama yapılır. Sonra anahtara şunları koyarız:

| Parça | Anlamı | Neden gerekli? |
|---|---|---|
| Ajan numarası | 1, 2 veya 3 | Öğrenme tablolarını ayırır |
| `sx,sy` | Hedefin yatay/dikey yönü: −1, 0, +1 | Hedefe hangi yönlerde yaklaşılacağını özetler |
| `v` | Ajanın hızı | Aynı hareket hızla birlikte farklı sonuç verir |
| `r` | Dört hareket yönündeki kırmızı risklerinin bit maskesi | Yakındaki tehlikeleri ayırt eder |
| `c` | Görünen rakip hedefe en az bizim kadar yakın mı? | Rekabeti öğrenilen duruma dahil eder |

Örnek anahtar:

```text
1|1,-1|v2|r4|c1
```

Bunu şöyle okuruz: “Ajan 1, hedef sağ üstte, hız 2, sol yönünde kırmızıya çarpma riski var ve görünen rakip hedefe en az bizim kadar yakın.”

### İşaret bilgisini nasıl çıkardık?

```python
sx = (dx > 0) - (dx < 0)
```

Python'da doğru `1`, yanlış `0` gibi davranır. `dx` pozitifse `1 − 0 = 1`; negatifse `0 − 1 = −1`; sıfırsa `0 − 0 = 0` olur. Aynısını y için yaparız.

### Bit maskesi ne demek?

Dört ayrı evet/hayır bilgisini tek sayıda tutuyoruz:

| Yön | Risk varsa eklenen sayı |
|---|---:|
| Yukarı | 1 |
| Aşağı | 2 |
| Sol | 4 |
| Sağ | 8 |

Sol ve sağ riskliyse `r = 4 + 8 = 12` olur. `1 << action`, ilgili sayıyı üretir. `red_mask & (1 << action)` o yöndeki risk bitinin açık olup olmadığını kontrol eder. Risk, `project()` ile ajanın kendi hızı ve görünür yiyecekler kullanılarak hesaplanır; yiyeceğin arkasına geçilmiş varsayılmaz.

`c` için rakibin ve bizim hedefe Manhattan uzaklıklarımız karşılaştırılır. Hızı bilinmeyen rakip için gerçek varış süresi tahmin etmiyoruz. Rakip, bölümde rastgele seçilen ölçüyle gözleme alınmıştır; hedef rekabetini özetlerken yine Manhattan kullanırız.

Bu sıkıştırmanın bedeli vardır: farklı tahtalar aynı anahtara dönüşebilir. Örneğin hedef bir hücre veya on hücre sağda olsa da yön aynı olabilir. Yöntem bu yüzden yaklaşık öğrenir; bütün tahtalar için en iyi kararı garanti etmez.

## 14. Q tablosu nasıl tutuluyor?

`LearningMemory.q_values`, anahtarı durum, değeri beş Q sayısı olan bir sözlüktür:

```json
{
  "1|1,-1|v2|r4|c1": [0.1, -0.1, -0.6, 0.1, -0.05]
}
```

Liste sırası her zaman `Up, Down, Left, Right, No Action` sırasıdır. Bu örnekte yukarı ve sağ başlangıçta en yüksek tahmine sahiptir; sol, kırmızı riski nedeniyle düşük başlar.

Aynı anahtara ait `visits` listesi, her eylemin kaç defa gerçekten öğrenme güncellemesi aldığını tutar:

```json
{
  "1|1,-1|v2|r4|c1": [3, 0, 1, 7, 0]
}
```

Bu, yukarı eyleminin 3, solun 1, sağın 7 kez güncellendiği anlamına gelir. Ziyaret sayısını bu sürümde öğrenme oranını değiştirmek için kullanmıyoruz; yapılan öğrenmeyi incelemek için saklıyoruz.

Anahtar başında ajan numarası bulunduğundan ajan 1'in ödülü ajan 2'nin satırını değiştirmez. Fiziksel olarak tek sözlük kullanılsa da tablolar mantıksal olarak bağımsızdır.

Bir sonraki durumun değerlerine bakarken de yeni satır oluşturulabilir. Dolayısıyla “öğrenilen durum” sayacı içindeki bazı satırlar henüz seçilmiş bir eylemle güncellenmemiş olabilir. Gerçek işlem sayısını `visits` toplamından buluruz; arayüz bunu “Q güncellemesi” olarak gösterir.

## 15. Ajan ilk anda hiçbir şey bilmiyorsa nasıl hareket ediyor?

Yeni bir durumun bütün Q değerlerini sıfır başlatmak mümkün. Fakat 50 × 50 tahtada seyrek yiyeceklerle tamamen amaçsız dolaşmak ilk denemeleri uzatır. Görünür yiyecek bilgisinden yararlanan küçük bir **başlangıç tercihi** veriyoruz:

```python
initial = [
    0.1 * (x * sx + y * sy) - 0.5 * bool(red_mask & (1 << action))
    for action, (x, y) in enumerate(DELTAS)
]
initial[-1] = -0.05
```

Hedefe doğru yön +0,1, hedeften uzaklaşan yön −0,1 alabilir. Kırmızıya çarpacak yönün başlangıç değeri ayrıca 0,5 azaltılır. Eylemsiz bekleme −0,05 ile başlar.

Örneğin hedef sağdaysa sağ hareketin başlangıç tercihi +0,1 olur. Sağda kırmızı riski varsa bu `0,1 − 0,5 = −0,4` olur.

Bu değerler **öğrenilmiş deneyim değildir**; bizim verdiğimiz küçük ön bilgidir. `LearningMemory.values()` yalnızca daha önce görülmeyen bir anahtarda bu listeyi ekler. Aynı anahtar yeniden geldiğinde başlangıç değerlerini tekrar yazmaz; mevcut öğrenilmiş değerleri kullanır.

Gerçek çevre ödülü hâlâ yalnızca +1, −1 veya 0'dır. Hedefe yaklaşmak için ayrı bir gerçek ödül eklemiyoruz. Başlangıçta verilen yön tercihleri, Q güncellemeleriyle değişir. Bu yüzden gözlenen davranış hem başlangıç bilgisinin hem de sonraki deneyimin sonucudur.

## 16. Ajan hangi eylemi seçiyor: ε-greedy

Sadece şu an en iyi görünen hareketi yapmak, başka bir seçeneğin daha iyi olduğunu öğrenmeyi engelleyebilir. Buna karşı biraz **keşif** yaparız.

`Simulation.choose_action()`:

```python
if self.rng.random() < self.memory.epsilon:
    return self.rng.randrange(len(ACTIONS))
best = max(values)
return self.rng.choice([i for i, value in enumerate(values) if value == best])
```

- `ε` olasılığıyla beş eylemden biri rastgele seçilir.
- Geri kalan zamanda en yüksek Q değerine sahip eylem seçilir.
- En iyi değerde eşitlik varsa adaylar arasında rastgele seçim yapılır.

Başlangıçta `ε = 0,20` olduğu için yaklaşık her beş kararın birinde keşif yapılır. Bu, her beşinci kararın mutlaka rastgele olduğu anlamına gelmez; her kararda ayrı olasılık hesabıdır.

Keşif oranı tamamlanan bölüm sayısıyla azalır:

```python
max(0.05, 0.20 * 0.97 ** episodes)
```

İlk bölümde 0,20; 10 bölümden sonra yaklaşık 0,147 olur. En az 0,05 olarak tutulur. Böylece ajan öğrendiklerini daha sık kullanırken yeni davranışları tamamen bırakmaz.

Üç ajanın Q değerleri ayrıdır; bu sade sürümde α, γ ve ε programı ortaktır. Rastgele keşif kırmızı yiyeceğe götürebilir. Hata yapabilmek, olumsuz ödülden öğrenmenin bir parçasıdır.

## 17. Q-learning matematiğini adım adım anlayalım

Kullandığımız güncelleme:

```text
Q_yeni(s,a) = Q_eski(s,a) + α × [r + γ × max Q(s′,a′) − Q_eski(s,a)]
```

Sembollerin anlamı:

| Sembol | Anlamı | Bu projede |
|---|---|---|
| `s` | Hareketten önceki durum | Durum anahtarı |
| `a` | Yapılan hareket | Beş eylemden biri |
| `r` | Bu harekette alınan ödül | +1, −1 veya 0 |
| `s′` | Hareketten sonraki durum | Yeni gözlemden hesaplanır |
| `max Q(s′,a′)` | Yeni durumda tahmini en iyi gelecek | Beş Q değerinin en büyüğü |
| `α` | Yeni bilgiye ne kadar ağırlık verelim? | 0,20 |
| `γ` | Gelecekteki ödülü ne kadar önemseyelim? | 0,90 |

### α ne işe yarar?

Öğrenme oranıdır. 0,20, eski tahmini hesaplanan yeni hedefe doğru farkın %20'si kadar değiştirmek demektir. Tek bir deneyim bütün geçmişi silmez.

### γ ne işe yarar?

Gelecek ödülün ağırlığıdır. Ajan sadece hemen yanındaki ödüle değil, sonraki hareketlerde beklenen ödüle de değer verir. Örneğin yeni durumun en iyi Q değeri 0,4 ise bunun hedefe katkısı `0,9 × 0,4 = 0,36` olur.

### Sayısal örnek: yeşil topladık

Eski Q = 0,1; ödül = +1; yeni durumdaki en iyi Q = 0,4 olsun:

```text
Hedef = 1 + 0,9 × 0,4 = 1,36
Hata  = 1,36 − 0,1 = 1,26
Yeni Q = 0,1 + 0,2 × 1,26 = 0,352
```

Ajan benzer durumu tekrar gördüğünde bu hareket artık 0,1 yerine 0,352 ile değerlendirilir.

### Sayısal örnek: kırmızı topladık

Eski ve gelecek Q değerleri aynı, ödül −1 olsun:

```text
Hedef = −1 + 0,9 × 0,4 = −0,64
Yeni Q = 0,1 + 0,2 × (−0,64 − 0,1) = −0,048
```

Bu hareketin tercih edilirliği düşer. Birkaç benzer deneyimden sonra kırmızıya giden kararın değeri daha da değişebilir.

### Bölüm bittiğinde ne değişir?

Bitmiş bölümün devamından ödül gelmez. Bu yüzden `future = 0` kullanırız. Son yeşili alan ajanın eski Q değeri 0,1 ise:

```text
Hedef = 1
Yeni Q = 0,1 + 0,2 × (1 − 0,1) = 0,28
```

4.000 adım sınırına gelmek de bizim bölüm tanımımızda bitiştir; o adımda gelecek Q eklemeyiz.

### Kodda karşılığı

`LearningMemory.learn()`:

```python
old = values[action]
future = 0.0 if terminal else max(next_values)
target = reward + GAMMA * future
values[action] += ALPHA * (target - old)
self.visits[key][action] += 1
```

Arayüzdeki son Q hesabı bu fonksiyonun döndürdüğü gerçek değerlerden gelir. Örnek bir animasyon veya uydurulmuş öğrenme göstergesi değildir. Bu sürümde uygunluk izi, ek yol araması veya ikinci öğrenme yöntemi yoktur.

## 18. Bir simülasyon adımının tamamı

`Simulation.step()` programın ana akışıdır:

1. Her ajan için mevcut tahtadan gözlem ve durum değerleri hazırlanır.
2. Her ajan Q değerleri ve ε ile bir eylem seçer.
3. Bütün eylemler `move()` ile eşzamanlı mikro-adımlar halinde yürütülür.
4. Her ajanın kendi ödülü alınır.
5. Yeşillerin bitip bitmediği ve adım sınırı kontrol edilir.
6. Her ajanın hareket sonrası durumu hesaplanır ve kendi Q satırı güncellenir.
7. Bölüm bitmediyse sonraki adım beklenir.
8. Bölüm bittiyse sonuç geçmişe eklenir, sayaç artar ve yeni tahta oluşturulur.

İlk üç ajanın kararını aynı eski tahtaya göre hazırlamak önemlidir. Ajan 1'i hareket ettirip sonra ajan 2'ye karar verdirseydik ikinci ajan ilk ajanın henüz yaptığı hareketi görmüş olurdu; eşzamanlı karar düzeni bozulurdu.

### Tek hareketi baştan sona izleyelim

Ajan 1 `(4, 5)` konumunda, hızı 2, son yeşil `(6, 5)` hücresinde olsun. Diğer ajanlar bu yiyeceğe aynı anda ulaşmasın. Eylem seçiminin sağ olduğunu varsayalım; keşif varsa başka hareket de seçilebilir.

- Hedef sağdadır; yeni bir durumsa sağın başlangıç Q değeri +0,1 olabilir.
- Ajan önce `(5, 5)`, sonra `(6, 5)` hücresine gider.
- Yeşil silinir; yalnızca ajan 1 +1 alır.
- Tahtada yeşil kalmadığı için bölüm biter.
- Gelecek Q sıfır alınır; başlangıç 0,1 ise yeni Q 0,28 olur.
- Diğer ajanların o adımdaki ödülü 0'dır; kendi eylem satırları kendi sonuçlarıyla güncellenir.
- Bölüm sonucu belleğin geçmiş listesine eklenir ve yeni tahta hazırlanır.

Yeni bölüm açılırken Q tablosu sıfırlanmaz. **Tahta değişir, öğrenilmiş deneyim kalır.**

## 19. Öğrenme JSON'a nasıl kaydediliyor?

**JSON**, sözlük ve listeleri metin biçiminde saklamanın yaygın bir yoludur. Python nesneleri uygulama kapanınca kaybolur; dosyaya yazarsak sonraki çalıştırmada geri alabiliriz.

`LearningMemory.save()` şu verileri saklar:

| Alan | İçerik |
|---|---|
| `version` | Dosya biçiminin sürümü |
| `episodes` | Tamamlanan bölüm sayısı |
| `q_values` | Ajanlara ait durum-eylem değerleri |
| `visits` | Durum-eylem güncelleme sayıları |
| `history` | Tamamlanan bütün bölümlerin parametre ve sonuçları |

Bir geçmiş satırında tarih, bölüm numarası, her renkten yiyecek sayısı, başlangıç seed değeri, seçilen uzaklık ölçüsü, kullanılan α/γ/ε, adım sayısı, toplam yeşil/kırmızı/ödül ve üç ajanın ayrı hızları ile skorları vardır.

JSON içindeki Q listelerinde hangi indeksin hangi harekete ait olduğu `ACTIONS` sırasıyla belirlenir. `/api/memory` görünümü bu eylem isimlerini ve geçerli katsayıları da döndürür.

### Neden her adımın bütün tahtasını kaydetmedik?

Öğrenmeyi sürdürmek için güncel Q değerleri ve ziyaret sayıları yeterlidir. Her adımın tüm konumlarını kaydetmek çok daha fazla veri üretirdi. Bu yüzden:

- Q tablosu her simülasyon adımında bellekte güncellenir.
- Arayüz son adımın gerçek hesaplamasını gösterir.
- Bütün tamamlanmış bölümlerin sonuçları tarihçede saklanır.
- Her adımın önceki Q sürümü ve tahta görüntüsü ayrı ayrı arşivlenmez.

### Dosyanın yarım yazılmasını nasıl önlüyoruz?

Önce `learning_memory.json.tmp` yazılır, sonra asıl dosyayla değiştirilir:

```python
temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
temporary.replace(path)
```

`indent=2`, dosyayı satır ve girintilerle okunabilir yapar. `ensure_ascii=False`, Türkçe karakterlerin okunur kalmasını sağlar. Geçici dosya kullanımı, asıl dosyanın içeriğinin yazım sırasında yarım kalma riskini azaltır.

Kaydetme; bölüm sonunda, duraklatınca, yeni bölüm düğmesine basınca ve terminalde Ctrl+C ile çıkarken yapılır. İşlem zorla sonlandırılırsa son kayıttan sonraki güncellemeler kaybolabilir. Bu, her adımda diske yazmamanın sonucudur.

`LearningMemory.load()` dosya varsa okur; yoksa boş bellekle başlar. Dosya bozuksa veya sürümü desteklenmiyorsa hata verir; sessizce öğrenmeyi sıfırlamaz.

Önceki uygulamanın `agent_memory.json` ve `training_results.csv` dosyalarına dokunmadık. Eski biçim farklı olduğu için yeni sürüm `learning_memory.json` kullanır; eski verileri yeni deney yapılmış gibi göstermiyoruz. Yeni dosya yerel çalışma verisi olduğu için `.gitignore` içinde tutulur.

### Seed kaydını doğru yorumlayalım

Seed rastgele sayı üreticisinin **başlangıç** değeridir. Tek bir `Simulation` nesnesiyle arka arkaya otomatik bölümler çalıştırılırsa üretici kaldığı yerden devam eder. Bu nedenle geçmişte aynı başlangıç seed değerinin görünmesi, otomatik bölümlerin aynı tahta olduğu anlamına gelmez.

Aşağıdaki kontrollü 30 bölümlük denemede ise her bölüm için yeni bir `Simulation` oluşturuldu. Böylece aynı seed yeniden verildiğinde aynı başlangıç tahtası, hızlar ve ölçü tekrar üretildi. Uygulamadaki varsayılan rastgele başlangıçta seed alanı `null` olur; HTML bunu “Rastgele” gösterir.

## 20. Python ile HTML nasıl konuşuyor?

Tarayıcı Python fonksiyonunu doğrudan çağıramaz. `app.py`, yalnızca bu bilgisayardaki `127.0.0.1` adresinde küçük bir **HTTP sunucusu** açar. HTTP, tarayıcının bir adrese istek gönderip cevap alması için kullanılan iletişim biçimidir.

**API**, HTML'in kullanabildiği adresler ve veri kurallarıdır:

| Adres | Yöntem | İşlev |
|---|---|---|
| `/` | GET | HTML sayfasını getirir |
| `/api/state` | GET | Geçerli tahtayı ve istatistikleri verir |
| `/api/tick` | POST | Çalışıyorsa 1–20 simülasyon adımı yürütür |
| `/api/control` | POST | Başlat, duraklat veya ayarları uygulayıp yeni bölüm aç |
| `/api/memory` | GET | Güncel Q belleğini, ziyaretleri ve geçmişi JSON olarak verir |

GET veri istemek, POST burada bir işlem istemek için kullanılır. Örneğin HTML şu isteği gönderir:

```json
{"action": "new_episode", "food_pairs": 40}
```

`app.py` içindeki `Handler.control()` bunu doğrular, mevcut öğrenmeyi kaydeder, yiyecek sayısını değiştirir ve `new_episode()` çağırır. Cevapta yeni tahta döner.

`integer()` tam sayı ve sınır kontrolünü tek yerde yapar. `12.5`, `true`, `"12"`, 0 veya 376 yiyecek sayısı olarak kabul edilmez. HTML sayı kutusu hatalı girişleri önler; sunucu da aynı sınırları ayrıca denetler. Çünkü tarayıcı dışından da API isteği gönderilebilir.

`main()` uygulama girişidir: komut satırı ayarlarını okur, JSON belleğini yükler, simülasyonu ve sunucuyu oluşturur, tarayıcıyı açar. Ctrl+C alındığında belleği kaydedip sunucuyu kapatır.

## 21. HTML tarafında hangi kod ne yapıyor?

`index.html` üç bölümden oluşur:

- **HTML:** Düğmelerin, kutuların, tablonun ve çizim alanının yapısı.
- **CSS:** Renkler, boyutlar, kolonlar ve dar ekrana uyum.
- **JavaScript:** Sunucuyla iletişim, çizim ve ekrandaki değerleri güncelleme.

### `request()`

`fetch()` ile HTTP isteği gönderir; cevabı JSON olarak okur. Sunucu hata bildirdiyse kullanıcıya gösterilecek bir hata oluşturur.

### `update()`

İstekleri bir Promise zincirine ekler. **Promise**, ileride tamamlanacak bir işlemin sonucunu temsil eder. Burada zinciri, bir isteğin cevabı işlenmeden sonraki isteği başlatmamak için kullanıyoruz.

Bu sıra önemlidir: eski bir adım isteğinin cevabı, yeni bölüm isteğinden sonra gelip eski tahtayı yeniden çizmemelidir. Yenileme ve kontrol istekleri aynı sırayı paylaşır.

### `control()`

Bir kontrol isteği sürerken düğmeleri geçici olarak devre dışı bırakır. İstek bittiğinde yeniden açar. Yeni bölüm isteğinde kullanıcı kutudaki taslak yiyecek sayısını gönderir.

### `render()`

Sunucudan gelen durumu metinlere ve tabloya dönüştürür. Skorları tarayıcıda yeniden hesaplamak yerine Python'daki gerçek değerleri gösterir. Son öğrenme adımının eski/yeni Q değerleri de burada yazılır.

Eğitim geçmişi, yeni bir sonuç eklendiğinde yeniden oluşturulur. Her satırda parametreler ve üç ajanın kendi ödül/hız bilgisi bulunur. Toplam puan bütün ajanların ödüllerinin toplamıdır.

Aynı yiyecek sayısında en az 20 tamamlanmış bölüm varsa ilk 10 ve son 10 bölümün ortalama toplam ödülü gösterilir. Farklı sayıda yiyecekle alınan ham skorları doğrudan karşılaştırmamak için bu özette geçerli yiyecek sayısıyla eşleşen kayıtlar kullanılır. Bu küçük özet kontrollü bilimsel deney yerine geçmez.

### `draw()` ve Canvas

**Canvas**, JavaScript ile çizim yaptığımız HTML alanıdır. İç çözünürlük 600 × 600, tahta 50 × 50 olduğu için hücre boyutu `600 / 50 = 12` pikseldir.

Bir hücrenin merkezini:

```javascript
const x = (agent.x + 0.5) * cell;
const y = (agent.y + 0.5) * cell;
```

ile buluruz. `0.5` hücrenin sol üst köşesinden merkezine geçer. Yeşiller daire, kırmızılar kare ve ajanlar numaralı renkli daire olarak çizilir. Kesikli çizgiler, Python'dan gelen tek en yakın rakip koordinatını gösterir.

### Eğitim hızı ile ajan hızı farklıdır

Tarayıcı yaklaşık 100 milisaniyede bir yenileme denemesi yapar. Kaydırıcı, bir istekte kaç simülasyon adımı çalıştırılacağını belirler. Önceki istek sürüyorsa yenisini biriktirmez.

Ajan hızı ise tek bir simülasyon adımında kaç hücre ilerleyebildiğidir: 1, 2 veya 3. Kaydırıcı bunu değiştirmez. Gerçek eğitim hızı hesaplama süresine ve tarayıcının zamanlayıcısına bağlıdır; sabit bir saniyelik adım garantisi yoktur. Tarayıcı sekmesi kapalıyken yeni tick gelmez, dolayısıyla bu tasarımda simülasyon ilerlemez.

## 22. İlk bildirilen ayar hatası neydi, nasıl düzelttik?

Eski HTML, yiyecek kutusu odakta değilken her yenilemede sunucunun eski değerini kutuya geri yazıyordu. Örneğin kullanıcı 125'i 40 yapıp başka bir alana tıkladığında, sonraki yenileme tekrar 125 yazabiliyordu. Yeni bölüm isteği de yanlışlıkla 125 gönderiyordu.

Şimdi kutuyu yalnızca ilk durum yüklemesinde sunucudan dolduruyoruz:

```javascript
if (!latest) foodInput.value = data.food_pairs;
```

Sonraki yenilemeler kullanıcının henüz uygulamadığı taslağı bozmaz. “Uygula / Yeni bölüm” açıkça bu değeri gönderir. Canlı durumdaki “Uygulanan yiyecek sayısı” satırı gerçekten kullanılan sayıyı gösterir.

Ayrıca ilk durum isteğini, otomatik adımları ve kontrol isteklerini aynı kuyruğa aldık. Böylece ayar uygulama ile eski cevapların çizilmesi arasındaki sıralama sorunu giderildi.

## 23. Zaman içinde gerçekten ne değişti? Çalıştırılan 30 bölüm

Bu sürüm hazırlanırken gerçek simülasyon çalıştırıldı; aşağıdaki değerler tahmin veya örnek veri değildir. Yeni `learning_memory.json` bu 30 bölümün Q belleğini ve bütün sonuçlarını içerir.

Deney düzeni:

- Her bölümde 40 yeşil, 40 kırmızı yiyecek.
- α = 0,20 ve γ = 0,90 sabit.
- Başlangıç seed değerleri 42–51, aynı sırayla üç defa kullanıldı.
- Her bölüm için aynı öğrenme belleğini kullanan yeni `Simulation` oluşturuldu.
- Böylece her 10 bölümlük grupta aynı başlangıç tahtaları, hızlar ve uzaklık ölçüleri kullanıldı; Q belleği sıfırlanmadı.
- Keşif oranı tamamlanan bölüm sayısına göre normal biçimde azaldı.

| Grup | Ortalama yeşil | Ortalama kırmızı | Ortalama ödül | Ortalama adım | Bütün yeşilleri alan bölüm |
|---|---:|---:|---:|---:|---:|
| 1–10 | 40 | 3,3 | 36,7 | 376,9 | 10 / 10 |
| 11–20 | 40 | 2,9 | 37,1 | 447,4 | 10 / 10 |
| 21–30 | 40 | 2,7 | 37,3 | 386,1 | 10 / 10 |

Ajanların ayrı ortalama ödülleri:

| Ajan | İlk 10 bölüm | Son 10 bölüm |
|---|---:|---:|
| 1 | 11,6 | 12,2 |
| 2 | 12,5 | 13,6 |
| 3 | 12,6 | 11,5 |

### Bu sonucu nasıl okuyalım?

Toplam ortalama ödül 0,6 arttı ve kırmızı ortalaması 0,6 azaldı. Buna karşılık adım sayısı düzenli azalmadı; ajan 3'ün ortalama kişisel ödülü de düştü. Ortak yiyecekler için rekabet edildiğinden takım toplamındaki artış her ajana aynı şekilde yansımaz.

İlk 10 bölümde kullanılan ε yaklaşık 0,2000–0,1520; son 10 bölümde 0,1088–0,0827 aralığındaydı. Hem Q değerleri hem keşif davranışı değişti. Bu yüzden küçük farkın tamamını yalnızca Q tablosunun daha iyi olmasına bağlayamayız. Öğrenme kapalı bir kontrol grubu ve çok daha fazla tekrar olmadan kesin nedensel sonuç çıkaramayız.

Somut olarak söyleyebildiğimiz: **36.312 gerçek ajan güncellemesi yapıldı, bellekte 554 durum satırı oluştu ve bu denemede sonraki gruplar ortalamada daha az kırmızı topladı.** Bu, bütün yeni tahtalarda sürekli iyileşme veya en iyi politika garantisi değildir.

HTML'de bu geçmiş kayıtlarını görebilir, eğitimi sürdürerek yeni bölümlerin aynı listeye eklendiğini izleyebilirsiniz. Başka yiyecek sayısına geçerseniz her satır kendi parametresini korur.

## 24. Neleri bilinçli olarak basit bıraktık?

- Tek öğrenme yöntemi Q-learning'dir; rota algoritması kıyası ve sinir ağı yoktur.
- α ve γ sabittir. ε bölüm sayısıyla azalır. Kullanıcıya onlarca ayar eklenmez.
- Yiyecekler rastgele dağıtılır; gizli bir yerleşim örüntüsü varmış gibi davranılmaz.
- Durum tablosu bütün tahtayı içermez; belleği küçük tutmak için bilgi kaybı kabul edilir.
- Öklid yalnızca yakın rakip ölçüsüdür; hiçbir yerde çapraz hareket yoktur.
- 4.000 adım sınırı, takılan bölümün sonsuza kadar sürmesini engelleyen uygulama kararıdır; ödevde verilmiş bir sayı değildir.
- Ajan, yiyecek veya sınırda erken durur. Kırmızı yiyecek bir duvar değildir; alınabilir ve −1 ödül verir.
- Aynı hücrede ajan bulunması yasaklanmaz. Ödevde yalnızca yiyecek rekabetinin sonucu tanımlanmıştır.
- Bellek kalıcıdır; tahtanın tam kaldığı yer kaydedilmez. Uygulama tekrar açılınca yeni tahta kurulur.

## 25. Kodu hangi sırayla okuyayım?

Önce `simulation.py` içindeki `ACTIONS` ve `DELTAS`, sonra `Agent`, `Observation`, `new_episode()`, `observation_for()`, `project()` ve `move()` ile ortam kurallarını anlayın. Ardından `state_values()`, `choose_action()` ve `LearningMemory.learn()` ile öğrenmeyi okuyun. Son olarak `step()` içinde bunların nasıl birleştiğini izleyin.

Daha sonra `app.py` içindeki `main()`, `make_handler()`, `state()`, `do_POST()` ve `control()` ile web bağlantısına geçin. En son `index.html` içindeki `request()`, `update()`, `control()`, `render()` ve `draw()` fonksiyonlarını okuyun.

Böylece ekrandaki düğmeden Q güncellemesine kadar zinciri takip edebilirsiniz:

```text
HTML düğmesi / zamanlayıcı
    → HTTP isteği
    → app.py doğrulaması
    → Simulation.step()
    → gözlem → eylem → hareket → kişisel ödül
    → Q tablosunun güncellenmesi
    → bölüm bittiyse geçmiş ve JSON kaydı
    → HTTP cevabı
    → HTML metinleri ve tahtanın yeniden çizilmesi
```

Projeyi kendi cümlenizle anlatırken bu sırayı kullanabilirsiniz: “Önce kurallara uygun rastgele tahta kuruyorum. Her ajana yalnızca izin verilen gözlemi veriyorum. Gözlemi küçük bir duruma çevirip Q tablosuyla hareket seçtiriyorum. Eşzamanlı hareketten sonra yiyecekleri ve kişisel ödülleri çözüyorum. Sonuçla ilgili Q değerini güncelliyorum. Deneyim JSON'da kalıyor; HTML'den hem hareketleri hem geçmiş sonuçları izliyorum.”
