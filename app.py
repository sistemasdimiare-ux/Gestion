import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz
import time
import re

# 1. CONEXIÓN A GOOGLE SHEETS
def save_to_google_sheets(datos_fila):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
        client = gspread.authorize(creds)
        # El nombre de tu Excel debe ser: GestionDiaria
        sheet = client.open("GestionDiaria").sheet1
        sheet.append_row(datos_fila)
        return True
    except Exception as e:
        st.error(f"Error: {e}")
        return False

# 2. CONFIGURACIÓN
st.set_page_config(page_title="Ventas", layout="wide")
if "form_key" not in st.session_state:
    st.session_state.form_key = 0

# 3. FORMULARIO
st.title("📝 Registro de Gestión")

with st.form(key=f"f_{st.session_state.form_key}"):
    c1, c2 = st.columns(2)
    with c1:
        zonal = st.selectbox("ZONAL", ["SELECCIONA", "TRUJILLO", "LIMA NORTE", "LIMA SUR", "LIMA ESTE", "HUANCAYO", "CAJAMARCA", "TARAPOTO"])
        dni_v = st.text_input("DNI VENDEDOR (8)", max_chars=8)
        det = st.selectbox("DETALLE *", ["SELECCIONA", "VENTA FIJA", "NO-VENTA", "CLIENTE AGENDADO", "REFERIDO", "PRE-VENTA"])
        nom_c = st.text_input("NOMBRE CLIENTE").upper()
        dni_c = st.text_input("DNI CLIENTE (8)", max_chars=8)
        t_op = st.selectbox("OPERACIÓN", ["SELECCIONA", "CAPTACIÓN", "MIGRACIÓN", "COMPLETA TV", "COMPLETA MT", "COMPLETA BA"])
    with c2:
        prod = st.selectbox("PRODUCTO", ["SELECCIONA", "NAKED", "DUO INT + TV", "DUO TV", "DUO BA", "TRIO"])
        ped = st.text_input("PEDIDO (10)", max_chars=10)
        mail = st.text_input("EMAIL")
        dir_i = st.text_input("DIRECCIÓN").upper()
        tel1 = st.text_input("CONTACTO 1 (9)", max_chars=9)
        mot = st.selectbox("MOTIVO NO VENTA", ["", "COMPETENCIA", "CLIENTE MOVISTAR", "MALA EXPERIENCIA", "CARGO FIJO ALTO", "SIN COBERTURA"])
    
    env = st.form_submit_button("REGISTRAR GESTIÓN")

# 4. LÓGICA
if env:
    err = []
    if len(dni_v) != 8: err.append("DNI Vendedor incorrecto")
    if det != "NO-VENTA":
        if len(dni_c) != 8: err.append("DNI Cliente incorrecto")
        if len(ped) != 10: err.append("Pedido debe tener 10 dígitos")
        if len(tel1) != 9: err.append("Contacto debe tener 9 dígitos")
    
    if err:
        for e in err: st.error(e)
    else:
        tz = pytz.timezone('America/Lima')
        ahora = datetime.now(tz)
        fila = [
            ahora.strftime("%d/%m/%Y %H:%M:%S"), zonal, dni_v, det,
            t_op if det != "NO-VENTA" else "N/A",
            nom_c if det != "NO-VENTA" else "N/A",
            dni_c if det != "NO-VENTA" else "N/A",
            dir_i, mail if mail else "N/A",
            tel1 if det != "NO-VENTA" else "N/A",
            "", prod if det != "NO-VENTA" else "N/A",
            "", ped if det != "NO-VENTA" else "0",
            "SI", mot if det == "NO-VENTA" else "N/A",
            "", "", ahora.strftime("%d/%m/%Y"), ahora.strftime("%H:%M:%S")
        ]
        if save_to_google_sheets(fila):
            st.success("¡Registrado!")
            st.session_state.form_key += 1
            st.rerun()
