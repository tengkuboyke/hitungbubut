import streamlit as st
import plotly.graph_objects as go
import numpy as np

# --- 1. KONFIGURASI HALAMAN WEB ---
st.set_page_config(page_title="Smart Quoting AI", layout="wide")

# Judul Besar di Tengah
st.title("🏭 Smart Manufacturing Quoting System")
st.markdown("---") # Garis pemisah

# --- 2. SIDEBAR (MENU KIRI) ---
# Di web, biasanya input ada di sebelah kiri
st.sidebar.header("⚙️ Input Parameter")

# Input User (Pengganti input() biasa)
panjang = st.sidebar.number_input("Panjang (mm)", value=100, step=10)
lebar = st.sidebar.number_input("Lebar (mm)", value=50, step=10)
tebal = st.sidebar.number_input("Tebal (mm)", value=20, step=5)

material = st.sidebar.selectbox(
    "Pilih Material",
    ("Mild Steel", "Aluminium 6061", "Stainless Steel 304")
)

# Input Biaya (Bisa disembunyikan nanti)
st.sidebar.subheader("💰 Cost Settings")
margin = st.sidebar.slider("Profit Margin (%)", 10, 100, 30)

# --- 3. LOGIKA HITUNGAN (ENGINEERING BRAIN) ---
# Menghitung Volume & Berat
vol_cm3 = (panjang/10) * (lebar/10) * (tebal/10)

# Database Material
if material == "Mild Steel":
    bj = 7.85
    harga_per_kg = 15000
elif material == "Aluminium 6061":
    bj = 2.70
    harga_per_kg = 45000
else: # Stainless
    bj = 7.93
    harga_per_kg = 80000

berat_kg = (vol_cm3 * bj) / 1000
biaya_mat = berat_kg * harga_per_kg
# Asumsi biaya mesin sederhana
biaya_prod = berat_kg * 25000 

hpp = biaya_mat + biaya_prod
harga_jual = hpp + (hpp * (margin/100))

# --- 4. TAMPILAN UTAMA (DASHBOARD) ---

# Membuat 2 Kolom: Kiri (Angka), Kanan (Visual 3D)
col1, col2 = st.columns([1, 2]) # Kolom kanan lebih lebar

with col1:
    st.subheader("📊 Hasil Analisa")
    
    # Menampilkan angka dengan gaya Dashboard
    st.metric(label="Estimasi Berat", value=f"{berat_kg:.2f} kg")
    st.metric(label="HPP (Modal)", value=f"Rp {hpp:,.0f}")
    
    st.divider() # Garis
    
    # Harga Jual dibuat besar dan hijau
    st.markdown("### Rekomendasi Harga:")
    st.success(f"Rp {harga_jual:,.0f}")

with col2:
    st.subheader("🧊 Visualisasi 3D Preview")
    
    # --- LOGIKA 3D PLOTLY (Sama seperti sebelumnya) ---
    # Kita buat kubus sesuai input user
    x, y, z = np.indices((2, 2, 2))
    x = x.flatten() * panjang
    y = y.flatten() * lebar
    z = z.flatten() * tebal
    
    fig = go.Figure(data=go.Mesh3d(
        x=x, y=y, z=z,
        alphahull=0,
        opacity=0.8,
        color='cyan',
        lighting=dict(ambient=0.5, diffuse=1)
    ))
    
    fig.update_layout(
        scene=dict(
            xaxis=dict(visible=False), # Hilangkan garis axis biar bersih
            yaxis=dict(visible=False),
            zaxis=dict(visible=False),
        ),
        margin=dict(r=0, l=0, b=0, t=0)
    )
    
    # Menampilkan 3D di Web
    st.plotly_chart(fig, use_container_width=True)

# --- 5. BUTTON ACTION ---
if st.button("Generate PDF Quotation"):
    st.balloons() # Efek animasi balon keluar
    st.info("Fitur cetak PDF akan hadir di versi berikutnya!")
