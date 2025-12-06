import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import google.generativeai as genai
from PIL import Image
import json

# --- 1. SETTING HALAMAN ---
st.set_page_config(page_title="Pro Shop Estimator", layout="wide")
st.title("🏭 Smart Manufacturing Estimator (All-in-One)")

# --- 2. DATABASE MANUAL (HARDCODED) ---
# Kita tulis datanya di sini supaya tidak perlu baca file luar lagi.
# Jauh lebih stabil dan anti-error.

def load_data_internal():
    # Data Material
    data_mat = {
        'Material': [
            'Mild Steel (SS400)', 'Aluminium 6061', 'Stainless Steel 304', 
            'Brass (Kuningan)', 'Bronze (Perunggu)', 'Nylon (Plastic)', 
            'Teflon (PTFE)', 'Tool Steel (SKD11)'
        ],
        'Density': [7.85, 2.70, 7.93, 8.73, 8.80, 1.15, 2.20, 7.80],
        'Price_Kg': [18000, 65000, 95000, 125000, 180000, 85000, 150000, 250000],
        'Hardness_Factor': [1.0, 0.6, 1.5, 0.8, 0.9, 0.4, 0.5, 1.8]
    }
    
    # Data Mesin
    data_mac = {
        'Machine_Name': [
            'Manual Lathe (Bubut)', 'Manual Milling (Frais)', 
            'CNC Turning 2-Axis', 'CNC Milling 3-Axis', 
            'CNC Milling 5-Axis', 'Surface Grinding'
        ],
        'Cost_Per_Hour': [60000, 75000, 120000, 150000, 350000, 90000],
        'Setup_Cost': [25000, 35000, 150000, 200000, 500000, 40000]
    }
    
    return pd.DataFrame(data_mat), pd.DataFrame(data_mac)

df_material, df_machine = load_data_internal()

# --- 3. SIDEBAR: KONEKSI OTAK AI ---
with st.sidebar.expander("🔑 AI Settings (Google Gemini)", expanded=False):
    api_key = st.text_input("Paste Google API Key", type="password")

# Inisialisasi Session State
if 'dimensi' not in st.session_state:
    st.session_state['dimensi'] = {'p': 100.0, 'l': 50.0, 't': 20.0, 'd': 50.0}
if 'scan_result' not in st.session_state:
    st.session_state['scan_result'] = "Belum ada scan."

# --- 4. AREA UPLOAD & SCANNING ---
col_upload, col_preview = st.columns([1, 1.5])

with col_upload:
    st.subheader("1. Upload Gambar Teknik")
    uploaded_file = st.file_uploader("Format: JPG, PNG", type=["jpg", "png", "jpeg"])
    
    st.markdown("---")
    st.subheader("2. Verifikasi Data")
    
    tipe_benda = st.radio("Bentuk Benda:", ["Block (Kotak)", "Cylinder (As/Pipa)"])
    
    if tipe_benda == "Block (Kotak)":
        p = st.number_input("Panjang (mm)", 0.0, 5000.0, st.session_state['dimensi']['p'])
        l = st.number_input("Lebar (mm)", 0.0, 2000.0, st.session_state['dimensi']['l'])
        t = st.number_input("Tebal (mm)", 0.0, 1000.0, st.session_state['dimensi']['t'])
        vol_cm3 = (p * l * t) / 1000
    else:
        d = st.number_input("Diameter (mm)", 0.0, 1000.0, st.session_state['dimensi']['d'])
        p = st.number_input("Panjang (mm)", 0.0, 5000.0, st.session_state['dimensi']['p'])
        r = d / 2
        vol_cm3 = (np.pi * (r**2) * p) / 1000

    if uploaded_file and api_key:
        if st.button("✨ SCAN GAMBAR DENGAN AI", type="primary"):
            try:
                with st.spinner("Sedang melihat gambar..."):
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    img = Image.open(uploaded_file)
                    
                    prompt = """
                    You are an expert Industrial Engineer. Look at this technical drawing.
                    Extract the main dimensions.
                    Return ONLY a JSON string: {"shape": "block", "length": 100, "width": 50, "thickness": 20, "diameter": 0}
                    If cylinder, fill diameter and length. If block, fill length, width, thickness.
                    """
                    response = model.generate_content([prompt, img])
                    text_res = response.text.replace("```json", "").replace("```", "").strip()
                    data_json = json.loads(text_res)
                    
                    # Update State
                    st.session_state['dimensi']['p'] = float(data_json.get('length', p))
                    if "block" in data_json.get('shape', 'block').lower():
                        st.session_state['dimensi']['l'] = float(data_json.get('width', l))
                        st.session_state['dimensi']['t'] = float(data_json.get('thickness', t))
                    else:
                        st.session_state['dimensi']['d'] = float(data_json.get('diameter', d))
                    
                    st.session_state['scan_result'] = "✅ Sukses! Data terisi otomatis."
                    st.rerun()
            except Exception as e:
                st.error(f"Gagal scan: {e}")

with col_preview:
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Preview Gambar", use_container_width=True)
        st.success(st.session_state['scan_result'])

# --- 5. LOGIKA HARGA ---
st.divider()
col1, col2, col3 = st.columns(3)

with col1:
    st.header("3. Material & Proses")
    # Dropdown ambil dari Dataframe Internal
    pilihan_material = st.selectbox("Material", df_material['Material'].unique())
    pilihan_mesin = st.selectbox("Mesin", df_machine['Machine_Name'].unique())

with col2:
    st.header("4. Estimasi")
    jam = st.number_input("Jam Kerja", 0.1, 100.0, 1.0, step=0.5)
    margin = st.slider("Margin %", 10, 100, 30)

# Kalkulasi Real-Time
mat_data = df_material[df_material['Material'] == pilihan_material].iloc[0]
mac_data = df_machine[df_machine['Machine_Name'] == pilihan_mesin].iloc[0]

berat = (vol_cm3 * mat_data['Density']) / 1000
cost_mat = berat * mat_data['Price_Kg']
cost_mac = (jam * mac_data['Cost_Per_Hour'] * mat_data['Hardness_Factor']) + mac_data['Setup_Cost']
hpp = cost_mat + cost_mac
harga = hpp + (hpp * (margin/100))

with col3:
    st.header("💰 Total Harga")
    st.metric("Berat Material", f"{berat:.2f} kg")
    st.metric("Total HPP", f"Rp {hpp:,.0f}")
    st.success(f"HARGA JUAL: Rp {harga:,.0f}")
