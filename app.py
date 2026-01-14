import streamlit as st
import pandas as pd
import json
import folium
import numpy as np
from streamlit_folium import folium_static
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import warnings

# Suppress the KMeans deprecation warning
warnings.filterwarnings("ignore", category=FutureWarning)

# --- Configuration for Streamlit App ---
st.set_page_config(layout="wide")

# --- Function to load and preprocess data ---
@st.cache_data
def load_data():
    df = pd.read_csv('master_data_pekan4_berlabel.csv')
    with open('38 Provinsi Indonesia - Provinsi.json', 'r') as f:
        geojson_data = json.load(f)

    # Synchronize Province Names
    mapping = {
        'DI Yogyakarta': 'Daerah Istimewa Yogyakarta',
        'Kep. Bangka Belitung': 'Kepulauan Bangka Belitung',
        'Kep. Riau': 'Kepulauan Riau'
    }
    df['province'] = df['province'].replace(mapping)
    return df, geojson_data

# --- Recommendation Function ---
def generate_recommendation(row):
    sgi = row['SGI']
    total_demand = row['total_demand']
    total_supply = row['total_supply']
    cluster = row['cluster_label']
    province = row['province']

    if cluster == 0: # Cluster 0 (e.g., typically high SGI, high demand, low supply - critical)
        if sgi > 0.5 and total_demand > total_supply:
            return f"Untuk Provinsi {province} (Klaster {cluster}): Kesenjangan 'Kritis' dengan permintaan tinggi ({total_demand:,}) dan pasokan rendah ({total_supply:,}). **Rekomendasi**: Fokus signifikan pada peningkatan kapasitas dan kualitas pelatihan di bidang ini. Pertimbangkan investasi dalam fasilitas dan kurikulum terkini."
        elif sgi > 0 and total_demand > total_supply:
            return f"Untuk Provinsi {province} (Klaster {cluster}): Kesenjangan 'Waspada' dengan permintaan lebih tinggi ({total_demand:,}) dari pasokan ({total_supply:,}). **Rekomendasi**: Terapkan program pelatihan percepatan dan kemitraan industri untuk memenuhi kebutuhan mendesak."
        else:
            return f"Untuk Provinsi {province} (Klaster {cluster}): Profil tidak seimbang dengan permintaan ({total_demand:,}) dan pasokan ({total_supply:,}) yang mengindikasikan kebutuhan akan penyesuaian. **Rekomendasi**: Lakukan studi pasar mendalam untuk mengidentifikasi akar masalah dan potensi intervensi yang tepat."
    elif cluster == 1: # Cluster 1 (e.g., typically balanced SGI or high supply - surplus)
        if sgi < 0 and total_supply > total_demand:
            return f"Untuk Provinsi {province} (Klaster {cluster}): 'Surplus' pasokan vokasi ({total_supply:,}) dibandingkan permintaan ({total_demand:,}). **Rekomendasi**: Fokus pada pengembangan pasar kerja baru, promosi ekspor keahlian, atau diversifikasi skill tenaga kerja ke bidang lain yang relevan."
        elif -0.2 <= sgi <= 0.2:
            return f"Untuk Provinsi {province} (Klaster {cluster}): Kondisi 'Seimbang' dengan SGI sekitar {sgi:.2f}. **Rekomendasi**: Pertahankan kualitas dan relevansi program pelatihan yang ada, serta pantau terus dinamika pasar untuk menjaga keseimbangan."
        else:
            return f"Untuk Provinsi {province} (Klaster {cluster}): Profil relatif seimbang, namun tetap perhatikan dinamika permintaan ({total_demand:,}) dan pasokan ({total_supply:,}). **Rekomendasi**: Implementasikan sistem monitoring pasar kerja yang responsif untuk deteksi dini pergeseran kebutuhan skill."
    else: # Cluster 2 (e.g., typically moderate SGI, moderate demand/supply)
        if sgi > 0.2 and total_demand > total_supply:
            return f"Untuk Provinsi {province} (Klaster {cluster}): Berada di zona 'Waspada' dengan permintaan ({total_demand:,}) yang melebihi pasokan ({total_supply:,}). **Rekomendasi**: Perluasan akses pelatihan dan fasilitasi magang untuk mempersiapkan lebih banyak tenaga kerja berkualitas."
        elif sgi < -0.2 and total_supply > total_demand:
            return f"Untuk Provinsi {province} (Klaster {cluster}): Cenderung 'Surplus' untuk skill ini ({total_supply:,} pasokan vs {total_demand:,} permintaan). **Rekomendasi**: Dorong pekerja untuk mengembangkan skill pelengkap atau eksplorasi peluang kerja di sektor lain yang sedang berkembang."
        else:
            return f"Untuk Provinsi {province} (Klaster {cluster}): Menunjukkan pola kesenjangan yang moderat. **Rekomendasi**: Lakukan evaluasi berkala terhadap efektivitas program pelatihan dan relevansi kurikulum dengan kebutuhan industri lokal."


# --- Main App Logic ---
def main_page():
    st.title("Halaman Utama: Peta Kesenjangan Vokasi & Rekomendasi")

    df, geojson_data = load_data()

    st.header("1. Peta Interaktif Kesenjangan Vokasi (SGI)")
    st.write("Pilih skill dan tahun untuk melihat peta kesenjangan vokasi di seluruh Indonesia.")

    # Dropdowns for user selection
    unique_skills = df['skill_name'].unique().tolist()
    unique_years = sorted(df['year'].unique().tolist())

    col1, col2 = st.columns(2)
    with col1:
        selected_skill = st.selectbox("Pilih Skill:", unique_skills, index=unique_skills.index('Cyber Security'))
    with col2:
        selected_year = st.selectbox("Pilih Tahun:", unique_years, index=unique_years.index(2025))

    # Filter Data for selected skill and year, and remove duplicates
    df_plot = df[(df['skill_name'] == selected_skill) & (df['year'] == selected_year)].copy()
    df_plot = df_plot.drop_duplicates(subset=['province'])

    # --- Clustering Analysis ---
    if not df_plot.empty:
        X_clustering = df_plot[['SGI', 'total_demand', 'total_supply']]
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X_clustering)
        kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(X_scaled)
        df_plot['cluster_label'] = cluster_labels

        # --- Generate Recommendations ---
        df_plot['recommendation'] = df_plot.apply(generate_recommendation, axis=1)

    # Set 'province' as index for efficient lookups
    df_plot_indexed = df_plot.set_index('province')

    # Define color mapping for status_gap
    color_map = {
        'Kritis': '#d62728',  # Merah
        'Waspada': '#ff7f0e', # Oranye
        'Surplus': '#2ca02c'  # Hijau
    }

    # Prepare geojson_data with formatted values for tooltips and styling
    # Create a deep copy of geojson_data to avoid modifying the cached original
    geojson_data_copy = json.loads(json.dumps(geojson_data)) # Deep copy

    for feature in geojson_data_copy['features']:
        province_name = feature['properties']['PROVINSI']
        if province_name in df_plot_indexed.index:
            data_row = df_plot_indexed.loc[province_name]
            feature['properties']['SGI_val_formatted'] = f"{data_row['SGI']:.2f}" if pd.notna(data_row['SGI']) else 'N/A'
            feature['properties']['Status_Gap_val'] = data_row['status_gap']
            feature['properties']['Total_Demand_val_formatted'] = f"{int(data_row['total_demand']):,}" if pd.notna(data_row['total_demand']) else 'N/A'
            feature['properties']['Total_Supply_val_formatted'] = f"{int(data_row['total_supply']):,}" if pd.notna(data_row['total_supply']) else 'N/A'
            feature['properties']['Cluster_Label_val'] = str(data_row['cluster_label']) # Add cluster label
            feature['properties']['Recommendation_val'] = data_row['recommendation'] # Add recommendation
        else:
            feature['properties']['SGI_val_formatted'] = 'N/A'
            feature['properties']['Status_Gap_val'] = 'Data Not Available'
            feature['properties']['Total_Demand_val_formatted'] = 'N/A'
            feature['properties']['Total_Supply_val_formatted'] = 'N/A'
            feature['properties']['Cluster_Label_val'] = 'N/A'
            feature['properties']['Recommendation_val'] = 'Tidak ada rekomendasi.'

    # Initialize Folium Map
    indonesia_center = [-2.5489, 118.0149]
    m = folium.Map(location=indonesia_center, zoom_start=5, tiles="cartodbpositron") # Added a tile layer for better visualization

    # Define a style function to apply discrete colors based on status_gap
    def get_color_for_province(feature):
        status = feature['properties']['Status_Gap_val']
        return {
            'fillColor': color_map.get(status, '#CCCCCC'), # Default to light grey for 'Data Not Available'
            'color': 'black',
            'weight': 0.5,
            'fillOpacity': 0.7 if status != 'Data Not Available' else 0.2
        }

    # Create a Folium GeoJson layer
    folium.GeoJson(
        geojson_data_copy,
        style_function=get_color_for_province,
        name=f'Kesenjangan Vokasi ({selected_skill} {selected_year})',
        highlight_function=lambda x: {'weight':3, 'fillOpacity':0.7},
        tooltip=folium.features.GeoJsonTooltip(
            fields=['PROVINSI', 'SGI_val_formatted', 'Status_Gap_val', 'Total_Demand_val_formatted', 'Total_Supply_val_formatted', 'Cluster_Label_val', 'Recommendation_val'],
            aliases=['Provinsi:', 'SGI:', 'Status Gap:', 'Total Demand:', 'Total Supply:', 'Klaster:', 'Rekomendasi:'],
            localize=True,
            sticky=False,
            labels=True,
            max_width=800
        )
    ).add_to(m)

    folium.LayerControl().add_to(m)

    # Display the map in Streamlit
    folium_static(m, width=1000, height=600)

    st.markdown("---")
    st.header("2. Implementasi Logika Rekomendasi Adaptif (berbasis SGI tertinggi dalam cluster)")

    if not df_plot.empty:
        st.subheader(f"Rekomendasi untuk Skill: {selected_skill} - Tahun: {selected_year}")
        # Display recommendations for each province
        for idx, row in df_plot.iterrows():
            st.markdown(f"**{row['province']} (Klaster {row['cluster_label']}):** {row['recommendation']}")
    else:
        st.info("Tidak ada data tersedia untuk skill dan tahun yang dipilih untuk menghasilkan rekomendasi.")

def page_2():
    st.title("Halaman Lain: Analisis Lebih Lanjut")
    st.write("""
        Selamat datang di Halaman Lain!

        Halaman ini akan dikembangkan untuk menyajikan analisis yang lebih mendalam,
        seperti:
        -   Grafik tren SGI dari waktu ke waktu.
        -   Perbandingan SGI antar provinsi atau antar skill.
        -   Tabel data detail yang dapat difilter dan diunduh.

        Fitur-fitur interaktif akan ditambahkan di sini di masa mendatang.
    """)

# --- Multi-page Navigation ---
st.sidebar.title("Navigasi")
selection = st.sidebar.radio("Go to", ["Halaman Utama", "Halaman Lain"])

if selection == "Halaman Utama":
    main_page()
elif selection == "Halaman Lain":
    page_2()
