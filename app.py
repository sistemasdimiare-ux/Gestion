import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz
import time
import re

# --- 1. FUNCIÓN DE CONEXIÓN ---
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

# Mantener datos del vendedor fijos en la sesión
if "zonal_fija" not in st.session_state: st.session_state.zonal_fija = "SELECCIONA"
if "dni_fijo" not in st.session_state: st.session_state.dni_fijo = ""
if "form_key" not in st.session_state: st.session_state.form_key = 0

def reiniciar_formulario():
    st.session_state.form_key += 1
    st.rerun()

# --- 3. CAPA 1: DATOS DEL VENDEDOR (SIDEBAR) ---
st.sidebar.title("👤 Identificación")
st.session_state.zonal_fija = st.sidebar.selectbox(
    "ZONAL", 
    ["SELECCIONA", "TRUJILLO", "LIMA NORTE", "LIMA SUR", "LIMA ESTE", "HUANCAYO", "CAJAMARCA", "TARAPOTO"],
    index=["SELECCIONA", "TRUJILLO", "LIMA NORTE", "LIMA SUR", "LIMA ESTE", "HUANCAYO", "CAJAMARCA", "TARAPOTO"].index(st.session_state.zonal_fija)
)
st.session_state.dni_fijo = st.sidebar.text_input("N° DOCUMENTO VENDEDOR", value=st.session_state.dni_fijo, max_chars=8)

# --- 4. CAPA 2: FORMULARIO DE GESTIÓN ---
st.title("📝 Registro de Gestión Diaria")

with st.form(key=f"main_form_{st.session_state.form_key}"):
    # El detalle define qué campos se muestran
    detalle = st.selectbox("DETALLE DE GESTIÓN *", ["SELECCIONA", "VENTA FIJA", "NO-VENTA", "CLIENTE AGENDADO", "REFERIDO", "PRE-VENTA"])
    
    st.markdown("---")
    
    # LÓGICA PARA NO-VENTA
    if detalle == "NO-VENTA":
        st.info("Ha seleccionado NO-VENTA. Solo debe completar el motivo.")
        motivo_no_venta = st.selectbox("INDICAR MOTIVO DE NO VENTA", ["SELECCIONA", "COMPETENCIA", "CLIENTE MOVISTAR", "MALA EXPERIENCIA", "CARGO FIJO ALTO", "SIN COBERTURA"])
        
        # Valores automáticos para campos ocultos
        nombre_cliente = dni_cliente = tipo_op = producto = pedido = email = direccion = cont1 = cont2 = cod_fe = venta_piloto = nom_ref = cont_ref = "N/A"
        
    else:
        # CAMPOS COMPLETOS PARA OTRAS GESTIONES
        col1, col2 = st.columns(2)
        with col1:
            nombre_cliente = st.text_input("NOMBRE DE CLIENTE").upper()
            dni_cliente = st.text_input("N° DE DOCUMENTO CLIENTE", max_chars=8)
            tipo_op = st.selectbox("Tipo de Operación", ["SELECCIONA", "CAPTACIÓN", "MIGRACIÓN", "COMPLETA TV", "COMPLETA MT", "COMPLETA BA"])
            producto = st.selectbox("PRODUCTO", ["SELECCIONA", "NAKED", "DUO INT + TV", "DUO TV", "DUO BA", "TRIO"])
            pedido = st.text_input("N° de Pedido", max_chars=10)
            cod_fe = st.text_input("Código FE")
            
        with col2:
            email = st.text_input("EMAIL DE CLIENTE")
            direccion = st.text_input("DIRECCION DE INSTALACION").upper()
            cont1 = st.text_input("N° DE CONTACTO DE CLIENTE 1", max_chars=9)
            cont2 = st.text_input("N° DE CONTACTO DE CLIENTE 2", max_chars=9)
            venta_piloto = st.radio("¿Venta Piloto?", ["SI", "NO"], horizontal=True)
            motivo_no_venta = "N/A"

        st.subheader("Datos de Referido")
        r1, r2 = st.columns(2)
        nom_ref = r1.text_input("NOMBRE Y APELLIDO DE REFERIDO").upper()
        cont_ref = r2.text_input("N° DE CONTACTO REFERIDO", max_chars=9)

    enviar = st.form_submit_button("🚀 REGISTRAR GESTIÓN", use_container_width=True)

# --- 5. VALIDACIONES Y ENVÍO ---
if enviar:
    errores = []
    # Validar Vendedor (Sidebar)
    if st.session_state.zonal_fija == "SELECCIONA": errores.append("⚠️ Seleccione su Zonal en el panel izquierdo.")
    if len(st.session_state.dni_fijo) != 8: errores.append("⚠️ Ingrese su DNI de vendedor (8 dígitos) en el panel izquierdo.")
    
    if detalle == "SELECCIONA":
        errores.append("⚠️ Seleccione el detalle de la gestión.")
    elif detalle == "NO-VENTA":
        if motivo_no_venta == "SELECCIONA": errores.append("⚠️ Debe indicar el motivo de la NO VENTA.")
    else:
        # Validaciones para el resto
        if not nombre_cliente: errores.append("⚠️ Nombre del cliente es obligatorio.")
        if len(dni_cliente) != 8: errores.append("⚠️ DNI del cliente debe tener 8 dígitos.")
        if len(pedido) != 10: errores.append("⚠️ El Pedido debe tener 10 dígitos.")
        if len(cont1) != 9: errores.append("⚠️ El Contacto 1 debe tener 9 dígitos.")

    if errores:
        for err in errores: st.error(err)
    else:
        # TIEMPO PERÚ
        tz = pytz.timezone('America/Lima')
        marca = datetime.now(tz)
        
        fila = [
            marca.strftime("%d/%m/%Y %H:%M:%S"), # Marca temporal
            st.session_state.zonal_fija,
            st.session_state.dni_fijo,
            detalle,
            tipo_op,
            nombre_cliente,
            dni_cliente,
            direccion,
            email,
            cont1,
            cont2,
            producto,
            cod_fe,
            pedido,
            venta_piloto,
            motivo_no_venta,
            nom_ref,
            cont_ref,
            marca.strftime("%d/%m/%Y"), # Fecha
            marca.strftime("%H:%M:%S")  # Hora
        ]

        if save_to_google_sheets(fila):
            st.success("✅ ¡Gestión registrada! Los datos del vendedor se mantienen.")
            st.balloons()
            time.sleep(2)
            reiniciar_formulario()
