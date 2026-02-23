import streamlit as st
import pandas as pd
from datetime import datetime
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pytz

# --- 1. CONFIGURACIÓN DE GOOGLE SHEETS ---
def save_to_google_sheets(datos_fila):
    # Definir el alcance
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # OPCIÓN RECOMENDADA: Guardar tus credenciales en los "Secrets" de Streamlit
    # Si usas archivo local: 'credenciales.json'
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
        client = gspread.authorize(creds)
        
        # Abre la hoja por nombre o por URL
        sheet = client.open("Gestion_Ventas_300").sheet1
        
        # Inserta la fila al final
        sheet.append_row(datos_fila)
        return True
    except Exception as e:
        st.error(f"Error de conexión con Google Sheets: {e}")
        return False

# --- 2. CONFIGURACIÓN DE PÁGINA Y REINICIO ---
st.set_page_config(page_title="Sistema Pro - 300 Usuarios", layout="wide")

if "form_key" not in st.session_state:
    st.session_state.form_key = 0

def reiniciar_formulario():
    st.session_state.form_key += 1
    st.rerun()

# --- 3. INTERFAZ ---
st.title("📝 Registro de Gestión Masiva")
st.sidebar.header("Perfil Vendedor")
zonal = st.sidebar.selectbox("ZONAL", ["SELECCIONA", "TRUJILLO", "LIMA NORTE", "LIMA SUR", "LIMA ESTE", "HUANCAYO", "CAJAMARCA", "TARAPOTO"])
dni_vendedor = st.sidebar.text_input("DNI VENDEDOR (8)", max_chars=8)

with st.form(key=f"ventas_v3_{st.session_state.form_key}"):
    c1, c2 = st.columns(2)
    
    with c1:
        detalle = st.selectbox("DETALLE *", ["SELECCIONA", "VENTA FIJA", "NO-VENTA", "CLIENTE AGENDADO", "REFERIDO", "PRE-VENTA"])
        nombre_cliente = st.text_input("NOMBRE DE CLIENTE").upper()
        dni_cliente = st.text_input("DNI/RUC CLIENTE", max_chars=11)
        tipo_op = st.selectbox("Tipo de Operación", ["SELECCIONA", "CAPTACIÓN", "MIGRACIÓN", "COMPLETA TV", "COMPLETA MT", "COMPLETA BA"])
        producto = st.selectbox("PRODUCTO", ["SELECCIONA", "NAKED", "DUO INT + TV", "DUO TV", "DUO BA", "TRIO"])
        pedido = st.text_input("N° de Pedido (10)", max_chars=10)
        email = st.text_input("EMAIL CLIENTE")

    with c2:
        motivo_no_venta = st.selectbox("MOTIVO NO VENTA (Si aplica)", ["", "COMPETENCIA", "CLIENTE MOVISTAR", "MALA EXPERIENCIA", "CARGO FIJO ALTO"])
        direccion = st.text_input("DIRECCION").upper()
        cont1 = st.text_input("CONTACTO 1 (9)", max_chars=9)
        cont2 = st.text_input("CONTACTO 2 (9)", max_chars=9)
        cod_fe = st.text_input("Código FE")
        venta_piloto = st.radio("¿Venta Piloto?", ["SI", "NO"], horizontal=True)

    st.markdown("---")
    nom_ref = st.text_input("NOMBRE REFERIDO")
    cont_ref = st.text_input("CONTACTO REFERIDO (9)", max_chars=9)

    enviar = st.form_submit_button("🚀 REGISTRAR AHORA", use_container_width=True)

# --- 4. VALIDACIONES Y LÓGICA ---
if enviar:
    errores = []
    
    # Validación BASE
    if zonal == "SELECCIONA" or len(dni_vendedor) != 8:
        errores.append("Verifique los datos del Vendedor (Zonal y DNI 8 dígitos).")
    
    if detalle == "SELECCIONA":
        errores.append("Debe seleccionar un DETALLE.")

    # VALIDACIÓN CONDICIONAL PARA NO-VENTA (Ignora Nombre y DNI)
    if detalle == "NO-VENTA":
        if not motivo_no_venta:
            errores.append("Para NO-VENTA debe elegir un MOTIVO.")
    else:
        # VALIDACIÓN PARA VENTAS Y OTROS
        if not nombre_cliente: errores.append("Nombre de cliente obligatorio.")
        if len(dni_cliente) < 8: errores.append("DNI Cliente inválido.")
        if len(pedido) != 10: errores.append("Pedido debe tener 10 dígitos.")
        if len(cont1) != 9: errores.append("Contacto 1 debe tener 9 dígitos.")

    if errores:
        for e in errores: st.error(e)
    else:
        # HORA LIMA
        peru_tz = pytz.timezone('America/Lima')
        ahora = datetime.now(peru_tz)
        
        # Preparar lista plana para Google Sheets (en orden de columnas)
        fila_excel = [
            ahora.strftime("%d/%m/%Y %H:%M:%S"),
            zonal,
            dni_vendedor,
            detalle,
            tipo_op if detalle != "NO-VENTA" else "N/A",
            nombre_cliente if nombre_cliente else "N/A",
            dni_cliente if dni_cliente else "N/A",
            direccion,
            email,
            cont1,
            cont2,
            producto if detalle != "NO-VENTA" else "N/A",
            cod_fe,
            pedido if detalle != "NO-VENTA" else "0",
            venta_piloto if detalle != "NO-VENTA" else "NO",
            motivo_no_venta if detalle == "NO-VENTA" else "N/A",
            nom_ref,
            cont_ref,
            ahora.strftime("%d/%m/%Y"),
            ahora.strftime("%H:%M:%S")
        ]

        if save_to_google_sheets(fila_excel):
            st.success("✅ ¡Registro exitoso en Google Sheets!")
            st.balloons()
            time.sleep(1)
            reiniciar_formulario()
