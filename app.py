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
        st.error(f"❌ Error de conexión: {e}")
        return False

# --- 2. PERSISTENCIA (CAPA 1: VENDEDOR) ---
st.set_page_config(page_title="Registro de Gestión Ventas", layout="wide")

if "zonal_fija" not in st.session_state: st.session_state.zonal_fija = "SELECCIONA"
if "dni_fijo" not in st.session_state: st.session_state.dni_fijo = ""
if "form_key" not in st.session_state: st.session_state.form_key = 0

# Sidebar persistente
st.sidebar.title("👤 Datos Vendedor")
st.session_state.zonal_fija = st.sidebar.selectbox("ZONAL", ["SELECCIONA", "TRUJILLO", "LIMA NORTE", "LIMA SUR", "LIMA ESTE", "HUANCAYO", "CAJAMARCA", "TARAPOTO"], index=["SELECCIONA", "TRUJILLO", "LIMA NORTE", "LIMA SUR", "LIMA ESTE", "HUANCAYO", "CAJAMARCA", "TARAPOTO"].index(st.session_state.zonal_fija))
st.session_state.dni_fijo = st.sidebar.text_input("MI DNI (8 dígitos)", value=st.session_state.dni_fijo, max_chars=8)

# --- 3. FORMULARIO (CAPA 2: GESTIÓN) ---
st.title("📝 Registro de Gestión")

# Selector de detalle fuera del form para actualización instantánea
detalle = st.selectbox("DETALLE DE GESTIÓN *", ["SELECCIONA", "VENTA FIJA", "NO-VENTA", "CLIENTE AGENDADO", "REFERIDO", "PRE-VENTA"])

with st.form(key=f"main_f_{st.session_state.form_key}"):
    
    # Inicialización de variables para evitar errores
    motivo_nv, nombre, dni_c, t_op, prod, pedido, mail, dire, c1, c2, fe, piloto, n_ref, c_ref = ["N/A"] * 13
    pedido = "0" # Por ser numérico en lógica de validación
    piloto = "NO"

    # CASO A: NO-VENTA
    if detalle == "NO-VENTA":
        st.subheader("Opciones de No-Venta")
        motivo_nv = st.selectbox("MOTIVO DE NO VENTA *", ["SELECCIONA", "COMPETENCIA", "CLIENTE MOVISTAR", "MALA EXPERIENCIA", "CARGO FIJO ALTO", "SIN COBERTURA"])

    # CASO B: REFERIDO (Tu nueva petición)
    elif detalle == "REFERIDO":
        st.subheader("Datos del Referido")
        r1, r2 = st.columns(2)
        n_ref = r1.text_input("NOMBRE DEL REFERIDO").upper()
        c_ref = r2.text_input("CONTACTO DEL REFERIDO (9 dígitos)", max_chars=9)

    # CASO C: VENTAS Y OTROS (Campos completos)
    elif detalle != "SELECCIONA":
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
            piloto = st.radio("¿ES VENTA PILOTO?", ["SI", "NO"], index=1, horizontal=True)

    enviar = st.form_submit_button("🚀 REGISTRAR GESTIÓN", use_container_width=True)

# --- 4. LÓGICA DE VALIDACIÓN ---
if enviar:
    errores = []
    if len(st.session_state.dni_fijo) != 8: errores.append("⚠️ Revisa tu DNI de vendedor en la izquierda.")
    if detalle == "SELECCIONA": errores.append("⚠️ Elige un Detalle de gestión.")
    
    if detalle == "NO-VENTA" and motivo_nv == "SELECCIONA":
        errores.append("⚠️ Indica el motivo de NO VENTA.")
    elif detalle == "REFERIDO" and (not n_ref or len(c_ref) != 9):
        errores.append("⚠️ Completa nombre y contacto del referido (9 dígitos).")
    elif detalle not in ["NO-VENTA", "REFERIDO", "SELECCIONA"]:
        if not nombre or len(dni_c) != 8 or len(pedido) != 10 or len(c1) != 9:
            errores.append("⚠️ Datos incompletos: Nombre, DNI(8), Pedido(10) y Contacto(9) son obligatorios.")

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
            st.success("✅ ¡Registro Exitoso!")
            st.session_state.form_key += 1
            st.rerun()
