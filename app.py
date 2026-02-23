import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz
import time

# --- 1. CONFIGURACIÓN INICIAL ---
st.set_page_config(page_title="Sistema de Registro", layout="centered")

# --- 2. CONEXIÓN A GOOGLE SHEETS ---
def conectar_google():
    # Uso de secrets para seguridad
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
    client = gspread.authorize(creds)
    return client.open("GestionDiaria")

@st.cache_data(ttl=60)
def cargar_maestro():
    try:
        doc = conectar_google()
        ws = doc.worksheet("Estructura")
        data = ws.get_all_values()
        df = pd.DataFrame(data[1:], columns=data[0])
        # Limpieza de DNI: Solo números y 8 dígitos
        df['DNI'] = df['DNI'].astype(str).str.replace(r'[^0-9]', '', regex=True).str.zfill(8)
        return df
    except Exception as e:
        st.error(f"Error cargando base maestra: {e}")
        return pd.DataFrame()

# --- 3. LÓGICA DE SESIÓN Y VLOOKUP ---
if "form_key" not in st.session_state: st.session_state.form_key = 0
if "dni_guardado" not in st.session_state: st.session_state.dni_guardado = ""

df_maestro = cargar_maestro()

# Sidebar para identificación
st.sidebar.title("👤 Vendedor")
dni_input = st.sidebar.text_input("DNI VENDEDOR", value=st.session_state.dni_guardado, max_chars=8)
st.session_state.dni_guardado = dni_input

# Simulación de VLOOKUP
dni_clean = "".join(filter(str.isdigit, dni_input)).zfill(8)
vendedor = df_maestro[df_maestro['DNI'] == dni_clean] if not df_maestro.empty else pd.DataFrame()

if not vendedor.empty and len(dni_input) == 8:
    supervisor_fijo = vendedor.iloc[0]['SUPERVISOR']
    zonal_fija = vendedor.iloc[0]['ZONAL']
    nombre_v = vendedor.iloc[0]['NOMBRE VENDEDOR']
    st.sidebar.success(f"✅ {nombre_v}")
    st.sidebar.info(f"📍 {zonal_fija} | 👤 {supervisor_fijo}")
else:
    supervisor_fijo = "N/A"
    zonal_fija = "SELECCIONA"
    nombre_v = "N/A"
    if len(dni_input) == 8:
        st.sidebar.warning("⚠️ DNI no hallado")

# --- 4. FORMULARIO ÚNICO ---
st.title("📝 Registro de Gestión")
detalle = st.selectbox("DETALLE DE GESTIÓN *", ["SELECCIONA", "VENTA FIJA", "NO-VENTA", "CLIENTE AGENDADO", "REFERIDO"])

with st.form(key=f"f_{st.session_state.form_key}"):
    # 22 Columnas preparadas
    mot_nv = n_cl = d_cl = t_op = prod = mail = dire = c1 = c2 = fe = n_ref = c_ref = "N/A"
    ped = "0"; pil = "NO"

    if detalle == "NO-VENTA":
        # Instrucción: Si es NO-VENTA, solo debe llenar el motivo
        mot_nv = st.selectbox("MOTIVO *", ["SELECCIONA", "COMPETENCIA", "MALA EXPERIENCIA", "CARGO ALTO", "SIN COBERTURA"])
    elif detalle == "REFERIDO":
        n_ref = st.text_input("NOMBRE REFERIDO").upper()
        c_ref = st.text_input("CONTACTO REFERIDO", max_chars=9)
    elif detalle != "SELECCIONA":
        c_a, c_b = st.columns(2)
        with c_a:
            n_cl = st.text_input("NOMBRE CLIENTE").upper()
            d_cl = st.text_input("DNI CLIENTE", max_chars=8)
            t_op = st.selectbox("OPERACIÓN", ["SELECCIONA", "CAPTACIÓN", "MIGRACIÓN", "ALTA"])
        with c_b:
            prod = st.selectbox("PRODUCTO", ["SELECCIONA", "BA", "DUO", "TRIO"])
            ped = st.text_input("PEDIDO", max_chars=10)
            c1 = st.text_input("CELULAR", max_chars=9)

    enviar = st.form_submit_button("🚀 GUARDAR REGISTRO", use_container_width=True)

# --- 5. ACCIÓN DE GUARDADO ---
if enviar:
    if supervisor_fijo == "N/A":
        st.error("❌ Identificación requerida.")
    elif detalle == "SELECCIONA":
        st.error("⚠️ Elige el detalle.")
    else:
        try:
            tz = pytz.timezone('America/Lima')
            ahora = datetime.now(tz)
            fila = [
                ahora.strftime("%d/%m/%Y %H:%M:%S"), zonal_fija, f"'{dni_clean}",
                nombre_v, supervisor_fijo, detalle, t_op, n_cl, f"'{d_cl}", 
                dire, mail, f"'{c1}", f"'{c2}", prod, fe, f"'{ped}", 
                pil, mot_nv, n_ref, f"'{c_ref}", ahora.strftime("%d/%m/%Y"), 
                ahora.strftime("%H:%M:%S")
            ]
            conectar_google().sheet1.append_row(fila, value_input_option='USER_ENTERED')
            st.success("✅ Guardado exitoso")
            st.balloons()
            time.sleep(1)
            st.session_state.form_key += 1
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")
