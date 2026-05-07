# 🎬 TMDB Film Hasılat Tahmin Projesi

> **Amaç:** TMDB veri setini kullanarak bir filmin gişe hasılatını tahmin eden makine öğrenmesi modeli geliştirmek ve veri analizi ile içgörüler üretmek.

---

## 📦 Veri Seti

| Kaynak | Bağlantı |
|--------|----------|
| Kaggle — TMDB Movie Metadata | [https://www.kaggle.com/datasets/tmdb/tmdb-movie-metadata](https://www.kaggle.com/datasets/tmdb/tmdb-movie-metadata) |

**İçerik:**
- `tmdb_5000_movies.csv` — Bütçe, hasılat, tür, dil, süre, popülerlik, puan, oy sayısı
- `tmdb_5000_credits.csv` — Yönetmen, başrol oyuncular, ekip bilgileri

Ham veri **~5.000 film** kaydı içermekte olup SQL Server ortamında (`TMDB_MovieDB`) yapılandırılmıştır.

---

## 🗂️ Proje Yapısı

```
tmdb-movie-data-analysis/
│
├── tmdb_analysis_mssql/
│   ├── script.sql                              # SQL sorgular ve tablo tanımları
│   ├── TMDB_MovieDB.bak                        # SQL Server yedek dosyası
│   │
│   ├── TMDB_MovieDB_Genel_Istatistikler.ipynb  # Tanımlayıcı istatistik analizleri
│   ├── TMDB_MovieDB_Film_gise_basarisi.ipynb   # Gişe başarısı analizi
│   ├── TMDB_MovieDB_Film_kar_durumu.ipynb      # Kâr/zarar analizi
│   ├── TMDB_MovieDB_Film_tur_gise_basarisi.ipynb # Tür bazlı gişe analizi
│   │
│   ├── model/
│   │   ├── xgboost_modeli.ipynb                # Model eğitim ve değerlendirme notebook'u
│   │   ├── tmdb_xgboost_best_model.json        # Kaydedilen XGBoost modeli (deploy'a hazır)
│   │   ├── tmdb_advanced_encoders.pkl          # Label/Target Encoder objeleri
│   │   ├── feature_importance.png              # Değişken önemi grafiği
│   │   ├── gercek_vs_tahmin.png                # Gerçek – Tahmin dağılımı
│   │   ├── confusion_matrix.png                # Konfüzyon matrisi
│   │   └── model_analiz_raporu.txt             # Model metrik raporu
│   │
│   ├── grafikler/                              # Tüm EDA görselleştirmeleri (13 grafik)
│   └── sonuclar/
│       └── analiz_sonucu.txt                   # Analiz bulguları (metin raporu)
│
├── tmdb-movie-metadata/                        # Ham veri seti
├── requirements.txt
└── README.md
```

---

## ⚙️ Kurulum

### Gereksinimler

```bash
pip install -r requirements.txt
```

`requirements.txt` içeriği:
```
joblib==1.5.3
matplotlib==3.10.9
numpy==2.4.4
pandas==3.0.2
pyodbc==5.3.0
scikit_learn==1.8.0
seaborn==0.13.2
xgboost==3.2.0

```

### Veritabanı Kurulumu

1. MS SQL Server'a `TMDB_MovieDB.bak` dosyasını restore edin.
2. `script.sql` dosyasını çalıştırarak tabloları ve ilişkileri tanımlayın.

---

## 🤖 Model: XGBoost Regressor

### Neden XGBoost?

- Bütçe ile hasılat arasındaki **doğrusal olmayan** karmaşık ilişkileri ensemble yapısıyla yakalar.
- Yerleşik **L1/L2 regularization** sayesinde overfitting'e karşı dirençlidir.
- **Feature Importance** desteği ile yorumlanabilir (açıklanabilir AI).
- GPU hızlandırması destekler — bu projede **NVIDIA GeForce RTX 4050** kullanılmıştır.

### Ön İşleme Pipeline

| Adım | Yöntem |
|------|--------|
| Eksik veri | NULL ve sıfır bütçeli kayıtlar çıkarıldı |
| Kategorik kodlama | `LabelEncoder` — yönetmen, başrol oyuncu |
| Tür kodlama | `TargetEncoder` — genre sütunları |
| Hedef değişken | Ham hasılat (`revenue`), log-transform uygulanmadı |

---

## 📊 Model Sonuçları

| Metrik | Değer | Yorum |
|--------|-------|-------|
| **R² Skoru** | **0.8497** | Hasılat değişiminin %85'ini açıklıyor |
| RMSE | $68,791,289 | Ortalama karekök hata |
| MAE | $37,830,620 | Ortalama mutlak hata |
| MAPE | %50.90 | Aykırı değerlere (blockbuster) duyarlı |

> **Not:** MAPE'nin yüksek görünmesi, film hasılat dağılımının sağa çarpık (blockbuster aykırı değer yoğun) yapısından kaynaklanmaktadır. R² ve MAE değerleri modelin gerçek performansını daha doğru yansıtmaktadır.

**En Etkili Değişkenler (Feature Importance):**
1. `budget` — Bütçe
2. `vote_count` — Oy sayısı
3. `popularity` — Popülerlik skoru
4. `runtime` — Film süresi

---

## 🔍 Temel Analiz Bulguları

### Bütçe ve Kâr İlişkisi
- Dev bütçeli **47 filmden yalnızca 1 tanesi zarar etti.**
- En büyük zarar: **The Lone Ranger** → −$165,710,090
- Genel trend: yüksek bütçe, kâr olasılığını artırır ancak garanti vermez.

### Rating ve Gişe
| Rating Grubu | Ortalama Hasılat |
|---|---|
| Düşük (0–5) | $40,869,461 |
| Orta (5–7) | $108,391,339 |
| **Yüksek (7–10)** | **$162,107,173** |

→ Yüksek puan, düşük puana kıyasla **%296 fazla** ortalama gelir anlamına gelmektedir.

### Tür Bazlı Ortalama Hasılat (İlk 10)

| Sıra | Tür | Ort. Hasılat |
|------|-----|-------------|
| 1 | Animation | $276,503,497 |
| 2 | Adventure | $244,209,721 |
| 3 | Fantasy | $233,567,521 |
| 4 | Family | $218,018,949 |
| 5 | Science Fiction | $185,795,526 |
| 6 | Action | $173,361,611 |
| 7 | Thriller | $107,664,678 |
| 8 | Comedy | $104,566,029 |
| 9 | Mystery | $101,674,339 |
| 10 | War | $99,331,524 |

### Sektör Liderleri

| Kategori | Lider | Toplam Hasılat |
|----------|-------|---------------|
| En iyi oyuncu | Stan Lee | $17,364,063,582 |
| En iyi yönetmen | Steven Spielberg | $9,147,393,164 |
| En iyi şirket | Warner Bros. | $49,155,747,874 |

### Mevsimsellik
- **Haziran** en yüksek ortalama hasılatı getiren ay.
- Kış tatili dönemi (Aralık) da peak sezon kategorisindedir.

---

## 📈 Görselleştirmeler

`tmdb_analysis_mssql/grafikler/` dizininde yer alan grafik listesi:

| Dosya | İçerik |
|-------|--------|
| `yillik_hasilat_trendi.png` | Yıllara göre ortalama hasılat değişimi |
| `yillik_film_sayisi_trendi.png` | Yıllık üretilen film sayısı trendi |
| `aylik_hasilat_mevsimsellik.png` | Aylık hasılat mevsimsellik analizi |
| `tur_vs_hasilat.png` | Türe göre ortalama hasılat karşılaştırması |
| `butce_kar_analizi.png` | Bütçe ve kâr ilişkisi |
| `rating_vs_revenue.png` | Puan grubu ve hasılat ilişkisi |
| `rating_scatter.png` | Puan dağılımı saçılım grafiği |
| `sure_puan_iliskisi.png` | Film süresi ve puan ilişkisi |
| `korelasyon_isi_haritasi.png` | Tüm sayısal değişkenler arası korelasyon |
| `oyuncu_hasilat_top10.png` | En çok hasılat getiren oyuncular |
| `yonetmen_hasilat_top10.png` | En çok hasılat getiren yönetmenler |
| `sirket_hasilat_top10.png` | En çok hasılat getiren şirketler |
| `en_cok_kar_edenler.png` | En yüksek kâr oranına sahip filmler |

---

## 🚀 Çalıştırma

### Analiz Notebook'larını Çalıştırma

```bash
jupyter notebook
```

Sırayla çalıştırılması önerilen notebook'lar:
1. `TMDB_MovieDB_Genel_Istatistikler.ipynb`
2. `TMDB_MovieDB_Film_kar_durumu.ipynb`
3. `TMDB_MovieDB_Film_gise_basarisi.ipynb`
4. `TMDB_MovieDB_Film_tur_gise_basarisi.ipynb`
5. `model/xgboost_modeli.ipynb`


## 🧰 Teknik Altyapı

| Bileşen | Teknoloji |
|---------|-----------|
| Dil | Python 3.x |
| Veritabanı | Microsoft SQL Server |
| ML Kütüphanesi | XGBoost, Scikit-learn |
| Veri İşleme | Pandas, NumPy |
| Görselleştirme | Matplotlib, Seaborn |
| Donanım | NVIDIA GeForce RTX 4050 (GPU hızlandırma) |
| Notebook Ortamı | Jupyter Notebook |

---

## 👤 Proje Sahibi

**berkyz** — [GitHub](https://github.com/berkyz/tmdb-movie-data-analysis)

---

> *Bu proje; veri bilimi, makine öğrenmesi ve SQL tabanlı veri analizi pratiklerini bir araya getiren kapsamlı bir film hasılat tahmin çalışmasıdır.*
