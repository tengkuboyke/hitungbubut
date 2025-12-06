import streamlit as st
import numpy as np
import pandas as pd
import json

# --- 1. SETTING HALAMAN (LITE MODE) ---
st.set_page_config(page_title="Estimator Lite", layout="centered", page_icon="⚡")

# CSS Sederhana & Ringan
st.markdown("""
<style>
    .stButton>button {height: 3em; width: 100%; border-radius: 8px; font-weight: bold;}
    .stMetric {background-color: #f0f2f6; border-radius: 8px; padding: 10px;}
</style>
""", unsafe_allow_html=True)

st.title("⚡ Quick Estimator")

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

# --- 3. INPUT CEPAT ---
with st.expander("⚙️ Setup Awal", expanded=True):
    api_key = st.text_input("Google API Key", type="password")
    c1, c2 = st.columns(2)
    with c1: mat_pilih = st.selectbox("Material", df_mat['Material'])
    with c2: mesin_pilih = st.selectbox("Mesin", df_mac['Mesin'])

# Logic State
if 'dim' not in st.session_state:
    st.session_state['dim'] = {'p': 100.0, 'l': 50.0, 't': 20.0, 'd': 50.0}

# --- 4. SCANNER (Lazy Import) ---
st.divider()
st.subheader("📸 Scan / Input")

# Tab Kamera/File
tab_cam, tab_file = st.tabs(["Kamera", "Upload"])
img_file = None

with tab_cam:
    cam_pic = st.camera_input("Foto")
    if cam_pic: img_file = cam_pic
with tab_file:
    uploaded = st.file_uploader("File", type=["jpg", "png"])
    if uploaded: img_file = uploaded

if img_file and api_key:
    if st.button("✨ SCAN SEKARANG", type="primary"):
        try:
            # Kita import library BERAT ini HANYA saat tombol ditekan
            # Biar loading awal aplikasi ngebut!
            import google.generativeai as genai
            from PIL import Image
            
            with st.spinner("AI Bekerja..."):
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
        except:
            st.error("Gagal Scan")

# --- 5. MANUAL EDIT & HASIL ---
st.divider()
mode = st.radio("Mode:", ["Kotak", "Silinder"], horizontal=True)

c1, c2, c3 = st.columns(3)
if mode == "Kotak":
    with c1: p = st.number_input("P", value=st.session_state['dim']['p'])
    with c2: l = st.number_input("L", value=st.session_state['dim']['l'])
    with c3: t = st.number_input("T", value=st.session_state['dim']['t'])
    vol = (p*l*t)/1000
else:
    with c1: d = st.number_input("D", value=st.session_state['dim']['d'])
    with c2: p = st.number_input("P", value=st.session_state['dim']['p'])
    vol = (np.pi*((d/2)**2)*p)/1000

# Kalkulasi
row_mat = df_mat[df_mat['Material'] == mat_pilih].iloc[0]
row_mac = df_mac[df_mac['Mesin'] == mesin_pilih].iloc[0]
berat = (vol * row_mat['Density']) / 1000
biaya = (berat * row_mat['Price']) + (1.0 * row_mac['Rate'] * row_mat['Hardness']) + row_mac['Setup']
harga = biaya * 1.3 # Margin 30% default

st.success(f"### 🏷️ Rp {harga:,.0f}")
st.caption(f"Berat: {berat:.2f} kg | HPP: Rp {biaya:,.0f}")

# FITUR 3D (OPSIONAL - DISEMBUYIKAN BIAR RINGAN)
tampil_3d = st.checkbox("Tampilkan Visualisasi 3D (Bikin berat HP)")
if tampil_3d:
    import plotly.graph_objects as go # Import di sini biar ringan di awal
    fig = go.Figure()
    if mode == "Kotak":
        fig.add_trace(go.Mesh3d(x=[0,p,p,0,0,p,p,0], y=[0,0,l,l,0,0,l,l], z=[0,0,0,0,t,t,t,t], color='cyan', opacity=0.6))
    else:
        z=np.linspace(0,p,10); th=np.linspace(0,6.28,10); tg,zg=np.meshgrid(th,z); x=(d/2)*np.cos(tg); y=(d/2)*np.sin(tg)
        fig.add_trace(go.Surface(x=x, y=y, z=zg, showscale=False))
    st.plotly_chart(fig, use_container_width=True)
