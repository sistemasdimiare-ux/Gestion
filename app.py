import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz
import time

# --- 1. CONEXIÓN ---
def conectar_google():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
    client = gspread.authorize(creds)
    return client.open("GestionDiaria")

def save_to_google_sheets(datos_fila):
    try:
        doc = conectar_google()
        sheet = doc.sheet1
        sheet.append_row(datos_fila, value_input_option='USER_ENTERED')
        return True
    except Exception as e:
        st.error(f"❌ Error al guardar: {e}")
        return False

# --- 2. CARGA DE BASE MAESTRA (Estructura de Supervisores) ---
@st.cache_data(ttl=600) # Se actualiza cada 10 min
def cargar_estructura():
    try:
        doc = conectar_google()
        # Leemos la pestaña llamada "Estructura"
        ws = doc.worksheet("Estructura")
        df = pd.DataFrame(ws.get_all_records())
        # Convertimos DNI a string para evitar líos con los ceros
        df['DNI'] = df['DNI'].astype(str).str.zfill(8)
        return df
    except:
        return pd.DataFrame(columns=['DNI', 'NOMBRE VENDEDOR', 'SUPERVISOR', 'ZONAL'])

# --- 3. CONFIGURACIÓN Y PERSISTENCIA ---
st.set_page_config(page_title="Sistema de Ventas Pro", layout="wide")

if "dni_fijo" not in st.session_state: st.session_state.dni_fijo = ""
if "form_key" not in st.session_state: st.session_state.form_key = 0

df_maestro = cargar_estructura()

# --- SIDEBAR INTELIGENTE ---
st.sidebar.title("👤 Identificación")
dni_input = st.sidebar.text_input("INGRESE SU DNI VENDEDOR", value=st.session_state.dni_fijo, max_chars=8)
st.session_state.dni_fijo = dni_input

# Búsqueda automática de Supervisor y Zonal
vendedor_info = df_maestro[df_maestro['DNI'] == dni_input]

if not vendedor_info.empty:
    supervisor_fijo = vendedor_info.iloc[0]['SUPERVISOR']
    zonal_fija = vendedor_info.iloc[0]['ZONAL']
    nombre_vend = vendedor_info.iloc[0]['NOMBRE VENDEDOR']
    st.sidebar.success(f"✅ Hola {nombre_vend}")
    st.sidebar.info(f"📍 Zonal: {zonal_fija}\n\n👤 Sup: {supervisor_fijo}")
else:
    supervisor_fijo = "NO ENCONTRADO"
    zonal_fija = "SELECCIONA"
    if dni_input: st.sidebar.warning("⚠️ DNI no registrado en Estructura.")

# --- 4. FORMULARIO DE GESTIÓN ---
st.title("📝 Registro de Gestión Diaria")

detalle = st.selectbox("DETALLE DE GESTIÓN *", ["SELECCIONA", "VENTA FIJA", "NO-VENTA", "CLIENTE AGENDADO", "REFERIDO", "PRE-VENTA"])

with st.form(key=f"main_f_{st.session_state.form_key}"):
    motivo_nv = nombre = dni_c = t_op = prod = mail = dire = c1 = c2 = fe = n_ref = c_ref = "N/A"
    pedido = "0"; piloto = "NO"

    if detalle == "NO-VENTA":
        st.subheader("Opciones de No-Venta")
        motivo_nv = st.selectbox("MOTIVO *", ["SELECCIONA", "COMPETENCIA", "CLIENTE MOVISTAR", "MALA EXPERIENCIA", "CARGO FIJO ALTO", "SIN COBERTURA"])
    elif detalle == "REFERIDO":
        st.subheader("Datos del Referido")
        r1, r2 = st.columns(2); n_ref = r1.text_input("NOMBRE REFERIDO").upper(); c_ref = r2.text_input("CONTACTO REFERIDO (9)", max_chars=9)
    elif detalle != "SELECCIONA":
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("NOMBRE CLIENTE").upper()
            dni_c = st.text_input("DNI CLIENTE (8)", max_chars=8)
            t_op = st.selectbox("OPERACIÓN", ["SELECCIONA", "CAPTACIÓN", "MIGRACIÓN", "COMPLETA TV", "COMPLETA MT", "COMPLETA BA"])
            prod = st.selectbox("PRODUCTO", ["SELECCIONA", "NAKED", "DUO INT + TV", "DUO TV", "DUO BA", "TRIO"])
            pedido = st.text_input("PEDIDO (10)", max_chars=10)
            fe = st.text_input("CÓDIGO FE")
        with col2:
            mail = st.text_input("EMAIL"); dire = st.text_input("DIRECCIÓN").upper()
            c1 = st.text_input("CONTACTO 1 (9)", max_chars=9)
            c2 = st.text_input("CONTACTO 2 (9)", max_chars=9)
            piloto = st.radio("¿PILOTO?", ["SI", "NO"], index=1, horizontal=True)

    enviar = st.form_submit_button("🚀 REGISTRAR GESTIÓN", use_container_width=True)

# --- 5. VALIDACIONES Y ENVÍO ---
if enviar:
    errores = []
    if supervisor_fijo == "NO ENCONTRADO": errores.append("⚠️ Tu DNI no está en la base de supervisores.")
    if detalle == "VENTA FIJA":
        if not nombre or not fe or not dire: errores.append("⚠️ Datos obligatorios incompletos.")
        if not dni_c.isdigit() or len(dni_c) != 8: errores.append("⚠️ DNI Cliente debe ser de 8 números.")
        if not c1.isdigit() or len(c1) != 9: errores.append("⚠️ Contacto debe ser de 9 números.")
    
    if errores:
        for err in errores: st.error(err)
    else:
        tz = pytz.timezone('America/Lima'); marca = datetime.now(tz)
        # La fila ahora incluye SUPERVISOR automáticamente
        fila = [
            marca.strftime("%d/%m/%Y %H:%M:%S"), zonal_fija, f"'{st.session_state.dni_fijo}", 
            supervisor_fijo, # Nueva columna D para tu Dashboard
            detalle, t_op, nombre, f"'{dni_c}", dire, mail, c1, c2, prod, fe, pedido, 
            piloto, motivo_nv, n_ref, c_ref, marca.strftime("%d/%m/%Y")
        ]
        if save_to_google_sheets(fila):
            st.success(f"✅ ¡Registrado! Supervisor: {supervisor_fijo}")
            st.balloons(); time.sleep(2)
            st.session_state.form_key += 1; st.rerun()
