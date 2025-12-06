import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import google.generativeai as genai
from PIL import Image
import json

# --- 1. SETTING HALAMAN (MOBILE FRIENDLY) ---
# Ubah layout="wide" jadi "centered" biar enak di HP
st.set_page_config(page_title="Estimator Mobile", layout="centered", page_icon="📱")

# CSS Khusus HP (Memperbesar tombol & font)
st.markdown("""
<style>
    /* Supaya tombol lebih gampang dipencet jari jempol */
    .stButton>button {
        height: 3em;
        width: 100%;
        border-radius: 10px;
        font-size: 18px;
        font-weight: bold;
    }
    /* Metric Card biar tidak terlalu mepet */
    div[data-testid="stMetric"] {
        background-color: #f8f9fa;
        border: 1px solid #ddd;
        padding: 10px;
        border-radius: 8px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

st.title("🏭 Pocket Estimator")

# --- 2. DATA ---
def get_data():
    mat = pd.DataFrame({
        'Material': ['Mild Steel', 'Aluminium 6061', 'Stainless 304', 'Brass', 'Nylon'],
        'Density': [7.85, 2.70, 7.93, 8.73, 1.15],
        'Price': [18000, 65000, 95000, 125000, 85000],
        'Hardness': [1.0, 0.6, 1.5, 0.8, 0.4]
    })
    mac = pd.DataFrame({
        'Mesin': ['Manual Lathe', 'Manual Milling', 'CNC Turning', 'CNC Milling'],
        'Rate': [60000, 75000, 120000, 150000],
        'Setup': [25000, 35000, 150000, 200000]
    })
    return mat, mac

df_mat, df_mac = get_data()

# --- 3. SETTING DI ATAS (BUKAN DI SIDEBAR) ---
# Supaya user HP langsung lihat, tidak perlu cari menu tersembunyi
with st.expander("⚙️ PENGATURAN & API KEY (Klik Disini)", expanded=True):
    api_key = st.text_input("🔑 Google API Key", type="password")
    
    c1, c2 = st.columns(2)
    with c1:
        mat_pilih = st.selectbox("Material", df_mat['Material'])
        jam = st.number_input("Jam Kerja", 1.0, 100.0, 1.0)
    with c2:
        mesin_pilih = st.selectbox("Mesin", df_mac['Mesin'])
        margin = st.number_input("Margin %", 10, 100, 30)

# --- 4. LOGIC STATE ---
if 'dim' not in st.session_state:
    st.session_state['dim'] = {'p': 100.0, 'l': 50.0, 't': 20.0, 'd': 50.0}

# --- 5. AREA INPUT KAMERA ---
st.divider()
st.subheader("📸 Ambil Foto / Upload")

# Pilihan Tab yang lebih simpel
tab_cam, tab_file = st.tabs(["Kamera HP", "Upload File"])
img_file = None

with tab_cam:
    cam_pic = st.camera_input("Jepret Gambar Teknik")
    if cam_pic: img_file = cam_pic

with tab_file:
    uploaded = st.file_uploader("Pilih dari Galeri", type=["jpg", "png"])
    if uploaded: img_file = uploaded

# TOMBOL SCAN (Hanya muncul jika ada foto)
if img_file:
    st.info("✅ Foto siap diproses")
    if api_key:
        if st.button("✨ SCAN UKURAN SEKARANG", type="primary"):
            try:
                with st.spinner("Mata AI sedang membaca..."):
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    img = Image.open(img_file)
                    prompt = "Extract dimensions JSON: {'shape': 'block', 'length': 100, 'width': 50, 'thickness': 20, 'diameter': 0}"
                    res = model.generate_content([prompt, img])
                    data = json.loads(res.text.replace("```json", "").replace("```", ""))
                    
                    st.session_state['dim']['p'] = float(data.get('length', 100))
                    st.session_state['dim']['l'] = float(data.get('width', 50))
                    st.session_state['dim']['t'] = float(data.get('thickness', 20))
                    st.session_state['dim']['d'] = float(data.get('diameter', 50))
                    st.rerun()
            except Exception as e:
                st.error("Gagal Scan. Coba foto ulang yang jelas.")
    else:
        st.error("⚠️ Masukkan API Key di menu Pengaturan di atas!")

# --- 6. HASIL & VISUALISASI ---
st.divider()
st.subheader("📝 Hasil & Edit Manual")

# Mode Edit yang Rapi
mode = st.radio("Bentuk:", ["Kotak", "Silinder"], horizontal=True)

col_in1, col_in2, col_in3 = st.columns(3)
if mode == "Kotak":
    with col_in1: p = st.number_input("Panjang", value=st.session_state['dim']['p'])
    with col_in2: l = st.number_input("Lebar", value=st.session_state['dim']['l'])
    with col_in3: t = st.number_input("Tebal", value=st.session_state['dim']['t'])
    vol = (p*l*t)/1000
else:
    with col_in1: d = st.number_input("Diameter", value=st.session_state['dim']['d'])
    with col_in2: p = st.number_input("Panjang", value=st.session_state['dim']['p'])
    vol = (np.pi*((d/2)**2)*p)/1000

# Hitung
row_mat = df_mat[df_mat['Material'] == mat_pilih].iloc[0]
row_mac = df_mac[df_mac['Mesin'] == mesin_pilih].iloc[0]
berat = (vol * row_mat['Density']) / 1000
biaya = (berat * row_mat['Price']) + (jam * row_mac['Rate'] * row_mat['Hardness']) + row_mac['Setup']
harga = biaya + (biaya * margin/100)

# Card Hasil (Full Width di HP)
st.success(f"### 🏷️ PENAWARAN: Rp {harga:,.0f}")
c1, c2 = st.columns(2)
c1.metric("Berat", f"{berat:.2f} kg")
c1.metric("HPP", f"Rp {biaya:,.0f}")

# Visualisasi 3D (Ditaruh di bawah biar tidak menuhin layar HP di awal)
with st.expander("🧊 Lihat Visualisasi 3D"):
    fig = go.Figure()
    if mode == "Kotak":
        fig.add_trace(go.Mesh3d(x=[0,p,p,0,0,p,p,0], y=[0,0,l,l,0,0,l,l], z=[0,0,0,0,t,t,t,t], color='cyan', opacity=0.6))
    else:
        z=np.linspace(0,p,20); th=np.linspace(0,6.28,20); tg,zg=np.meshgrid(th,z); x=(d/2)*np.cos(tg); y=(d/2)*np.sin(tg)
        fig.add_trace(go.Surface(x=x, y=y, z=zg, showscale=False))
    
    fig.update_layout(height=250, margin=dict(l=0,r=0,t=0,b=0), scene=dict(aspectmode='data'))
    st.plotly_chart(fig, use_container_width=True)
