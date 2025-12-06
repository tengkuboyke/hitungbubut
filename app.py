import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import google.generativeai as genai
from PIL import Image
import json

# --- 1. SETTING HALAMAN ---
st.set_page_config(page_title="Pro Shop Estimator Final", layout="wide")
st.title("🏭 Smart Manufacturing Estimator (Final)")

# --- 2. DATABASE MANUAL (HARDCODED) ---
def load_data_internal():
    data_mat = {
        'Material': ['Mild Steel (SS400)', 'Aluminium 6061', 'Stainless Steel 304', 'Brass (Kuningan)', 'Bronze (Perunggu)', 'Nylon (Plastic)', 'Teflon (PTFE)', 'Tool Steel (SKD11)'],
        'Density': [7.85, 2.70, 7.93, 8.73, 8.80, 1.15, 2.20, 7.80],
        'Price_Kg': [18000, 65000, 95000, 125000, 180000, 85000, 150000, 250000],
        'Hardness_Factor': [1.0, 0.6, 1.5, 0.8, 0.9, 0.4, 0.5, 1.8]
    }
    data_mac = {
        'Machine_Name': ['Manual Lathe (Bubut)', 'Manual Milling (Frais)', 'CNC Turning 2-Axis', 'CNC Milling 3-Axis', 'CNC Milling 5-Axis', 'Surface Grinding'],
        'Cost_Per_Hour': [60000, 75000, 120000, 150000, 350000, 90000],
        'Setup_Cost': [25000, 35000, 150000, 200000, 500000, 40000]
    }
    return pd.DataFrame(data_mat), pd.DataFrame(data_mac)

df_material, df_machine = load_data_internal()

# --- 3. SIDEBAR: AI SETTINGS ---
with st.sidebar.expander("🔑 AI Settings (Google Gemini)", expanded=True):
    api_key = st.text_input("Paste Google API Key", type="password")

if 'dimensi' not in st.session_state:
    st.session_state['dimensi'] = {'p': 100.0, 'l': 50.0, 't': 20.0, 'd': 50.0}
if 'scan_result' not in st.session_state:
    st.session_state['scan_result'] = ""

# --- 4. LAYOUT ATAS (UPLOAD & VISUALISASI) ---
col_kiri, col_kanan = st.columns([1, 1])

with col_kiri:
    st.subheader("1. Upload & Scan")
    uploaded_file = st.file_uploader("Upload Gambar Teknik (JPG/PNG)", type=["jpg", "png", "jpeg"])
    
    # Logic AI Scan
    if uploaded_file and api_key:
        if st.button("✨ SCAN GAMBAR SEKARANG", type="primary"):
            try:
                with st.spinner("AI sedang membaca dimensi..."):
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    img = Image.open(uploaded_file)
                    prompt = """
                    You are an expert Industrial Engineer. Look at this technical drawing.
                    Extract the main dimensions. Return ONLY a JSON string: {"shape": "block", "length": 100, "width": 50, "thickness": 20, "diameter": 0}
                    If cylinder, fill diameter and length. If block, fill length, width, thickness.
                    """
                    response = model.generate_content([prompt, img])
                    text_res = response.text.replace("```json", "").replace("```", "").strip()
                    data_json = json.loads(text_res)
                    
                    st.session_state['dimensi']['p'] = float(data_json.get('length', 100))
                    if "block" in data_json.get('shape', 'block').lower():
                        st.session_state['dimensi']['l'] = float(data_json.get('width', 50))
                        st.session_state['dimensi']['t'] = float(data_json.get('thickness', 20))
                    else:
                        st.session_state['dimensi']['d'] = float(data_json.get('diameter', 50))
                    
                    st.session_state['scan_result'] = "✅ Scan Berhasil!"
                    st.rerun()
            except Exception as e:
                st.error(f"Gagal scan: {e}")
    
    # Tampilkan Preview Foto yang diupload
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Gambar dari User", use_container_width=True)
        if st.session_state['scan_result']:
            st.success(st.session_state['scan_result'])

with col_kanan:
    st.subheader("2. Visualisasi 3D (Interactive)")
    
    # Input Data Manual / Hasil Scan
    tipe_benda = st.radio("Bentuk:", ["Block (Kotak)", "Cylinder (As/Pipa)"], horizontal=True)
    
    if tipe_benda == "Block (Kotak)":
        p = st.number_input("Panjang (mm)", 0.0, 5000.0, st.session_state['dimensi']['p'])
        l = st.number_input("Lebar (mm)", 0.0, 2000.0, st.session_state['dimensi']['l'])
        t = st.number_input("Tebal (mm)", 0.0, 1000.0, st.session_state['dimensi']['t'])
        vol_cm3 = (p * l * t) / 1000
        
        # VISUALISASI KUBUS (YANG HILANG TADI)
        fig = go.Figure(data=go.Mesh3d(
            x=[0, p, p, 0, 0, p, p, 0], y=[0, 0, l, l, 0, 0, l, l], z=[0, 0, 0, 0, t, t, t, t],
            i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2], j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3], k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
            color='cyan', opacity=0.6, name='Material'
        ))
    else:
        d = st.number_input("Diameter (mm)", 0.0, 1000.0, st.session_state['dimensi']['d'])
        p = st.number_input("Panjang (mm)", 0.0, 5000.0, st.session_state['dimensi']['p'])
        r = d / 2
        vol_cm3 = (np.pi * (r**2) * p) / 1000
        
        # VISUALISASI SILINDER (YANG HILANG TADI)
        z = np.linspace(0, p, 30); th = np.linspace(0, 2*np.pi, 30)
        tg, zg = np.meshgrid(th, z); x = (d/2)*np.cos(tg); y = (d/2)*np.sin(tg)
        fig = go.Figure(data=go.Surface(x=x, y=y, z=zg, showscale=False, colorscale='Viridis'))

    fig.update_layout(margin=dict(l=0,r=0,b=0,t=0), height=300, scene=dict(aspectmode='data'))
    st.plotly_chart(fig, use_container_width=True)

# --- 5. LOGIKA HARGA & HASIL ---
st.divider()
st.subheader("3. Estimasi Biaya")

c1, c2, c3 = st.columns(3)
with c1:
    pilihan_material = st.selectbox("Pilih Material", df_material['Material'].unique())
    pilihan_mesin = st.selectbox("Pilih Mesin", df_machine['Machine_Name'].unique())

with c2:
    jam = st.number_input("Estimasi Jam Kerja", 0.1, 100.0, 1.0, step=0.5)
    margin = st.slider("Profit Margin (%)", 10, 100, 30)

# Kalkulasi
mat_data = df_material[df_material['Material'] == pilihan_material].iloc[0]
mac_data = df_machine[df_machine['Machine_Name'] == pilihan_mesin].iloc[0]

berat = (vol_cm3 * mat_data['Density']) / 1000
cost_mat = berat * mat_data['Price_Kg']
cost_mac = (jam * mac_data['Cost_Per_Hour'] * mat_data['Hardness_Factor']) + mac_data['Setup_Cost']
hpp = cost_mat + cost_mac
harga = hpp + (hpp * (margin/100))

with c3:
    st.markdown("### 💰 Total Penawaran")
    st.metric("Berat Material", f"{berat:.2f} kg")
    st.metric("Modal (HPP)", f"Rp {hpp:,.0f}")
    st.success(f"HARGA JUAL: Rp {harga:,.0f}")
