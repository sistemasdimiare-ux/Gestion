import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz
import time

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Sistema Ventas Pro", layout="wide")

# --- 2. CONEXIÓN Y CARGA ---
def conectar_google():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
    return gspread.authorize(creds).open("GestionDiaria")

@st.cache_data(ttl=60)
def cargar_datos_completos():
    try:
        doc = conectar_google()
        # Carga Estructura
        ws_est = doc.worksheet("Estructura")
        data_est = ws_est.get_all_values()
        df_est = pd.DataFrame(data_est[1:], columns=data_est[0])
        df_est = df_est.loc[:, ~df_est.columns.str.contains('^$|^Unnamed')]
        # Limpieza total de DNI (quita espacios, saltos de línea y asegura 8 dígitos)
        df_est['DNI'] = df_est['DNI'].astype(str).str.replace(r'\s+', '', regex=True).str.zfill(8)
        
        # Carga Gestiones
        ws_gest = doc.sheet1
        df_gest = pd.DataFrame(ws_gest.get_all_records())
        return df_est, df_gest
    except Exception as e:
        st.error(f"Error crítico de carga: {e}")
        return pd.DataFrame(), pd.DataFrame()

# --- 3. IDENTIFICACIÓN (Sidebar) ---
if "form_key" not in st.session_state: st.session_state.form_key = 0
if "dni_fijo" not in st.session_state: st.session_state.dni_fijo = ""

df_maestro, df_gestiones = cargar_datos_completos()

st.sidebar.title("👤 Identificación")
dni_input = st.sidebar.text_input("INGRESE SU DNI VENDEDOR", value=st.session_state.dni_fijo, max_chars=8)
st.session_state.dni_fijo = dni_input

# Búsqueda limpia
dni_limpio = dni_input.strip().zfill(8)
vendedor_info = df_maestro[df_maestro['DNI'] == dni_limpio] if not df_maestro.empty else pd.DataFrame()

if not vendedor_info.empty and len(dni_input) == 8:
    supervisor_fijo = vendedor_info.iloc[0]['SUPERVISOR']
    zonal_fija = vendedor_info.iloc[0]['ZONAL']
    nombre_vend = vendedor_info.iloc[0]['NOMBRE VENDEDOR']
    st.sidebar.success(f"✅ Hola {nombre_vend}")
    st.sidebar.info(f"📍 Zonal: {zonal_fija}\n👤 Sup: {supervisor_fijo}")
else:
    supervisor_fijo = "N/A"; zonal_fija = "SELECCIONA"; nombre_vend = "N/A"
    if len(dni_input) == 8:
        st.sidebar.warning("⚠️ DNI no encontrado. Revisa la pestaña 'Estructura' en tu Excel.")

# --- 4. PESTAÑAS ---
tab_reg, tab_dash = st.tabs(["📝 REGISTRO", "📊 DASHBOARD"])

with tab_reg:
    st.title("Registro de Gestión")
    detalle = st.selectbox("DETALLE DE GESTIÓN *", ["SELECCIONA", "VENTA FIJA", "NO-VENTA", "CLIENTE AGENDADO", "REFERIDO", "PRE-VENTA"])

    with st.form(key=f"f_{st.session_state.form_key}"):
        motivo_nv = nombre = dni_c = t_op = prod = dire = fe = n_ref = c_ref = "N/A"
        pedido = "0"; mail = "N/A"; c1 = c2 = "N/A"; piloto = "NO"

        if detalle == "NO-VENTA":
            motivo_nv = st.selectbox("MOTIVO *", ["SELECCIONA", "COMPETENCIA", "CLIENTE MOVISTAR", "MALA EXPERIENCIA", "CARGO FIJO ALTO", "SIN COBERTURA"])
        elif detalle == "REFERIDO":
            r1, r2 = st.columns(2)
            n_ref = r1.text_input("NOMBRE REFERIDO").upper()
            c_ref = r2.text_input("CONTACTO REFERIDO", max_chars=9)
        elif detalle != "SELECCIONA":
            col1, col2 = st.columns(2)
            with col1:
                nombre = st.text_input("NOMBRE CLIENTE").upper()
                dni_c = st.text_input("DNI CLIENTE", max_chars=8)
                t_op = st.selectbox("OPERACIÓN", ["SELECCIONA", "CAPTACIÓN", "MIGRACIÓN", "ALTA"])
                prod = st.selectbox("PRODUCTO", ["SELECCIONA", "HFC", "FTTH"])
                pedido = st.text_input("PEDIDO", max_chars=10)
            with col2:
                fe = st.text_input("CÓDIGO FE")
                dire = st.text_input("DIRECCIÓN").upper()
                c1 = st.text_input("CELULAR 1", max_chars=9)
                piloto = st.radio("¿PILOTO?", ["SI", "NO"], index=1, horizontal=True)

        btn = st.form_submit_button("🚀 GUARDAR", use_container_width=True)

    if btn:
        if supervisor_fijo == "N/A":
            st.error("❌ El DNI debe estar registrado para guardar.")
        elif detalle == "SELECCIONA":
            st.error("⚠️ Elige el detalle.")
        else:
            tz = pytz.timezone('America/Lima')
            marca = datetime.now(tz)
            fila = [
                marca.strftime("%d/%m/%Y %H:%M:%S"), zonal_fija, f"'{st.session_state.dni_fijo}",
                nombre_vend, supervisor_fijo, detalle, t_op, nombre, f"'{dni_c}", 
                dire, mail, f"'{c1}", f"'{c2}", prod, fe, f"'{pedido}", 
                piloto, motivo_nv, n_ref, f"'{c_ref}", marca.strftime("%d/%m/%Y"), 
                marca.strftime("%H:%M:%S")
            ]
            if save_to_google_sheets(fila):
                st.success("✅ ¡Registrado!")
                st.balloons()
                time.sleep(1)
                st.session_state.form_key += 1
                st.rerun()

with tab_dash:
    st.title("📊 Dashboard")
    if df_gestiones.empty:
        st.info("No hay datos para mostrar.")
    else:
        # Gráfico Ventas por Supervisor
        df_v = df_gestiones[df_gestiones['DETALLE GESTIÓN'] == 'VENTA FIJA']
        if not df_v.empty:
            fig = px.bar(df_v.groupby('SUPERVISOR').size().reset_index(name='Cant'), 
                         x='SUPERVISOR', y='Cant', title="Ventas por Equipo", text_auto=True)
            st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Ranking")
        st.dataframe(df_gestiones, use_container_width=True)
