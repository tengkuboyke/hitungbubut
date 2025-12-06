import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import google.generativeai as genai
from PIL import Image
import json

# --- 1. SETTING HALAMAN ---
st.set_page_config(page_title="AI Drawing Scanner", layout="wide")
st.title("📸 AI Blueprint Scanner & Estimator")

# --- 2. DATABASE LOADER ---
@st.cache_data
def load_databases():
    try:
        url_mat = "https://raw.githubusercontent.com/tengkuboyke/hitungbubut/main/materials.csv"
        url_mac = "https://raw.githubusercontent.com/tengkuboyke/hitungbubut/main/machines.csv"
        return pd.read_csv(url_mat), pd.read_csv(url_mac)
    except:
        return None, None

df_material, df_machine = load_databases()
if df_material is None: st.stop()

# --- 3. SIDEBAR: KONEKSI OTAK AI ---
with st.sidebar.expander("🔑 AI Settings (Google Gemini)", expanded=False):
    api_key = st.text_input("Paste Google API Key", type="password", help="Dapatkan gratis di aistudio.google.com")

# Inisialisasi Session State (Agar angka bisa diedit setelah di-scan)
if 'dimensi' not in st.session_state:
    st.session_state['dimensi'] = {'p': 100.0, 'l': 50.0, 't': 20.0, 'd': 50.0}
if 'scan_result' not in st.session_state:
    st.session_state['scan_result'] = "Belum ada scan."

# --- 4. AREA UPLOAD & SCANNING ---
col_upload, col_preview = st.columns([1, 1.5])

with col_upload:
    st.subheader("1. Upload Gambar Teknik")
    uploaded_file = st.file_uploader("Format: JPG, PNG, JPEG", type=["jpg", "png", "jpeg"])
    
    # INPUT MANUAL / HASIL SCAN (Bisa diedit)
    st.markdown("---")
    st.subheader("2. Verifikasi Data")
    
    tipe_benda = st.radio("Bentuk Benda:", ["Block (Kotak)", "Cylinder (As/Pipa)"])
    
    # Form Input Dinamis
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

    # TOMBOL MAGIC AI
    if uploaded_file and api_key:
        if st.button("✨ SCAN GAMBAR DENGAN AI", type="primary"):
            try:
                # Proses AI
                st.info("Sedang menganalisa gambar teknik...")
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                img = Image.open(uploaded_file)
                
                # Prompt khusus untuk Engineering Drawing
                prompt = """
                You are an expert Industrial Engineer. Look at this technical drawing.
                Extract the main dimensions for raw material estimation.
                1. Identify if it looks like a Block or Cylinder.
                2. Find Length, Width, Thickness (for Block) OR Diameter, Length (for Cylinder).
                3. Return ONLY a JSON string like this: {"shape": "block", "length": 100, "width": 50, "thickness": 20}
                If you are unsure, estimate based on the largest visible numbers.
                """
                
                response = model.generate_content([prompt, img])
                text_res = response.text.replace("```json", "").replace("```", "").strip()
                data_json = json.loads(text_res)
                
                # Update Session State
                st.session_state['dimensi']['p'] = float(data_json.get('length', p))
                
                if "block" in data_json.get('shape', '').lower():
                    st.session_state['dimensi']['l'] = float(data_json.get('width', l))
                    st.session_state['dimensi']['t'] = float(data_json.get('thickness', t))
                else:
                    st.session_state['dimensi']['d'] = float(data_json.get('diameter', d)) # Asumsi diameter
                
                st.session_state['scan_result'] = "✅ Sukses! Silakan cek angka di bawah."
                st.rerun() # Refresh halaman biar angka terisi
                
            except Exception as e:
                st.error(f"Gagal scan: {e}")

with col_preview:
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Preview Gambar User", use_container_width=True)
        st.caption(st.session_state['scan_result'])
    else:
        # Tampilkan visualisasi 3D dummy kalau belum ada gambar
        st.info("Visualisasi 3D akan muncul setelah data terisi.")
        fig = go.Figure()
        if tipe_benda == "Block (Kotak)":
             fig.add_trace(go.Mesh3d(x=[0, p, p, 0, 0, p, p, 0], y=[0, 0, l, l, 0, 0, l, l], z=[0, 0, 0, 0, t, t, t, t], i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2], j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3], k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6], color='cyan', opacity=0.5))
        else:
             z = np.linspace(0, p, 30); th = np.linspace(0, 2*np.pi, 30); tg, zg = np.meshgrid(th, z); x = (d/2)*np.cos(tg); y = (d/2)*np.sin(tg)
             fig.add_trace(go.Surface(x=x, y=y, z=zg, showscale=False))
        st.plotly_chart(fig, use_container_width=True)


# --- 5. LOGIKA HARGA (SAMA SEPERTI SEBELUMNYA) ---
st.divider()
col1, col2, col3 = st.columns(3)

with col1:
    st.header("3. Material & Proses")
    pilihan_material = st.selectbox("Material", df_material['Material'].unique())
    pilihan_mesin = st.selectbox("Mesin", df_machine['Machine_Name'].unique())

with col2:
    st.header("4. Estimasi")
    jam = st.number_input("Jam Kerja", 0.5, 100.0, 1.0)
    margin = st.slider("Margin %", 10, 100, 30)

# Kalkulasi
mat_data = df_material[df_material['Material'] == pilihan_material].iloc[0]
mac_data = df_machine[df_machine['Machine_Name'] == pilihan_mesin].iloc[0]

berat = (vol_cm3 * mat_data['Density']) / 1000
cost_mat = berat * mat_data['Price_Kg']
cost_mac = (jam * mac_data['Cost_Per_Hour'] * mat_data['Hardness_Factor']) + mac_data['Setup_Cost']
hpp = cost_mat + cost_mac
harga = hpp + (hpp * (margin/100))

with col3:
    st.header("💰 Total Harga")
    st.metric("Berat", f"{berat:.2f} kg")
    st.metric("HPP", f"Rp {hpp:,.0f}")
    st.success(f"OFFER: Rp {harga:,.0f}")
