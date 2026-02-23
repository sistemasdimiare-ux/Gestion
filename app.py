import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz
import time

def save_to_google_sheets(datos_fila):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
        client = gspread.authorize(creds)
        sheet = client.open("GestionDiaria").sheet1
        sheet.append_row(datos_fila)
        return True
    except Exception as e:
        st.error(f"Error: {e}")
        return False

st.set_page_config(page_title="Ventas Pro", layout="wide")

# --- PERSISTENCIA DE DATOS DEL VENDEDOR ---
# Esto hace que el DNI y Zonal no se borren nunca
if "zonal_fija" not in st.session_state: st.session_state.zonal_fija = "SELECCIONA"
if "dni_fijo" not in st.session_state: st.session_state.dni_fijo = ""
if "form_key" not in st.session_state: st.session_state.form_key = 0

# SIDEBAR (Capa fija)
st.sidebar.title("👤 Datos del Vendedor")
st.session_state.zonal_fija = st.sidebar.selectbox("ZONAL", ["SELECCIONA", "TRUJILLO", "LIMA NORTE", "LIMA SUR", "LIMA ESTE", "HUANCAYO", "CAJAMARCA", "TARAPOTO"], index=["SELECCIONA", "TRUJILLO", "LIMA NORTE", "LIMA SUR", "LIMA ESTE", "HUANCAYO", "CAJAMARCA", "TARAPOTO"].index(st.session_state.zonal_fija))
st.session_state.dni_fijo = st.sidebar.text_input("MI DNI (8 dígitos)", value=st.session_state.dni_fijo, max_chars=8)

# CUERPO PRINCIPAL
st.title("📝 Registro de Gestión")

with st.form(key=f"form_{st.session_state.form_key}"):
    detalle = st.selectbox("DETALLE DE GESTIÓN", ["SELECCIONA", "VENTA FIJA", "NO-VENTA", "CLIENTE AGENDADO", "REFERIDO", "PRE-VENTA"])
    
    # LÓGICA DINÁMICA: Si es NO-VENTA, solo muestra el motivo
    if detalle == "NO-VENTA":
        motivo = st.selectbox("INDICAR MOTIVO DE NO VENTA", ["", "COMPETENCIA", "CLIENTE MOVISTAR", "MALA EXPERIENCIA", "CARGO FIJO ALTO", "SIN COBERTURA"])
        # Campos ocultos automáticos
        nombre, dni_c, pedido, tel1 = "N/A", "N/A", "0", "N/A"
    else:
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("NOMBRE
