# 🇮🇩 Dashboard Analisis Kesenjangan Vokasi Indonesia

Proyek ini adalah sistem pendukung keputusan (Decision Support System) yang memvisualisasikan **Skill Gap Index (SGI)** di 38 Provinsi Indonesia. Aplikasi ini membantu mengidentifikasi ketidakseimbangan antara permintaan industri (*Demand*) dan ketersediaan lulusan vokasi (*Supply*).

## 🚀 Fitur Utama
- **Halaman 1: Peta Panas Interaktif**: Visualisasi spasial menggunakan Folium untuk melihat status kesenjangan (Kritis, Waspada, Surplus) di setiap provinsi.
- **Logika Rekomendasi Adaptif**: Memberikan saran strategis otomatis berdasarkan nilai SGI tertinggi di setiap cluster wilayah.
- **Analisis Cluster**: Mengelompokkan wilayah dengan karakteristik serupa untuk standarisasi kebijakan vokasi.

## 🛠️ Teknologi yang Digunakan
- **Python** (Bahasa Pemrograman Utama)
- **Streamlit** (Framework Web Dashboard)
- **Folium & Plotly** (Visualisasi Peta & Grafik)
- **Scikit-Learn** (K-Means Clustering)
- **Pandas** (Manipulasi Data)

## 📁 Struktur Repositori
- `app.py`: Script utama aplikasi Streamlit.
- `master_data_pekan4_berlabel.csv`: Dataset master hasil pengolahan data.
- `38 Provinsi Indonesia - Provinsi.json`: Data GeoJSON untuk batas wilayah provinsi.
- `requirements.txt`: Daftar library Python yang dibutuhkan.

## 🏃 Cara Menjalankan Secara Lokal
1. Clone repositori ini:
   ```bash
   git clone [https://github.com/Qonitaaa832/Grup-DB9-G008.git](https://github.com/Qonitaaa832/Grup-DB9-G008.git)
