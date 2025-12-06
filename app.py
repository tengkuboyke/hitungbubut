import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd

# --- 1. SETTING HALAMAN ---
st.set_page_config(page_title="Pro Shop Database System", layout="wide")
st.title("🏭 Smart Manufacturing Estimator (Live DB)")

# --- 2. FUNGSI TARIK DATABASE (THE MAGIC) ---
# Ini akan mengambil file CSV langsung dari GitHub Anda
@st.cache_data
def load_data():
    # Link RAW ke file CSV Anda (JANGAN DIUBAH)
    url = "https://raw.githubusercontent.com/tengkuboyke/hitungbubut/main/materials.csv"
    try:
        df = pd.read_csv(url)
        return df
    except Exception as e:
        st.error(f"Gagal membaca database! Pastikan file 'materials.csv' ada di GitHub. Error: {e}")
        return None

# Load Database saat aplikasi mulai
df_material = load_data()

# Jika database gagal diload, stop aplikasi
if df_material is None:
    st.stop()

# --- 3. SIDEBAR: INPUT DATA ---
st.sidebar.header("1. Material Selection")

# Dropdown mengambil nama material DARI FILE CSV (Bukan hardcode lagi!)
# Kita ambil kolom 'Material' dari tabel
pilihan_material = st.sidebar.selectbox("Pilih Material (Live Stock)", df_material['Material'].unique())

# FILTER OTOMATIS: Ambil data berat jenis & harga berdasarkan pilihan
# Ini cara Python mencari baris Excel:
data_terpilih = df_material[df_material['Material'] == pilihan_material].iloc[0]

# Simpan data ke variabel
bj_actual = data_terpilih['Density']
harga_actual = data_terpilih['Price_Kg']
factor_actual = data_terpilih['Hardness_Factor']

# Tampilkan Info Material di Sidebar biar user yakin
st.sidebar.info(f"📊 Info Data:\nDensity: {bj_actual} g/cm3\nHarga: Rp {harga_actual:,.0f}/kg\nHardness: {factor_actual}x")

st.sidebar.markdown("---")
st.sidebar.header("2. Geometri & Proses")

tipe_proses = st.sidebar.radio("Jenis Pekerjaan:", ["Milling (Block)", "Turning (Round Bar)"])

if tipe_proses == "Milling (Block)":
    p = st.sidebar.number_input("Panjang (mm)", 0, 2000, 100)
    l = st.sidebar.number_input("Lebar (mm)", 0, 1000, 50)
    t = st.sidebar.number_input("Tebal (mm)", 0, 500, 20)
    vol_cm3 = (p * l * t) / 1000
else:
    d = st.sidebar.number_input("Diameter (mm)", 0, 500, 50)
    pj = st.sidebar.number_input("Panjang (mm)", 0, 2000, 100)
    r = d / 2
    vol_cm3 = (np.pi * (r**2) * pj) / 1000

# --- 4. KALKULASI HARGA ---
# A. Biaya Material (Real Price dari CSV)
berat_kg = (vol_cm3 * bj_actual) / 1000
biaya_material = berat_kg * harga_actual

# B. Biaya Machining (Dipengaruhi Hardness Factor dari CSV)
# Jika material keras (Hardness > 1), waktu mesin otomatis dikali lipat
st.sidebar.markdown("---")
jam_estimasi = st.sidebar.number_input("Estimasi Waktu Mesin (Jam)", 0.5, 50.0, 1.0, step=0.5)
tarif_mesin = st.sidebar.number_input("Tarif Mesin (Rp/Jam)", value=100000, step=10000)
margin = st.sidebar.slider("Profit Margin (%)", 10, 100, 30)

# Rumus: Waktu x Tarif x Tingkat Kekerasan Material
biaya_mesin = jam_estimasi * tarif_mesin * factor_actual

hpp = biaya_material + biaya_mesin
harga_jual = hpp + (hpp * (margin/100))

# --- 5. DASHBOARD OUTPUT ---
col1, col2 = st.columns([1, 1.5])

with col1:
    st.subheader("💰 Smart Quotation")
    st.markdown(f"Material: **{pilihan_material}**")
    
    st.write("Breakdown Biaya:")
    col_a, col_b = st.columns(2)
    col_a.metric("Berat", f"{berat_kg:.2f} kg")
    col_a.metric("Cost Material", f"Rp {biaya_material:,.0f}")
    
    col_b.metric("Difficulty", f"{factor_actual}x")
    col_b.metric("Cost Mesin", f"Rp {biaya_mesin:,.0f}")
    
    st.divider()
    st.success(f"HARGA JUAL: Rp {harga_jual:,.0f}")
    
    if factor_actual > 1.0:
        st.warning(f"⚠️ Note: Biaya mesin naik {int((factor_actual-1)*100)}% karena material ini keras.")

with col2:
    st.subheader("🧊 Visualisasi")
    fig = go.Figure()
    if tipe_proses == "Milling (Block)":
        fig.add_trace(go.Mesh3d(x=[0, p, p, 0, 0, p, p, 0], y=[0, 0, l, l, 0, 0, l, l], z=[0, 0, 0, 0, t, t, t, t], i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2], j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3], k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6], color='cyan', opacity=0.6))
    else:
        z = np.linspace(0, pj, 30); th = np.linspace(0, 2*np.pi, 30); tg, zg = np.meshgrid(th, z); x = (d/2)*np.cos(tg); y = (d/2)*np.sin(tg)
        fig.add_trace(go.Surface(x=x, y=y, z=zg, showscale=False))
    
    fig.update_layout(margin=dict(l=0,r=0,b=0,t=0), height=350, scene=dict(xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False)))
    st.plotly_chart(fig, use_container_width=True)
