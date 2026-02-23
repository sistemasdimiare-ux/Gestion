import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz
import time

# --- 1. CONEXIÓN ---
def conectar_google():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
        client = gspread.authorize(creds)
        return client.open("GestionDiaria")
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None

def save_to_google_sheets(datos_fila):
    try:
        doc = conectar_google()
        if doc:
            sheet = doc.sheet1
            sheet.append_row(datos_fila, value_input_option='USER_ENTERED')
            return True
        return False
    except Exception as e:
        st.error(f"❌ Error al guardar: {e}")
        return False

# --- 2. CARGA DE BASE MAESTRA ---
@st.cache_data(ttl=300)
def cargar_estructura():
    try:
        doc = conectar_google()
        if not doc: return pd.DataFrame()
        ws = doc.worksheet("Estructura")
        data = ws.get_all_values()
        
        df_completo = pd.DataFrame(data[1:], columns=data[0])
        # Limpiar columnas fantasma
        df_completo = df_completo.loc[:, ~df_completo.columns.str.contains('^$|^Unnamed')]
        
        # NORMALIZACIÓN CRÍTICA DE DNI: Quita espacios y asegura 8 dígitos
        df_completo['DNI'] = df_completo['DNI'].astype(str).str.replace(r'[^0-9]', '', regex=True).str.zfill(8)
        
        return df_completo[['DNI', 'NOMBRE VENDEDOR', 'SUPERVISOR', 'ZONAL']].copy()
    except Exception as e:
        st.error(f"⚠️ Error en pestaña Estructura: {e}")
        return pd.DataFrame(columns=['DNI', 'NOMBRE VENDEDOR', 'SUPERVISOR', 'ZONAL'])

# --- 3. CONFIGURACIÓN DE LA WEB ---
st.set_page_config(page_title="Sistema de Ventas Pro", layout="wide")

if "form_key" not in st.session_state: st.session_state.form_key = 0
if "dni_fijo" not in st.session_state: st.session_state.dni_fijo = ""

df_maestro = cargar_estructura()

# --- SIDEBAR (IDENTIFICACIÓN) ---
st.sidebar.title("👤 Identificación")
dni_input = st.sidebar.text_input("INGRESE SU DNI VENDEDOR", value=st.session_state.dni_fijo, max_chars=8)
st.session_state.dni_fijo = dni_input

dni_buscado = dni_input.strip().zfill(8)
vendedor_info = df_maestro[df_maestro['DNI'] == dni_buscado] if not df_maestro.empty else pd.DataFrame()

if not vendedor_info.empty and len(dni_input) == 8:
    supervisor_fijo = vendedor_info.iloc[0]['SUPERVISOR']
    zonal_fija = vendedor_info.iloc[0]['ZONAL']
    nombre_vend = vendedor_info.iloc[0]['NOMBRE VENDEDOR']
    st.sidebar.success(f"✅ Hola {nombre_vend}")
    st.sidebar.info(f"📍 Zonal: {zonal_fija}\n\n👤 Sup: {supervisor_fijo}")
else:
    supervisor_fijo = "N/A"; zonal_fija = "SELECCIONA"; nombre_vend = "N/A"
    if len(dni_input) == 8:
        st.sidebar.warning("⚠️ DNI no encontrado. Revisa la pestaña 'Estructura'.")

# --- 4. FORMULARIO ---
st.title("📝 Registro de Gestión Diaria")
detalle = st.selectbox("DETALLE DE GESTIÓN *", ["SELECCIONA", "VENTA FIJA", "NO-VENTA", "CLIENTE AGENDADO", "REFERIDO", "PRE-VENTA"])

with st.form(key=f"main_f_{st.session_state.form_key}"):
    # Variables iniciales (22 columnas en total)
    motivo_nv = nombre = dni_c = t_op = prod = mail = dire = c1 = c2 = fe = n_ref = c_ref = "N/A"
    pedido = "0"; piloto = "NO"

    if detalle == "NO-VENTA":
        # Instrucción: Si es NO-VENTA, solo debe llenar el motivo.
        motivo_nv = st.selectbox("MOTIVO *", ["SELECCIONA", "COMPETENCIA", "CLIENTE MOVISTAR", "MALA EXPERIENCIA", "CARGO FIJO ALTO", "SIN COBERTURA"])
    
    elif detalle == "REFERIDO":
        n_ref = st.text_input("NOMBRE REFERIDO").upper()
        c_ref = st.text_input("CONTACTO REFERIDO (9)", max_chars=9)
    
    elif detalle != "SELECCIONA":
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("NOMBRE CLIENTE").upper()
            dni_c = st.text_input("DNI CLIENTE (8)", max_chars=8)
            t_op = st.selectbox("OPERACIÓN", ["SELECCIONA", "CAPTACIÓN", "MIGRACIÓN", "ALTA"])
            prod = st.selectbox("PRODUCTO", ["SELECCIONA", "NAKED", "DUO", "TRIO"])
            pedido = st.text_input("PEDIDO (10)", max_chars=10)
        with col2:
            fe = st.text_input("CÓDIGO FE")
            dire = st.text_input("DIRECCIÓN").upper()
            mail = st.text_input("EMAIL")
            c1 = st.text_input("CONTACTO 1 (9)", max_chars=9)
            piloto = st.radio("¿PILOTO?", ["SI", "NO"], index=1, horizontal=True)

    enviar = st.form_submit_button("🚀 REGISTRAR GESTIÓN", use_container_width=True)

# --- 5. LÓGICA DE ENVÍO ---
if enviar:
    if supervisor_fijo == "N/A":
        st.error("❌ DNI no validado.")
    elif detalle == "SELECCIONA":
        st.error("⚠️ Elige un detalle.")
    else:
        tz = pytz.timezone('America/Lima')
        marca = datetime.now(tz)
        
        # Estructura exacta de 22 columnas (A hasta V)
        fila = [
            marca.strftime("%d/%m/%Y %H:%M:%S"), # A: Marca Temporal
            zonal_fija,                          # B: Zonal
            f"'{dni_buscado}",                  # C: DNI Vendedor
            nombre_vend,                         # D: Nombre Vendedor
            supervisor_fijo,                     # E: Supervisor
            detalle,                             # F: Detalle Gestión
            t_op,                                # G: Operación
            nombre,                              # H: Nombre Cliente
            f"'{dni_c}",                         # I: DNI Cliente
            dire,                                # J: Dirección
            mail,                                # K: Email
            f"'{c1}",                            # L: Contacto 1
            f"'{c2}",                            # M: Contacto 2
            prod,                                # N: Producto
            fe,                                  # O: FE
            f"'{pedido}",                        # P: Pedido
            piloto,                              # Q: Piloto
            motivo_nv,                           # R: Motivo No-Venta
            n_ref,                               # S: Nombre Referido
            f"'{c_ref}",                         # T: Contacto Referido
            marca.strftime("%d/%m/%Y"),          # U: Fecha
            marca.strftime("%H:%M:%S")           # V: Hora
        ]

        if save_to_google_sheets(fila):
            st.success(f"✅ Gestión guardada para {nombre_vend}")
            st.balloons()
            time.sleep(2)
            st.session_state.form_key += 1
            st.rerun()
