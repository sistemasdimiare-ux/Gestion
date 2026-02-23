import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz
import time

# --- 1. CONFIGURACIÓN DE CONEXIÓN (GOOGLE SHEETS) ---
def save_to_google_sheets(datos_fila):
    # Definimos los permisos necesarios
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    try:
        # Lee las credenciales desde los Secrets de Streamlit
        creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
        client = gspread.authorize(creds)
        
        # IMPORTANTE: Asegúrate de que tu Excel se llame exactamente así
        sheet = client.open("GestionDiaria").sheet1
        
        # Agrega la fila al final
        sheet.append_row(datos_fila)
        return True
    except Exception as e:
        st.error(f"❌ Error al conectar con Google Sheets: {e}")
        return False

# --- 2. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Registro de Ventas", layout="wide")

# Inicializar clave de formulario para reinicio limpio
if "form_key" not in st.session_state:
    st.session_state.form_key = 0

def reiniciar_formulario():
    st.session_state.form_key += 1
    st.rerun()

# --- 3. INTERFAZ DE USUARIO ---
st.title("📝 Registro de ventas")
st.markdown("---")

# Sidebar para datos del vendedor (se mantienen fijos para agilizar)
st.sidebar.header("Datos del Vendedor")
zonal = st.sidebar.selectbox("ZONAL", ["SELECCIONA", "TRUJILLO", "LIMA NORTE", "LIMA SUR", "LIMA ESTE", "HUANCAYO", "CAJAMARCA", "TARAPOTO"])
dni_vendedor = st.sidebar.text_input("DNI VENDEDOR", max_chars=8, help="Ingresa tu DNI de 8 dígitos")

# Formulario principal
with st.form(key=f"ventas_form_{st.session_state.form_key}"):
    col1, col2 = st.columns(2)
    
    with col1:
        detalle = st.selectbox("DETALLE DE GESTIÓN *", ["SELECCIONA", "VENTA FIJA", "NO-VENTA", "CLIENTE AGENDADO", "REFERIDO", "PRE-VENTA"])
        nombre_cliente = st.text_input("NOMBRE COMPLETO DEL CLIENTE").upper()
        dni_cliente = st.text_input("DNI/RUC CLIENTE", max_chars=11)
        tipo_op = st.selectbox("TIPO DE OPERACIÓN", ["SELECCIONA", "CAPTACIÓN", "MIGRACIÓN", "COMPLETA TV", "COMPLETA MT", "COMPLETA BA"])
        producto = st.selectbox("PRODUCTO", ["SELECCIONA", "NAKED", "DUO INT + TV", "DUO TV", "DUO BA", "TRIO"])
        pedido = st.text_input("N° DE PEDIDO (10 dígitos)", max_chars=10)

    with col2:
        email = st.text_input("EMAIL DEL CLIENTE")
        direccion = st.text_input("DIRECCIÓN DE INSTALACIÓN").upper()
        cont1 = st.text_input("TELÉFONO CONTACTO 1", max_chars=9)
        cont2 = st.text_input("TELÉFONO CONTACTO 2", max_chars=9)
        cod_fe = st.text_input("CÓDIGO FE")
        venta_piloto = st.radio("¿ES VENTA PILOTO?", ["SI", "NO"], horizontal=True)
        motivo_no_venta = st.selectbox("SI ES 'NO-VENTA', INDIQUE MOTIVO", ["", "COMPETENCIA", "CLIENTE MOVISTAR", "MALA EXPERIENCIA", "CARGO FIJO ALTO", "SIN COBERTURA"])

    st.markdown("---")
    st.subheader("Datos de Referido (Opcional)")
    r_col1, r_col2 = st.columns(2)
    nom_ref = r_col1.text_input("NOMBRE DEL REFERIDO").upper()
    cont_ref = r_col2.text_input("CONTACTO DEL REFERIDO", max_chars=9)

    enviar = st.form_submit_button("🚀 REGISTRAR GESTIÓN", use_container_width=True)

# --- 4. LÓGICA DE PROCESAMIENTO ---
if enviar:
    errores = []
    
    # Validaciones obligatorias
    if zonal == "SELECCIONA" or len(dni_vendedor) != 8:
        errores.append("⚠️ Datos del vendedor incompletos (Zonal y DNI de 8 dígitos).")
    
    if detalle == "SELECCIONA":
        errores.append("⚠️ Seleccione un detalle de gestión.")

    # Lógica específica por tipo de gestión
    if detalle == "NO-VENTA":
        if not motivo_no_venta:
            errores.append("⚠️ Para 'NO-VENTA' debe indicar el motivo.")
    else:
        # Validaciones para ventas reales
        if not nombre_cliente: errores.append("⚠️ Nombre del cliente es obligatorio.")
        if len(dni_cliente) < 8: errores.append("⚠️ DNI/RUC del cliente no es válido.")
