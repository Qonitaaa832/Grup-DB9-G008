import streamlit as st
import pandas as pd
import json
import folium
from streamlit_folium import folium_static
import matplotlib.pyplot as plt

# ======================================================
# TAMBAHAN IMPORT UNTUK PDF
# ======================================================
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4

# ======================================================
# 1. KONFIGURASI HALAMAN
# ======================================================
st.set_page_config(
    page_title="Dashboard SGI Indonesia",
    layout="wide"
)

# ======================================================
# 2. GLOBAL CSS (NAVBAR + FIX DROPDOWN)
# ======================================================
st.markdown("""
<style>
/* ===== BASE ===== */
.main {
    background-color: #f8fafc;
}

h1, h2, h3 {
    color: #0f172a;
    font-weight: 700;
}

p, li {
    color: #1f2937;
    font-size: 15px;
}

/* ===== FIX DROPDOWN ===== */
div[data-baseweb="select"] {
    z-index: 10000 !important;
}

/* ===== NAVBAR ===== */
.navbar {
    position: sticky;
    top: 0;
    z-index: 9999;
    background: linear-gradient(90deg, #1e3a8a, #1d4ed8);
    padding: 14px 32px;
    margin-bottom: 24px;
    border-radius: 0 0 14px 14px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.18);
}

.nav-btn {
    background: transparent;
    border: none;
    color: #e5e7eb;
    font-size: 15px;
    font-weight: 600;
    padding: 8px 20px;
    border-radius: 999px;
    cursor: pointer;
}

.nav-btn:hover {
    background: rgba(255,255,255,0.18);
}

.nav-active {
    background: white !important;
    color: #1e3a8a !important;
}

/* ===== CARD ===== */
.card {
    background: white;
    padding: 20px;
    border-radius: 14px;
    box-shadow: 0 8px 26px rgba(0,0,0,0.08);
    margin-bottom: 20px;
}

/* ===== TOP 5 ===== */
.priority {
    background: #fee2e2;
    border-left: 6px solid #dc2626;
    padding: 12px;
    border-radius: 10px;
    margin-bottom: 12px;
}

/* ===== MAP ===== */
iframe {
    width: 100% !important;
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)

# ======================================================
# 3. LOAD DATA (TIDAK DIUBAH)
# ======================================================
@st.cache_data
def load_data():
    df = pd.read_csv('master_data_pekan4_berlabel.csv')
    with open('38 Provinsi Indonesia - Provinsi.json', 'r') as f:
        geojson_data = json.load(f)

    mapping = {
        'DI Yogyakarta': 'Daerah Istimewa Yogyakarta',
        'Kep. Bangka Belitung': 'Kepulauan Bangka Belitung',
        'Kep. Riau': 'Kepulauan Riau'
    }
    df['province'] = df['province'].replace(mapping)
    return df, geojson_data

df, geojson_data = load_data()

# ======================================================
# 4. SESSION STATE NAVIGASI
# ======================================================
if "page" not in st.session_state:
    st.session_state.page = "page1"

# ======================================================
# 5. NAVBAR ATAS + PENAMBAHAN UNTUK CALCULATOR
# ======================================================
col_nav1, col_nav2, col_nav3 = st.columns([1,1,1])

with col_nav1:
    if st.button("🗺️ Peta Panas Nasional"):
        st.session_state.page = "page1"
with col_nav2:
    if st.button("💡 Rekomendasi Kebijakan"):
        st.session_state.page = "page2"
with col_nav3:
    if st.button("🧮 SGI Calculator"):
        st.session_state.page = "calculator"

# ======================================================
# 6. HALAMAN 1 (TIDAK DIUBAH)
# ======================================================
def page_1():
    st.markdown("""
    <div class="card">
        <h2>Geo-Clustering Skill Gap Index (SGI)</h2>
        <p>Pemetaan nasional kesenjangan kompetensi tenaga kerja berbasis wilayah dan bidang keahlian.</p>
    </div>
    """, unsafe_allow_html=True)

    # FILTER
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        selected_year = st.selectbox("Tahun", sorted(df['year'].unique()), key="yr_new")
    with col_f2:
        selected_skill = st.selectbox("Bidang Keahlian", sorted(df['skill_name'].unique()), key="sk_new")

    df_plot = df[(df['year'] == selected_year) & (df['skill_name'] == selected_skill)]
    data_dict = df_plot.set_index('province')

    col_map, col_top = st.columns([4, 1.4])

    # MAP
    with col_map:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        m = folium.Map(location=[-2.5, 118], zoom_start=5, tiles="CartoDB positron")
        folium.Choropleth(
            geo_data=geojson_data,
            data=df_plot,
            columns=["province", "SGI"],
            key_on="feature.properties.PROVINSI",
            fill_color="YlOrRd",
            fill_opacity=0.85,
            line_opacity=0.3,
            legend_name="Skill Gap Index (SGI)"
        ).add_to(m)
        for feature in geojson_data['features']:
            prov = feature['properties']['PROVINSI']
            if prov in data_dict.index:
                feature['properties']['SGI_Val'] = f"{data_dict.loc[prov, 'SGI']:.2f}"
                feature['properties']['Status'] = data_dict.loc[prov, 'status_gap']
            else:
                feature['properties']['SGI_Val'] = "N/A"
                feature['properties']['Status'] = "Tidak tersedia"
        folium.GeoJson(
            geojson_data,
            tooltip=folium.GeoJsonTooltip(
                fields=['PROVINSI', 'SGI_Val', 'Status'],
                aliases=['Provinsi', 'Nilai SGI', 'Status Gap']
            )
        ).add_to(m)
        folium_static(m, height=720)
        st.markdown("</div>", unsafe_allow_html=True)

    # TOP 5
    with col_top:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("🔥 Top 5 Provinsi Demand Tertinggi")
        top5 = df_plot[['province', 'SGI']].sort_values(by='SGI', ascending=False).head(5)
        for i, row in enumerate(top5.itertuples(), 1):
            st.markdown(
                f"""
                <div class="priority">
                    <b>{i}. {row.province}</b><br>
                    SGI: {row.SGI:.2f}
                </div>
                """,
                unsafe_allow_html=True
            )
        st.markdown("</div>", unsafe_allow_html=True)

# ======================================================
# 7. HALAMAN 2 (PDF DITAMBAH TOP 5 JOB DEMAND)
# ======================================================
def page_2():
    st.title("💡 Rekomendasi Kebijakan & Analisis Adaptif")
    st.markdown("Halaman ini memberikan arahan strategis berdasarkan posisi kompetensi wilayah Anda.")

    selected_prov = st.selectbox("📍 Pilih Provinsi Anda:", sorted(df['province'].unique()), key='prov_p2')

    df_recent = df[df['year'] == 2025]
    prov_data = df_recent[df_recent['province'] == selected_prov]
    
    if not prov_data.empty:
        user_cluster = prov_data['cluster_label'].iloc[0]

        cluster_recs = df_recent[df_recent['cluster_label'] == user_cluster] \
            .groupby('skill_name')['SGI'].mean().sort_values(ascending=False)

        top_skill = cluster_recs.index[0]
        top_sgi_val = cluster_recs.values[0]

        st.success(f"### 🎯 Prioritas Utama: {top_skill}")

        st.info(f"""
        **Analisis Situasi:**
        Provinsi **{selected_prov}** berada dalam **Cluster {user_cluster}**. Secara kolektif dalam kelompok ini, bidang **{top_skill}** memiliki tingkat kesenjangan tertinggi (SGI: {top_sgi_val:.2f}). 
        
        **Rekomendasi Kebijakan:**
        1. **Penyelarasan Kurikulum:** Dinas Pendidikan/Pemerintah Daerah disarankan untuk segera melakukan sinkronisasi kurikulum vokasi dengan standar industri di bidang {top_skill}.
        2. **Alokasi Beasiswa:** Mengalihkan sebagian porsi beasiswa kejuruan untuk fokus pada pelatihan intensif (bootcamp/sertifikasi) bidang {top_skill}.
        3. **Incentive Industri:** Memberikan insentif bagi perusahaan di bidang {top_skill} yang bersedia menyediakan tempat magang (internship) bagi lulusan lokal di {selected_prov}.
        """)

        st.write(f"### Ranking Kebutuhan Skill di Cluster {user_cluster}")
        st.bar_chart(cluster_recs)

        with st.expander("Lihat Data Mentah Cluster"):
            st.write(cluster_recs)

        # ===============================
        # PDF BUTTON
        # ===============================
        def generate_policy_pdf(province, cluster, top_skill, sgi_value):
            file_name = f"Policy_Brief_{province.replace(' ', '_')}_SGI.pdf"
            doc = SimpleDocTemplate(file_name, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []

            story.append(Paragraph("POLICY BRIEF – SKILL GAP INDEX (SGI)", styles["Title"]))
            story.append(Spacer(1, 14))

            story.append(Paragraph(f"<b>Provinsi:</b> {province}", styles["Normal"]))
            story.append(Paragraph(f"<b>Cluster:</b> {cluster}", styles["Normal"]))
            story.append(Paragraph(f"<b>Bidang Prioritas:</b> {top_skill}", styles["Normal"]))
            story.append(Paragraph(f"<b>Nilai SGI:</b> {sgi_value:.2f}", styles["Normal"]))
            story.append(Spacer(1, 12))

            story.append(Paragraph("<b>Rekomendasi Kebijakan</b>", styles["Heading2"]))
            story.append(Paragraph(
                f"""
                Provinsi <b>{province}</b> berada pada cluster <b>{cluster}</b>.
                Bidang <b>{top_skill}</b> menunjukkan tingkat kesenjangan tertinggi.
                <br/><br/>
                Rekomendasi:
                <br/>1. Penyelarasan kurikulum vokasi
                <br/>2. Penguatan sertifikasi kompetensi
                <br/>3. Insentif kemitraan industri
                """,
                styles["Normal"]
            ))

            # ===============================
            # Tambahkan grafik Top 5 Job Demand per Tahun
            # ===============================
            df_prov = df[df['province'] == province]
            top5_yearly = df_prov.groupby(['year', 'skill_name'])['SGI'].mean().reset_index()

            for year in sorted(df_prov['year'].unique()):
                top5 = top5_yearly[top5_yearly['year'] == year].sort_values('SGI', ascending=False).head(5)
                plt.figure(figsize=(6,3))
                plt.barh(top5['skill_name'], top5['SGI'], color='salmon')
                plt.xlabel('SGI')
                plt.title(f'Top 5 Job Demand {province} - {year}')
                plt.gca().invert_yaxis()
                img_path = f'top5_{province}_{year}.png'
                plt.tight_layout()
                plt.savefig(img_path)
                plt.close()

                story.append(Spacer(1, 12))
                story.append(Paragraph(f"<b>Top 5 Job Demand Tahun {year}</b>", styles["Heading2"]))
                story.append(Image(img_path, width=400, height=200))

            doc.build(story)
            return file_name

        if st.button("📄 Export Policy Brief (PDF)"):
            pdf_file = generate_policy_pdf(
                selected_prov,
                user_cluster,
                top_skill,
                top_sgi_val
            )
            with open(pdf_file, "rb") as f:
                st.download_button(
                    "⬇️ Download PDF",
                    f,
                    file_name=pdf_file,
                    mime="application/pdf"
                )

    else:
        st.error("Data tidak ditemukan untuk wilayah ini.")

# ======================================================
# 8. HALAMAN 3: SGI CALCULATOR (BARU)
# ======================================================
def page_sgi_calculator():
    st.markdown("""
    <div class="card">
        <h2>🧮 SGI Calculator (Simulator Kebijakan)</h2>
        <p>Simulasikan pengaruh supply, demand, dan mismatch terhadap nilai SGI.</p>
    </div>
    """, unsafe_allow_html=True)

    demand = st.slider("📈 Demand Industri (%)", 0, 100, 70) / 100
    supply = st.slider("🎓 Supply Lulusan (%)", 0, 100, 50) / 100
    certification = st.slider("📜 Tingkat Sertifikasi (%)", 0, 100, 40) / 100
    mismatch = st.slider("⚠️ Tingkat Mismatch (%)", 0, 100, 60) / 100

    sgi = (
        (demand - supply) * 0.4 +
        mismatch * 0.3 +
        (1 - certification) * 0.3
    )

    st.metric("Nilai SGI (Simulasi)", f"{sgi:.2f}")

    if sgi >= 0.6:
        st.error("🔴 Status: KRITIS")
    elif sgi >= 0.4:
        st.warning("🟠 Status: TINGGI")
    elif sgi >= 0.2:
        st.info("🟡 Status: SEDANG")
    else:
        st.success("🟢 Status: AMAN")

# ======================================================
# 9. ROUTING
# ======================================================
if st.session_state.page == "page1":
    page_1()
elif st.session_state.page == "page2":
    page_2()
else:
    page_sgi_calculator()
