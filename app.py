import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import google.generativeai as genai
from PIL import Image
import json

# --- 1. SETTING HALAMAN ---
st.set_page_config(page_title="Estimator Pro V2", layout="wide", page_icon="📸")

st.markdown("""
<style>
    .stMetric {background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 5px; padding: 10px;}
    .stButton>button {width: 100%; border-radius: 5px; font-weight: bold;}
</style>
""", unsafe_allow_html=True)

st.title("🏭 Manufacturing Cost & Scan AI")

# --- 2. DATA (HARDCODED) ---
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

# --- 3. SIDEBAR (WAJIB ISI API KEY) ---
with st.sidebar:
    st.header("⚙️ Pengaturan")
    # API KEY SAYA TARUH PALING ATAS BIAR KELIHATAN
    api_key = st.text_input("🔑 Google API Key", type="password", help="Wajib diisi agar AI jalan")
    if not api_key:
        st.warning("⚠️ Masukkan API Key dulu!")
    
    st.divider()
    mat_pilih = st.selectbox("Material", df_mat['Material'])
    mesin_pilih = st.selectbox("Mesin", df_mac['Mesin'])
    jam = st.number_input("Jam Kerja", 1.0, 100.0, 1.0)
    margin = st.slider("Margin %", 10, 50, 30)

# --- 4. LOGIC STATE ---
if 'dim' not in st.session_state:
    st.session_state['dim'] = {'p': 100.0, 'l': 50.0, 't': 20.0, 'd': 50.0}

# --- 5. LAYOUT UTAMA ---
col_kiri, col_kanan = st.columns([1, 1.2])

with col_kiri:
    st.subheader("1. Ambil Gambar Teknik")
    
    # PILIHAN: UPLOAD FILE atau KAMERA LANGSUNG
    tab_upload, tab_cam = st.tabs(["📂 Upload File", "📸 Kamera Langsung"])
    
    img_file = None
    
    with tab_upload:
        uploaded = st.file_uploader("Pilih File", type=["jpg", "png", "jpeg"])
        if uploaded: img_file = uploaded
            
    with tab_cam:
        cam_pic = st.camera_input("Ambil Foto Blueprint")
        if cam_pic: img_file = cam_pic

    # LOGIKA SCAN (MUNCUL KALAU ADA GAMBAR)
    if img_file:
        st.success("Gambar terdeteksi!")
        # Tampilkan Tombol Scan HANYA jika API Key ada
        if api_key:
            if st.button("✨ KLIK UNTUK SCAN UKURAN (AI)", type="primary"):
                try:
                    with st.spinner("AI sedang melihat gambar..."):
                        genai.configure(api_key=api_key)
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        img = Image.open(img_file)
                        prompt = "Extract dimensions. Return JSON: {'shape': 'block', 'length': 100, 'width': 50, 'thickness': 20, 'diameter': 0}"
                        res = model.generate_content([prompt, img])
                        data = json.loads(res.text.replace("```json", "").replace("```", ""))
                        
                        # Update Data
                        st.session_state['dim']['p'] = float(data.get('length', 100))
                        st.session_state['dim']['l'] = float(data.get('width', 50))
                        st.session_state['dim']['t'] = float(data.get('thickness', 20))
                        st.session_state['dim']['d'] = float(data.get('diameter', 50))
                        st.toast("Scan Berhasil!", icon="✅")
                        st.rerun()
                except Exception as e:
                    st.error(f"Gagal Scan: {e}")
        else:
            st.error("🚫 Tombol Scan terkunci. Masukkan Google API Key di Sidebar sebelah kiri.")

    # INPUT MANUAL (HASIL SCAN MASUK SINI)
    st.divider()
    mode = st.radio("Bentuk:", ["Kotak", "Silinder"], horizontal=True)
    if mode == "Kotak":
        p = st.number_input("Panjang", value=st.session_state['dim']['p'])
        l = st.number_input("Lebar", value=st.session_state['dim']['l'])
        t = st.number_input("Tebal", value=st.session_state['dim']['t'])
        vol = (p*l*t)/1000
    else:
        d = st.number_input("Diameter", value=st.session_state['dim']['d'])
        p = st.number_input("Panjang", value=st.session_state['dim']['p'])
        vol = (np.pi*((d/2)**2)*p)/1000

with col_kanan:
    st.subheader("2. Hasil Estimasi")
    
    # Hitung
    row_mat = df_mat[df_mat['Material'] == mat_pilih].iloc[0]
    row_mac = df_mac[df_mac['Mesin'] == mesin_pilih].iloc[0]
    
    berat = (vol * row_mat['Density']) / 1000
    biaya = (berat * row_mat['Price']) + (jam * row_mac['Rate'] * row_mac['Hardness']) + row_mac['Setup']
    harga = biaya + (biaya * margin/100)
    
    # Visualisasi
    fig = go.Figure()
    if mode == "Kotak":
        fig.add_trace(go.Mesh3d(x=[0,p,p,0,0,p,p,0], y=[0,0,l,l,0,0,l,l], z=[0,0,0,0,t,t,t,t], color='cyan', opacity=0.6))
    else:
        z=np.linspace(0,p,20); th=np.linspace(0,6.28,20); tg,zg=np.meshgrid(th,z); x=(d/2)*np.cos(tg); y=(d/2)*np.sin(tg)
        fig.add_trace(go.Surface(x=x, y=y, z=zg, showscale=False))
    
    fig.update_layout(height=300, margin=dict(l=0,r=0,t=0,b=0), scene=dict(aspectmode='data'))
    st.plotly_chart(fig, use_container_width=True)
    
    # Card Hasil
    c1, c2 = st.columns(2)
    c1.metric("Berat Material", f"{berat:.2f} kg")
    c1.metric("Modal (HPP)", f"Rp {biaya:,.0f}")
    st.success(f"### HARGA JUAL: Rp {harga:,.0f}")
