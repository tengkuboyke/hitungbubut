import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import google.generativeai as genai
from PIL import Image
import json

# --- 1. SETTING HALAMAN ---
st.set_page_config(page_title="Estimator Pro", layout="wide", page_icon="⚙️")

# CSS Sederhana untuk mempercantik
st.markdown("""
<style>
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 10px;
        border: 1px solid #dce0e6;
    }
</style>
""", unsafe_allow_html=True)

st.title("🏭 Manufacturing Cost Estimator")

# --- 2. DATA (HARDCODED BIAR CEPAT) ---
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

# --- 3. SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Pengaturan")
    api_key = st.text_input("Google API Key", type="password")
    
    st.divider()
    mat_pilih = st.selectbox("Material", df_mat['Material'])
    mesin_pilih = st.selectbox("Mesin", df_mac['Mesin'])
    
    st.divider()
    jam = st.number_input("Jam Kerja", 1.0, 100.0, 1.0)
    margin = st.slider("Margin %", 10, 50, 30)

# --- 4. LOGIC ---
if 'dim' not in st.session_state:
    st.session_state['dim'] = {'p': 100.0, 'l': 50.0, 't': 20.0, 'd': 50.0}

# --- 5. LAYOUT ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Input Gambar / Dimensi")
    uploaded = st.file_uploader("Upload Gambar Teknik", type=["jpg", "png"])
    
    if uploaded and api_key:
        st.image(uploaded, caption="Preview", width=300)
        if st.button("✨ Scan Dimensi (AI)"):
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-1.5-flash')
                img = Image.open(uploaded)
                prompt = "Extract dimensions to JSON: {'shape': 'block', 'length': 100, 'width': 50, 'thickness': 20, 'diameter': 0}"
                res = model.generate_content([prompt, img])
                data = json.loads(res.text.replace("```json", "").replace("```", ""))
                
                st.session_state['dim']['p'] = float(data.get('length', 100))
                st.session_state['dim']['l'] = float(data.get('width', 50))
                st.session_state['dim']['t'] = float(data.get('thickness', 20))
                st.session_state['dim']['d'] = float(data.get('diameter', 50))
                st.rerun()
            except:
                st.error("Gagal Scan")

    # Input Manual (Tab style)
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

with col2:
    st.subheader("2. Hasil & Visualisasi")
    
    # Kalkulasi
    row_mat = df_mat[df_mat['Material'] == mat_pilih].iloc[0]
    row_mac = df_mac[df_mac['Mesin'] == mesin_pilih].iloc[0]
    
    berat = (vol * row_mat['Density']) / 1000
    biaya = (berat * row_mat['Price']) + (jam * row_mac['Rate'] * row_mat['Hardness']) + row_mac['Setup']
    harga = biaya + (biaya * margin/100)
    
    # Visualisasi Simple
    fig = go.Figure()
    if mode == "Kotak":
        fig.add_trace(go.Mesh3d(x=[0,p,p,0,0,p,p,0], y=[0,0,l,l,0,0,l,l], z=[0,0,0,0,t,t,t,t], color='cyan', opacity=0.5))
    else:
        z=np.linspace(0,p,20); th=np.linspace(0,6.28,20); tg,zg=np.meshgrid(th,z); x=(d/2)*np.cos(tg); y=(d/2)*np.sin(tg)
        fig.add_trace(go.Surface(x=x, y=y, z=zg, showscale=False))
    
    fig.update_layout(height=250, margin=dict(l=0,r=0,t=0,b=0))
    st.plotly_chart(fig, use_container_width=True)
    
    # CARD HASIL
    c1, c2 = st.columns(2)
    c1.metric("Berat", f"{berat:.2f} kg")
    c1.metric("HPP (Modal)", f"Rp {biaya:,.0f}")
    c2.metric("HARGA JUAL", f"Rp {harga:,.0f}", delta="Final Offer")
