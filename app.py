import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz
import time

# --- 1. CONEXIÓN ---
def save_to_google_sheets(datos_fila):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
        client = gspread.authorize(creds)
        sheet = client.open("GestionDiaria").sheet1
        sheet.append_row(datos_fila)
        return True
    except Exception as e:
        st.error(f"❌ Error: {e}")
        return False

# --- 2. PERSISTENCIA (CAPA 1: VENDEDOR) ---
st.set_page_config(page_title="Registro de Ventas", layout="wide")

if "zonal_fija" not in st.session_state: st.session_state.zonal_fija = "SELECCIONA"
if "dni_fijo" not in st.session_state: st.session_state.dni_fijo = ""
if "form_key" not in st.session_state: st.session_state.form_key = 0

# Sidebar fijo
st.sidebar.title("👤 Datos Vendedor")
st.session_state.zonal_fija = st.sidebar.selectbox("ZONAL", ["SELECCIONA", "TRUJILLO", "LIMA NORTE", "LIMA SUR", "LIMA ESTE", "HUANCAYO", "CAJAMARCA", "TARAPOTO"], index=["SELECCIONA", "TRUJILLO", "LIMA NORTE", "LIMA SUR", "LIMA ESTE", "HUANCAYO", "CAJAMARCA", "TARAPOTO"].index(st.session_state.zonal_fija))
st.session_state.dni_fijo = st.sidebar.text_input("DNI VENDEDOR", value=st.session_state.dni_fijo, max_chars=8)

# --- 3. FORMULARIO (CAPA 2: GESTIÓN) ---
st.title("📝 Registro de Gestión")

# IMPORTANTE: El detalle va FUERA del form para que la página reaccione al instante
detalle = st.selectbox("DETALLE DE GESTIÓN *", ["SELECCIONA", "VENTA FIJA", "NO-VENTA", "CLIENTE AGENDADO", "REFERIDO", "PRE-VENTA"])

with st.form(key=f"main_f_{st.session_state.form_key}"):
    
    # LÓGICA DINÁMICA DE CAMPOS
    if detalle == "NO-VENTA":
        st.subheader("Opciones de No-Venta")
        motivo_nv = st.selectbox("MOTIVO DE NO VENTA *", ["SELECCIONA", "COMPETENCIA", "CLIENTE MOVISTAR", "MALA EXPERIENCIA", "CARGO FIJO ALTO", "SIN COBERTURA"])
        
        # Seteo interno de nulos
        nombre, dni_c, t_op, prod, pedido, mail, dire, c1, c2, fe, piloto, n_ref, c_ref = "N/A", "N/A", "N/A", "N/A", "0", "N/A", "N/A", "N/A", "N/A", "N/A", "NO", "N/A", "N/A"
        
    else:
        motivo_nv = "N/A"
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("NOMBRE DE CLIENTE").upper()
            dni_c = st.text_input("DNI CLIENTE", max_chars=8)
            t_op = st.selectbox("TIPO OPERACIÓN", ["SELECCIONA", "CAPTACIÓN", "MIGRACIÓN", "COMPLETA TV", "COMPLETA MT", "COMPLETA BA"])
            prod = st.selectbox("PRODUCTO", ["SELECCIONA", "NAKED", "DUO INT + TV", "DUO TV", "DUO BA", "TRIO"])
            pedido = st.text_input("N° PEDIDO (10)", max_chars=10)
        with col2:
            mail = st.text_input("EMAIL")
            dire = st.text_input("DIRECCIÓN").upper()
            c1 = st.text_input("CONTACTO 1", max_chars=9)
            c2 = st.text_input("CONTACTO 2", max_chars=9)
            fe = st.text_input("CÓDIGO FE")
            piloto = st.radio("¿PILOTO?", ["SI", "NO"], index=1, horizontal=True)

        st.markdown("---")
        r1, r2 = st.columns(2)
        n_ref = r1.text_input("NOMBRE REFERIDO").upper()
        c_ref = r2.text_input("CONTACTO REFERIDO", max_chars=9)

    enviar = st.form_submit_button("🚀 REGISTRAR GESTIÓN", use_container_width=True)

# --- 4. VALIDACIÓN Y ENVÍO ---
if enviar:
    errores = []
    if len(st.session_state.dni_fijo) != 8: errores.append("⚠️ Revisa tu DNI en la izquierda.")
    if detalle == "SELECCIONA": errores.append("⚠️ Selecciona el Detalle.")
    
    if detalle == "NO-VENTA":
        if motivo_nv == "SELECCIONA": errores.append("⚠️ Indica el motivo de NO VENTA.")
    else:
        if not nombre or len(dni_c) < 8 or len(pedido) < 10:
            errores.append("⚠️ Completa los datos del cliente (DNI 8 dígitos, Pedido 10 dígitos).")

    if errores:
        for e in errores: st.error(e)
    else:
        tz = pytz.timezone('America/Lima')
        marca = datetime.now(tz)
        fila = [
            marca.strftime("%d/%m/%Y %H:%M:%S"), st.session_state.zonal_fija, st.session_state.dni_fijo,
            detalle, t_op, nombre, dni_c, dire, mail, c1, c2, prod, fe, pedido, piloto,
            motivo_nv, n_ref, c_ref, marca.strftime("%d/%m/%Y"), marca.strftime("%H:%M:%S")
        ]

        if save_to_google_sheets(fila):
            st.success("✅ ¡Guardado!")
            st.session_state.form_key += 1
            st.rerun()
