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

# --- 2. CARGA DE BASE MAESTRA (Lectura flexible desde columna G) ---
@st.cache_data(ttl=300)
def cargar_estructura():
    try:
        doc = conectar_google()
        ws = doc.worksheet("Estructura")
        
        # Obtenemos todos los valores de la pestaña
        data = ws.get_all_values()
        
        # Convertimos a DataFrame usando la primera fila como nombres de columna
        df_completo = pd.DataFrame(data[1:], columns=data[0])
        
        # Eliminamos columnas vacías (esto limpia las columnas A-F si están vacías)
        df_completo = df_completo.loc[:, ~df_completo.columns.str.contains('^$|^Unnamed')]
        
        # Seleccionamos las columnas necesarias. 
        # IMPORTANTE: Los nombres en tu Excel (Fila 1) deben ser exactos.
        columnas_req = ['DNI', 'NOMBRE VENDEDOR', 'SUPERVISOR', 'ZONAL']
        df = df_completo[columnas_req].copy()
        
        # Limpiamos y normalizamos el DNI
        df['DNI'] = df['DNI'].astype(str).str.strip().str.zfill(8)
        return df
    except Exception as e:
        st.error(f"⚠️ Error: No se encontraron las columnas necesarias en 'Estructura'. Verifica que los nombres en la Fila 1 sean DNI, NOMBRE VENDEDOR, SUPERVISOR y ZONAL. {e}")
        return pd.DataFrame(columns=['DNI', 'NOMBRE VENDEDOR', 'SUPERVISOR', 'ZONAL'])

# --- 3. CONFIGURACIÓN ---
st.set_page_config(page_title="Sistema de Ventas Pro", layout="wide")

if "form_key" not in st.session_state: st.session_state.form_key = 0
if "dni_fijo" not in st.session_state: st.session_state.dni_fijo = ""

df_maestro = cargar_estructura()

# --- SIDEBAR ---
st.sidebar.title("👤 Identificación")
dni_input = st.sidebar.text_input("INGRESE SU DNI VENDEDOR", value=st.session_state.dni_fijo, max_chars=8)
st.session_state.dni_fijo = dni_input

# Búsqueda de datos del vendedor
dni_buscado = dni_input.strip().zfill(8)
vendedor_info = df_maestro[df_maestro['DNI'] == dni_buscado]

if not vendedor_info.empty and len(dni_input) == 8:
    supervisor_fijo = vendedor_info.iloc[0]['SUPERVISOR']
    zonal_fija = vendedor_info.iloc[0]['ZONAL']
    nombre_vend = vendedor_info.iloc[0]['NOMBRE VENDEDOR']
    st.sidebar.success(f"✅ Hola {nombre_vend}")
    st.sidebar.info(f"📍 Zonal: {zonal_fija}\n\n👤 Sup: {supervisor_fijo}")
else:
    supervisor_fijo = "N/A"
    zonal_fija = "SELECCIONA"
    if len(dni_input) == 8:
        st.sidebar.warning("⚠️ DNI no encontrado en la columna G de Estructura.")

# --- 4. FORMULARIO ---
st.title("📝 Registro de Gestión Diaria")

detalle = st.selectbox("DETALLE DE GESTIÓN *", ["SELECCIONA", "VENTA FIJA", "NO-VENTA", "CLIENTE AGENDADO", "REFERIDO", "PRE-VENTA"])

with st.form(key=f"main_f_{st.session_state.form_key}"):
    # Variables iniciales (Evita el ValueError de las imágenes anteriores)
    motivo_nv = nombre = dni_c = t_op = prod = mail = dire = c1 = c2 = fe = n_ref = c_ref = "N/A"
    pedido = "0"; piloto = "NO"

    if detalle == "NO-VENTA":
        st.subheader("Opciones de No-Venta")
        motivo_nv = st.selectbox("MOTIVO *", ["SELECCIONA", "COMPETENCIA", "CLIENTE MOVISTAR", "MALA EXPERIENCIA", "CARGO FIJO ALTO", "SIN COBERTURA"])
    
    elif detalle == "REFERIDO":
        st.subheader("Datos del Referido")
        r1, r2 = st.columns(2)
        n_ref = r1.text_input("NOMBRE REFERIDO").upper()
        c_ref = r2.text_input("CONTACTO REFERIDO (9)", max_chars=9)
    
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
            mail = st.text_input("EMAIL")
            dire = st.text_input("DIRECCIÓN").upper()
            c1 = st.text_input("CONTACTO 1 (9)", max_chars=9)
            c2 = st.text_input("CONTACTO 2 (9)", max_chars=9)
            piloto = st.radio("¿PILOTO?", ["SI", "NO"], index=1, horizontal=True)

    enviar = st.form_submit_button("🚀 REGISTRAR GESTIÓN", use_container_width=True)

# --- 5. ENVÍO ---
if enviar:
    if supervisor_fijo == "N/A":
        st.error("❌ DNI no validado. Asegúrate de estar registrado en la Estructura.")
    elif detalle == "SELECCIONA":
        st.error("⚠️ Elige un detalle de gestión.")
    else:
        tz = pytz.timezone('America/Lima')
        marca = datetime.now(tz)
        
        # Preparamos la fila con TODA la información del vendedor
        # Ahora incluimos Nombre, Supervisor y Zonal en cada registro
        fila = [
            marca.strftime("%d/%m/%Y %H:%M:%S"), # A: Fecha y Hora
            zonal_fija,                         # B: Zonal
            f"'{st.session_state.dni_fijo}",    # C: DNI Vendedor (con ')
            nombre_vend,                        # D: Nombre Vendedor (NUEVO)
            supervisor_fijo,                    # E: Supervisor (NUEVO)
            detalle,                            # F: Detalle de Gestión
            t_op,                               # G: Tipo Operación
            nombre,                             # H: Nombre Cliente
            f"'{dni_c}",                        # I: DNI Cliente (con ')
            dire,                               # J: Dirección
            mail,                               # K: Email
            f"'{c1}",                           # L: Contacto 1
            f"'{c2}",                           # M: Contacto 2
            prod,                               # N: Producto
            fe,                                 # O: Código FE
            f"'{pedido}",                       # P: Pedido
            piloto,                             # Q: Piloto
            motivo_nv,                          # R: Motivo No-Venta
            n_ref,                              # S: Nombre Referido
            f"'{c_ref}",                        # T: Contacto Referido
            marca.strftime("%d/%m/%Y"),         # U: Fecha solo
            marca.strftime("%H:%M:%S")          # V: hora solo
        ]

        if save_to_google_sheets(fila):
            st.success(f"✅ Gestión registrada para {nombre_vend} (Sup: {supervisor_fijo})")
            st.balloons()
            time.sleep(2)
            st.session_state.form_key += 1
            st.rerun()

