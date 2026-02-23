import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz
import time

# --- 1. CONEXIÓN A GOOGLE SHEETS ---
def conectar_google():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
    client = gspread.authorize(creds)
    return client.open("GestionDiaria")

@st.cache_data(ttl=60)
def cargar_estructura():
    try:
        doc = conectar_google()
        ws = doc.worksheet("Estructura")
        data = ws.get_all_values()
        df = pd.DataFrame(data[1:], columns=data[0])
        # Limpieza de columnas vacías y normalización de DNI
        df = df.loc[:, ~df.columns.str.contains('^$|^Unnamed')]
        df['DNI'] = df['DNI'].astype(str).str.replace(r'[^0-9]', '', regex=True).str.zfill(8)
        return df
    except Exception as e:
        st.error(f"Error cargando base maestra: {e}")
        return pd.DataFrame()

# --- 2. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Registro de Ventas", layout="centered")

if "form_key" not in st.session_state: st.session_state.form_key = 0
if "dni_fijo" not in st.session_state: st.session_state.dni_fijo = ""

df_maestro = cargar_estructura()

# --- 3. IDENTIFICACIÓN (VLOOKUP) EN SIDEBAR ---
st.sidebar.title("👤 Vendedor")
dni_input = st.sidebar.text_input("DNI VENDEDOR", value=st.session_state.dni_fijo, max_chars=8)
st.session_state.dni_fijo = dni_input

dni_buscado = "".join(filter(str.isdigit, dni_input)).zfill(8)
vendedor_info = df_maestro[df_maestro['DNI'] == dni_buscado] if not df_maestro.empty else pd.DataFrame()

if not vendedor_info.empty and len(dni_input) == 8:
    supervisor_fijo = vendedor_info.iloc[0]['SUPERVISOR']
    zonal_fija = vendedor_info.iloc[0]['ZONAL']
    nombre_vend = vendedor_info.iloc[0]['NOMBRE VENDEDOR']
    st.sidebar.success(f"✅ {nombre_vend}")
    st.sidebar.info(f"📍 {zonal_fija}\n👤 Sup: {supervisor_fijo}")
else:
    supervisor_fijo = "N/A"
    zonal_fija = "SELECCIONA"
    nombre_vend = "N/A"
    if len(dni_input) == 8:
        st.sidebar.warning("⚠️ DNI no registrado")

# --- 4. FORMULARIO DE REGISTRO ---
st.title("📝 Registro de Gestión Diaria")
detalle = st.selectbox("DETALLE DE GESTIÓN *", ["SELECCIONA", "VENTA FIJA", "NO-VENTA", "CLIENTE AGENDADO", "REFERIDO", "PRE-VENTA"])

with st.form(key=f"main_form_{st.session_state.form_key}"):
    # Variables iniciales (22 columnas)
    motivo_nv = nombre = dni_c = t_op = prod = mail = dire = c1 = c2 = fe = n_ref = c_ref = "N/A"
    pedido = "0"; piloto = "NO"

    if detalle == "NO-VENTA":
        # Instrucción: Si es NO-VENTA, solo debe llenar el motivo.
        motivo_nv = st.selectbox("MOTIVO NO-VENTA *", ["SELECCIONA", "COMPETENCIA", "MALA EXPERIENCIA", "CARGO FIJO ALTO", "SIN COBERTURA"])
    
    elif detalle == "REFERIDO":
        n_ref = st.text_input("NOMBRE REFERIDO").upper()
        c_ref = st.text_input("CONTACTO REFERIDO", max_chars=9)
    
    elif detalle != "SELECCIONA":
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("NOMBRE CLIENTE").upper()
            dni_c = st.text_input("DNI CLIENTE", max_chars=8)
            t_op = st.selectbox("OPERACIÓN", ["SELECCIONA", "CAPTACIÓN", "MIGRACIÓN", "ALTA"])
            prod = st.selectbox("PRODUCTO", ["SELECCIONA", "BA", "DUO", "TRIO"])
        with col2:
            fe = st.text_input("CÓDIGO FE")
            dire = st.text_input("DIRECCIÓN").upper()
            c1 = st.text_input("CELULAR 1", max_chars=9)
            pedido = st.text_input("N° PEDIDO", max_chars=10)
            piloto = st.radio("¿PILOTO?", ["SI", "NO"], index=1, horizontal=True)

    enviar = st.form_submit_button("🚀 GUARDAR GESTIÓN", use_container_width=True)

# --- 5. LÓGICA DE GUARDADO ---
if enviar:
    if supervisor_fijo == "N/A":
        st.error("❌ Identificación inválida.")
    elif detalle == "SELECCIONA":
        st.error("⚠️ Elige un detalle de gestión.")
    else:
        try:
            tz = pytz.timezone('America/Lima')
            ahora = datetime.now(tz)
            
            # Fila exacta de 22 columnas
            fila = [
                ahora.strftime("%d/%m/%Y %H:%M:%S"), # A: Marca Temporal
                zonal_fija,                          # B: Zonal
                f"'{dni_buscado}",                  # C: DNI Vendedor
                nombre_vend,                         # D: Nombre Vendedor
                supervisor_fijo,                     # E: Supervisor
                detalle,                             # F: Detalle Gestión
                t_op,                                # G: Tipo Operación
                nombre,                              # H: Nombre Cliente
                f"'{dni_c}",                         # I: DNI Cliente
                dire,                                # J: Dirección
                mail,                                # K: Email
                f"'{c1}",                            # L: Contacto 1
                f"'{c2}",                            # M: Contacto 2
                prod,                                # N: Producto
                fe,                                  # O: Código FE
                f"'{pedido}",                        # P: Pedido
                piloto,                              # Q: Piloto
                motivo_nv,                           # R: Motivo No-Venta
                n_ref,                               # S: Nombre Referido
                f"'{c_ref}",                         # T: Contacto Referido
                ahora.strftime("%d/%m/%Y"),          # U: Fecha
                ahora.strftime("%H:%M:%S")           # V: Hora
            ]
            
            doc = conectar_google()
            doc.sheet1.append_row(fila, value_input_option='USER_ENTERED')
            
            st.success("✅ ¡Guardado correctamente!")
            st.balloons()
            time.sleep(2)
            st.session_state.form_key += 1
            st.rerun()
            
        except Exception as e:
            st.error(f"Error al guardar: {e}")
