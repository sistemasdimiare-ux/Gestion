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

# --- 2. CONFIGURACIÓN Y PERSISTENCIA ---
st.set_page_config(page_title="Sistema de Ventas Oficial", layout="wide")

if "zonal_fija" not in st.session_state: st.session_state.zonal_fija = "SELECCIONA"
if "dni_fijo" not in st.session_state: st.session_state.dni_fijo = ""
if "form_key" not in st.session_state: st.session_state.form_key = 0

def reiniciar_formulario():
    st.session_state.form_key += 1
    st.rerun()

# CAPA 1: SIDEBAR (Vendedor fijo)
st.sidebar.title("👤 Datos Vendedor")
st.session_state.zonal_fija = st.sidebar.selectbox("ZONAL", ["SELECCIONA", "TRUJILLO", "LIMA NORTE", "LIMA SUR", "LIMA ESTE", "HUANCAYO", "CAJAMARCA", "TARAPOTO"], index=["SELECCIONA", "TRUJILLO", "LIMA NORTE", "LIMA SUR", "LIMA ESTE", "HUANCAYO", "CAJAMARCA", "TARAPOTO"].index(st.session_state.zonal_fija))
st.session_state.dni_fijo = st.sidebar.text_input("MI DNI (8 dígitos)", value=st.session_state.dni_fijo, max_chars=8)

# --- 3. FORMULARIO (CAPA 2: GESTIÓN) ---
st.title("📝 Registro de Gestión")

# Selector de detalle fuera del form para que la capa cambie al instante
detalle = st.selectbox("DETALLE DE GESTIÓN *", ["SELECCIONA", "VENTA FIJA", "NO-VENTA", "CLIENTE AGENDADO", "REFERIDO", "PRE-VENTA"])

with st.form(key=f"main_f_{st.session_state.form_key}"):
    
    # Inicializamos todas las variables como "N/A" por defecto
    motivo_nv = nombre = dni_c = t_op = prod = mail = dire = c1 = c2 = fe = n_ref = c_ref = "N/A"
    pedido = "0"
    piloto = "NO"

    # CASO 1: NO-VENTA (Capa mínima)
    if detalle == "NO-VENTA":
        st.subheader("Opciones de No-Venta")
        motivo_nv = st.selectbox("MOTIVO DE NO VENTA *", ["SELECCIONA", "COMPETENCIA", "CLIENTE MOVISTAR", "MALA EXPERIENCIA", "CARGO FIJO ALTO", "SIN COBERTURA"])

    # CASO 2: REFERIDO (Capa mínima)
    elif detalle == "REFERIDO":
        st.subheader("Datos del Referido")
        r1, r2 = st.columns(2)
        n_ref = r1.text_input("NOMBRE DEL REFERIDO").upper()
        c_ref = r2.text_input("CONTACTO DEL REFERIDO (9 dígitos)", max_chars=9)

    # CASO 3: TODO LO DEMÁS (Capa completa)
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
            c1 = st.text_input("CONTACTO 1 (9)", max_chars=9)
            c2 = st.text_input("CONTACTO 2 (9)", max_chars=9)
            fe = st.text_input("CÓDIGO FE(13)", max_chars=13)
            piloto = st.radio("¿VENTA PILOTO?", ["SI", "NO"], index=1, horizontal=True)

    enviar = st.form_submit_button("🚀 REGISTRAR GESTIÓN", use_container_width=True)

# --- 4. VALIDACIONES Y ENVÍO ---
if enviar:
    errores = []
    if len(st.session_state.dni_fijo) != 8: errores.append("⚠️ Revisa el DNI del vendedor en el sidebar.")
    if detalle == "SELECCIONA": errores.append("⚠️ Selecciona el Detalle.")
    
    if detalle == "NO-VENTA" and motivo_nv == "SELECCIONA":
        errores.append("⚠️ Elige un motivo de NO-VENTA.")
    elif detalle == "REFERIDO" and (not n_ref or len(c_ref) != 9):
        errores.append("⚠️ Nombre y Teléfono (9) del referido son obligatorios.")
    elif detalle not in ["NO-VENTA", "REFERIDO", "SELECCIONA"]:
        if not nombre or len(dni_c) != 8 or len(pedido) != 10:
            errores.append("⚠️ Datos de cliente incompletos (DNI 8 dígitos, Pedido 10 dígitos).")

    if errores:
        for e in errores: st.error(e)
    else:
        tz = pytz.timezone('America/Lima')
        marca = datetime.now(tz)
        
        # Lista final de 20 columnas para el Excel
        fila = [
            marca.strftime("%d/%m/%Y %H:%M:%S"), # A: Marca Temporal
            st.session_state.zonal_fija,         # B: Zonal
            st.session_state.dni_fijo,           # C: DNI Vendedor
            detalle,                             # D: Detalle
            t_op,                                # E: Tipo Operación
            nombre,                              # F: Nombre Cliente
            dni_c,                               # G: DNI Cliente
            dire,                                # H: Dirección
            mail,                                # I: Email
            c1,                                  # J: Contacto 1
            c2,                                  # K: Contacto 2
            prod,                                # L: Producto
            fe,                                  # M: Código FE
            pedido,                              # N: Pedido
            piloto,                              # O: Piloto
            motivo_nv,                           # P: Motivo No-Venta
            n_ref,                               # Q: Nombre Referido
            c_ref,                               # R: Contacto Referido
            marca.strftime("%d/%m/%Y"),          # S: Fecha
            marca.strftime("%H:%M:%S")           # T: Hora
        ]

        if save_to_google_sheets(fila):
            st.success("✅ ¡Registro Exitoso!")
            st.balloons()
            time.sleep(2)
            reiniciar_formulario()
