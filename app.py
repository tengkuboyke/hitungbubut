import streamlit as st
import plotly.graph_objects as go
import numpy as np

# --- 1. SETTING HALAMAN ---
st.set_page_config(page_title="Pro Shop Estimator V3", layout="wide")
st.title("🏭 Pro Manufacturing Cost Estimator")
st.markdown("Hitung: Material + Machining + Drilling/Tapping + Precision/Grinding")
st.markdown("---")

# --- 2. SIDEBAR: RAW MATERIAL ---
st.sidebar.header("1. Raw Material")

tipe_proses = st.sidebar.radio(
    "Jenis Pekerjaan:",
    ["Milling / CNC (Block)", "Turning / Bubut (Round Bar)"]
)

if tipe_proses == "Milling / CNC (Block)":
    st.sidebar.caption("Dimensi Balok")
    p = st.sidebar.number_input("Panjang (mm)", 0, 2000, 100)
    l = st.sidebar.number_input("Lebar (mm)", 0, 1000, 50)
    t = st.sidebar.number_input("Tebal (mm)", 0, 500, 20)
    vol_cm3 = (p * l * t) / 1000
else:
    st.sidebar.caption("Dimensi As")
    d = st.sidebar.number_input("Diameter (mm)", 0, 500, 50)
    pj = st.sidebar.number_input("Panjang (mm)", 0, 2000, 100)
    r = d / 2
    vol_cm3 = (np.pi * (r**2) * pj) / 1000

material = st.sidebar.selectbox(
    "Jenis Material",
    ("Mild Steel", "Aluminium 6061", "Stainless 304", "Brass", "Plastic (Nylon/POM)")
)

# Database Berat Jenis
if "Aluminium" in material: bj = 2.7
elif "Stainless" in material: bj = 7.93
elif "Brass" in material: bj = 8.73
elif "Plastic" in material: bj = 1.2
else: bj = 7.85

# --- 3. SIDEBAR: FITUR (DRILL, TAP, ETC) ---
st.sidebar.markdown("---")
st.sidebar.header("2. Fitur & Kerumitan")

with st.sidebar.expander("🛠️ Detail Lubang & Tap", expanded=True):
    col_drill, col_tap = st.columns(2)
    with col_drill:
        jml_lubang = st.number_input("Jml Bor", 0, 100, 0, help="Jumlah lubang biasa")
    with col_tap:
        jml_tap = st.number_input("Jml Tap", 0, 100, 0, help="Jumlah lubang berulir")

with st.sidebar.expander("📏 Toleransi & Finishing", expanded=True):
    toleransi = st.selectbox(
        "Level Toleransi",
        ("Standard (0.1 mm)", "Presisi (0.05 mm)", "High Precision (0.01 mm / H7)")
    )
    
    perlu_grinding = st.checkbox("Perlu Surface Grinding?")
    if perlu_grinding:
        luas_grinding = st.number_input("Estimasi Luas Grinding (cm2)", 0, 10000, 100)
    else:
        luas_grinding = 0

# --- 4. SIDEBAR: TARIF (COSTING) ---
st.sidebar.markdown("---")
st.sidebar.header("3. Parameter Biaya")
# Biaya default (bisa diubah user)
harga_mat_per_kg = st.sidebar.number_input("Harga Material (Rp/kg)", value=20000, step=1000)
tarif_mesin = st.sidebar.number_input("Tarif CNC/Bubut (Rp/Jam)", value=100000, step=10000)
tarif_grinding = 150000 # Tarif per jam grinding (flat asumsi)

# Estimasi Waktu Dasar (User input manual estimasi kasar)
jam_dasar = st.sidebar.number_input("Estimasi Waktu Roughing (Jam)", 0.5, 50.0, 1.0)
margin_persen = st.sidebar.slider("Profit Margin (%)", 10, 100, 30)

# --- 5. OTAK KALKULATOR (LOGIC) ---

# A. Biaya Material
berat_kg = (vol_cm3 * bj) / 1000
cost_material = berat_kg * harga_mat_per_kg

# B. Biaya Fitur (Drill & Tap)
# Asumsi: 1 Lubang drill = 5 menit, 1 Tap = 10 menit
biaya_per_lubang = (5/60) * tarif_mesin
biaya_per_tap = (10/60) * tarif_mesin
cost_feature = (jml_lubang * biaya_per_lubang) + (jml_tap * biaya_per_tap)

# C. Faktor Kesulitan (Toleransi)
if "Standard" in toleransi:
    factor = 1.0
elif "Presisi" in toleransi:
    factor = 1.3 # Harga mesin naik 30% karena harus pelan
else: # High Precision
    factor = 1.8 # Harga mesin naik 80%

cost_machining_base = jam_dasar * tarif_mesin
cost_machining_total = cost_machining_base * factor

# D. Biaya Grinding
# Asumsi: Grinding butuh 20 menit per 100 cm2
if perlu_grinding:
    jam_grinding = (luas_grinding / 100) * (20/60)
    cost_grinding = jam_grinding * tarif_grinding
    # Minimum charge grinding
    if cost_grinding < 50000: cost_grinding = 50000
else:
    cost_grinding = 0

# TOTAL HPP
hpp = cost_material + cost_machining_total + cost_feature + cost_grinding
harga_jual = hpp + (hpp * (margin_persen/100))

# --- 6. TAMPILAN DASHBOARD ---
col1, col2 = st.columns([1, 1.5])

with col1:
    st.subheader("💰 Breakdown Harga")
    
    # Kita buat tabel rincian biar terlihat profesional
    st.write("Rincian Biaya Produksi:")
    
    data_biaya = {
        "Komponen": ["Material", "Machining (CNC/Lathe)", "Fitur (Drill/Tap)", "Finishing (Grinding)"],
        "Biaya (Rp)": [f"{cost_material:,.0f}", f"{cost_machining_total:,.0f}", f"{cost_feature:,.0f}", f"{cost_grinding:,.0f}"]
    }
    st.table(data_biaya)
    
    st.metric("Total HPP (Modal)", f"Rp {hpp:,.0f}")
    
    st.divider()
    st.success(f"HARGA PENAWARAN: Rp {harga_jual:,.0f}")
    st.caption(f"Spek: {toleransi} | Berat: {berat_kg:.2f} kg")

with col2:
    st.subheader("🧊 Visualisasi Material")
    
    fig = go.Figure()

    if tipe_proses == "Milling / CNC (Block)":
        # Gambar Kubus Transparan
        fig.add_trace(go.Mesh3d(
            x=[0, p, p, 0, 0, p, p, 0],
            y=[0, 0, l, l, 0, 0, l, l],
            z=[0, 0, 0, 0, t, t, t, t],
            i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2],
            j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3],
            k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
            color='gray', opacity=0.5, name='Raw Material'
        ))
        
        # Visualisasi Simulasi Lubang (Titik Merah) - Gimmick Visual
        if jml_lubang > 0:
            # Taruh titik-titik random di atas permukaan sebagai simbol lubang
            x_holes = np.random.uniform(10, p-10, jml_lubang)
            y_holes = np.random.uniform(10, l-10, jml_lubang)
            z_holes = [t] * jml_lubang
            
            fig.add_trace(go.Scatter3d(
                x=x_holes, y=y_holes, z=z_holes,
                mode='markers',
                marker=dict(size=5, color='red', symbol='circle'),
                name='Drilling Points'
            ))

    else:
        # Gambar Silinder
        z_cyl = np.linspace(0, pj, 50)
        theta = np.linspace(0, 2*np.pi, 50)
        theta_grid, z_grid = np.meshgrid(theta, z_cyl)
        x_cyl = (d/2) * np.cos(theta_grid)
        y_cyl = (d/2) * np.sin(theta_grid)
        
        fig.add_trace(go.Surface(x=x_cyl, y=y_cyl, z=z_grid, colorscale='Greys', opacity=0.8, showscale=False))

    fig.update_layout(
        scene=dict(xaxis_title='X', yaxis_title='Y', zaxis_title='Z', aspectmode='data'),
        margin=dict(l=0, r=0, b=0, t=0)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    st.info("ℹ️ Titik merah pada visualisasi adalah ilustrasi posisi lubang.")
