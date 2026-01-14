import streamlit as st
import pandas as pd
import json
import folium
from streamlit_folium import folium_static

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Dashboard SGI Indonesia", layout="wide")

# --- 2. FUNGSI LOAD DATA ---
@st.cache_data
def load_data():
    df = pd.read_csv('master_data_pekan4_berlabel.csv')
    with open('38 Provinsi Indonesia - Provinsi.json', 'r') as f:
        geojson_data = json.load(f)

    # Sinkronisasi Nama Provinsi
    mapping = {
        'DI Yogyakarta': 'Daerah Istimewa Yogyakarta',
        'Kep. Bangka Belitung': 'Kepulauan Bangka Belitung',
        'Kep. Riau': 'Kepulauan Riau'
    }
    df['province'] = df['province'].replace(mapping)
    return df, geojson_data

# Memanggil data secara Global
df, geojson_data = load_data()

# --- 3. HALAMAN 1: PETA PANAS ---
def page_1():
    st.title("🗺️ Geo-Clustering Skill Gap Index (SGI): Model Adaptif Pemetaan Kompetensi Vokasi untuk Optimalisasi Kebutuhan Tenaga Kerja Regional")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.subheader("Filter Analisis")
        # Pastikan Key UNIK ('yr_p1', 'sk_p1')
        selected_year = st.selectbox("Tahun", sorted(df['year'].unique()), key='yr_p1')
        selected_skill = st.selectbox("Bidang Keahlian (Skill)", sorted(df['skill_name'].unique()), key='sk_p1')
    
    df_plot = df[(df['year'] == selected_year) & (df['skill_name'] == selected_skill)].copy()
    data_dict = df_plot.set_index('province')

    with col2:
        m = folium.Map(location=[-2.5, 118], zoom_start=5, tiles="CartoDB positron")

        folium.Choropleth(
            geo_data=geojson_data,
            name="SGI Map",
            data=df_plot,
            columns=["province", "SGI"],
            key_on="feature.properties.PROVINSI",
            fill_color="YlOrRd",
            fill_opacity=0.7,
            line_opacity=0.2,
            legend_name="Skill Gap Index (SGI)",
            highlight=True
        ).add_to(m)

        # Injeksi data ke GeoJSON untuk Tooltip
        for feature in geojson_data['features']:
            prov_name = feature['properties']['PROVINSI']
            if prov_name in data_dict.index:
                feature['properties']['SGI_Val'] = f"{data_dict.loc[prov_name, 'SGI']:.2f}"
                feature['properties']['Status'] = data_dict.loc[prov_name, 'status_gap']
            else:
                feature['properties']['SGI_Val'] = "N/A"
                feature['properties']['Status'] = "Data Tidak Tersedia"

        folium.GeoJson(
            geojson_data,
            style_function=lambda x: {'fillColor': 'transparent', 'color': 'black', 'weight': 0.5},
            tooltip=folium.GeoJsonTooltip(
                fields=['PROVINSI', 'SGI_Val', 'Status'],
                aliases=['Provinsi:', 'Nilai SGI:', 'Status Gap:'],
                localize=True
            )
        ).add_to(m)

        folium_static(m, width=950, height=550)

# --- 4. HALAMAN 2: REKOMENDASI ---
def page_2():
    st.title("💡 Rekomendasi Kebijakan & Analisis Adaptif")
    st.markdown("Halaman ini memberikan arahan strategis berdasarkan posisi kompetensi wilayah Anda.")

    # 1. Pilih Provinsi
    selected_prov = st.selectbox("📍 Pilih Provinsi Anda:", sorted(df['province'].unique()), key='prov_p2')

    # Filter Data tahun terbaru
    df_recent = df[df['year'] == 2025]
    prov_data = df_recent[df_recent['province'] == selected_prov]
    
    if not prov_data.empty:
        user_cluster = prov_data['cluster_label'].iloc[0]
        
        # 2. Logika Rekomendasi Adaptif
        # Mencari skill dengan SGI rata-rata tertinggi di cluster yang sama
        cluster_recs = df_recent[df_recent['cluster_label'] == user_cluster].groupby('skill_name')['SGI'].mean().sort_values(ascending=False)
        top_skill = cluster_recs.index[0]
        top_sgi_val = cluster_recs.values[0]

        # 3. PENJELASAN REKOMENDASI (POLICY INSIGHT)
        st.success(f"### 🎯 Prioritas Utama: {top_skill}")
        
        # Penjelasan Berbasis Data
        st.info(f"""
        **Analisis Situasi:**
        Provinsi **{selected_prov}** berada dalam **Cluster {user_cluster}**. Secara kolektif dalam kelompok ini, bidang **{top_skill}** memiliki tingkat kesenjangan tertinggi (SGI: {top_sgi_val:.2f}). 
        
        **Rekomendasi Kebijakan:**
        1. **Penyelarasan Kurikulum:** Dinas Pendidikan/Pemerintah Daerah disarankan untuk segera melakukan sinkronisasi kurikulum vokasi dengan standar industri di bidang {top_skill}.
        2. **Alokasi Beasiswa:** Mengalihkan sebagian porsi beasiswa kejuruan untuk fokus pada pelatihan intensif (bootcamp/sertifikasi) bidang {top_skill}.
        3. **Incentive Industri:** Memberikan insentif bagi perusahaan di bidang {top_skill} yang bersedia menyediakan tempat magang (internship) bagi lulusan lokal di {selected_prov}.
        """)

        # 4. Visualisasi Pendukung
        st.write(f"### Ranking Kebutuhan Skill di Cluster {user_cluster}")
        st.bar_chart(cluster_recs)
        
        # Tabel Data Detail
        with st.expander("Lihat Data Mentah Cluster"):
            st.write(cluster_recs)
    else:
        st.error("Data tidak ditemukan untuk wilayah ini.")

# --- 5. NAVIGASI (HANYA GUNAKAN LOGIKA INI DI BAGIAN PALING BAWAH) ---
st.sidebar.title("🧭 Menu Navigasi")

# Simpan pilihan ke dalam variabel 'selection'
selection = st.sidebar.radio("Pilih Tampilan:", ["Halaman 1: Peta Panas", "Halaman 2: Rekomendasi Adaptif"])

# PENTING: Gunakan blok IF-ELSE ini agar hanya SATU halaman yang dipanggil
if selection == "Halaman 1: Peta Panas":
    page_1()  # Panggil fungsi page_1 HANYA jika dipilih
elif selection == "Halaman 2: Rekomendasi Adaptif":
    page_2()  # Panggil fungsi page_2 HANYA jika dipilih
