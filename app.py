import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz
import time

# --- 1. FUNCIÓN DE CONEXIÓN ---
def save_to_google_sheets(datos_fila):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
        client = gspread.authorize(creds)
        sheet = client.open("GestionDiaria").sheet1
        # Usamos USER_ENTERED para que respete la comilla simple como formato de texto
        sheet.append_row(datos_fila, value_input_option='USER_ENTERED')
        return True
    except Exception as e:
        st.error(f"❌ Error de conexión: {e}")
        return False

# --- 2. CONFIGURACIÓN Y PERSISTENCIA (CAPA 1: VENDEDOR) ---
st.set_page_config(page_title="Sistema de Ventas Oficial", layout="wide")

# Persistencia de datos del vendedor
if "zonal_fija" not in st.session_state: st.session_state.zonal_fija = "SELECCIONA"
if "dni_fijo" not in st.session_state: st.session_state.dni_fijo = ""
if "form_key" not in st.session_state: st.session_state.form_key = 0

def reiniciar_formulario():
    st.session_state.form_key += 1
    st.rerun()

# SIDEBAR: Identificación del vendedor (No se borra)
st.sidebar.title("👤 Identificación Vendedor")
st.session_state.zonal_fija = st.sidebar.selectbox(
    "ZONAL", 
    ["SELECCIONA", "TRUJILLO", "LIMA NORTE", "LIMA SUR", "LIMA ESTE", "HUANCAYO", "CAJAMARCA", "TARAPOTO"],
    index=["SELECCIONA", "TRUJILLO", "LIMA NORTE", "LIMA SUR", "LIMA ESTE", "HUANCAYO", "CAJAMARCA", "TARAPOTO"].index(st.session_state.zonal_fija)
)
st.session_state.dni_fijo = st.sidebar.text_input("MI DNI (8 dígitos)", value=st.session_state.dni_fijo, max_chars=8)

# --- 3. FORMULARIO (CAPA 2: GESTIÓN) ---
st.title("📝 Registro de Gestión Diaria")

detalle = st.selectbox("DETALLE DE GESTIÓN *", ["SELECCIONA", "VENTA FIJA", "NO-VENTA", "CLIENTE AGENDADO", "REFERIDO", "PRE-VENTA"])

with st.form(key=f"main_f_{st.session_state.form_key}"):
    
    # Inicialización de variables
    motivo_nv = nombre = dni_c = t_op = prod = mail = dire = c1 = c2 = fe = n_ref = c_ref = "N/A"
    pedido = "0"
    piloto = "NO"

    if detalle == "NO-VENTA":
        st.subheader("Opciones de No-Venta")
        motivo_nv = st.selectbox("MOTIVO DE NO VENTA *", ["SELECCIONA", "COMPETENCIA", "CLIENTE MOVISTAR", "MALA EXPERIENCIA", "CARGO FIJO ALTO", "SIN COBERTURA"])

    elif detalle == "REFERIDO":
        st.subheader("Datos del Referido")
        r1, r2 = st.columns(2)
        n_ref = r1.text_input("NOMBRE DEL REFERIDO").upper()
        c_ref = r2.text_input("CONTACTO DEL REFERIDO (9 dígitos)", max_chars=9)

    elif detalle != "SELECCIONA":
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("NOMBRE DE CLIENTE").upper()
            dni_c = st.text_input("DNI CLIENTE (8 dígitos)", max_chars=8)
            t_op = st.selectbox("TIPO OPERACIÓN", ["SELECCIONA", "CAPTACIÓN", "MIGRACIÓN", "COMPLETA TV", "COMPLETA MT", "COMPLETA BA"])
            prod = st.selectbox("PRODUCTO", ["SELECCIONA", "NAKED", "DUO INT + TV", "DUO TV", "DUO BA", "TRIO"])
            pedido = st.text_input("N° PEDIDO (10 dígitos)", max_chars=10)
            fe = st.text_input("CÓDIGO FE")
        with col2:
            mail = st.text_input("EMAIL")
            dire = st.text_input("DIRECCIÓN DE INSTALACIÓN").upper()
            c1 = st.text_input("CONTACTO 1 (9 dígitos)", max_chars=9)
            c2 = st.text_input("CONTACTO 2 (9 dígitos)", max_chars=9)
            piloto = st.radio("¿VENTA PILOTO?", ["SI", "NO"], index=1, horizontal=True)

    enviar = st.form_submit_button("🚀 REGISTRAR GESTIÓN", use_container_width=True)

# --- 4. VALIDACIONES Y FORMATEO ---
if enviar:
    errores = []
    
    # Validación Sidebar
    if not st.session_state.dni_fijo.isdigit() or len(st.session_state.dni_fijo) != 8:
        errores.append("⚠️ Su DNI de vendedor debe tener 8 números.")
    
    if detalle == "VENTA FIJA":
        if not nombre or not fe or not dire: errores.append("⚠️ Nombre, FE y Dirección son obligatorios.")
        if not dni_c.isdigit() or len(dni_c) != 8: errores.append("⚠️ El DNI CLIENTE debe tener 8 números.")
        if not pedido.isdigit() or len(pedido) != 10: errores.append("⚠️ El PEDIDO debe tener 10 números.")
        if not c1.isdigit() or len(c1) != 9: errores.append("⚠️ El CONTACTO 1 debe tener 9 números.")

    if errores:
        for err in errores: st.error(err)
    else:
        tz = pytz.timezone('America/Lima')
        marca = datetime.now(tz)
        
        # Formateo de fila: Solo DNI Vendedor y DNI Cliente llevan la comilla para preservar ceros
        fila = [
            marca.strftime("%d/%m/%Y %H:%M:%S"), 
            st.session_state.zonal_fija, 
            f"'{st.session_state.dni_fijo}", # DNI VENDEDOR CON PRESERVACIÓN
            detalle, 
            t_op, 
            nombre, 
            f"'{dni_c}", # DNI CLIENTE CON PRESERVACIÓN
            dire, 
            mail, 
            c1, # Los teléfonos y pedidos van normal
            c2, 
            prod, 
            fe, 
            pedido, 
            piloto, 
            motivo_nv, 
            n_ref, 
            c_ref, 
            marca.strftime("%d/%m/%Y"), 
            marca.strftime("%H:%M:%S")
        ]

        if save_to_google_sheets(fila):
            st.success("✅ Registro completado. Ceros en DNI preservados.")
            st.balloons()
            time.sleep(2)
            reiniciar_formulario()
