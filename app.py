import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz
import time

# Intento de importación segura de Plotly para evitar que la app caiga
try:
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Gestión Comercial Pro", layout="wide")

# --- 2. FUNCIONES DE CONEXIÓN Y CARGA ---
def conectar_google():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
    client = gspread.authorize(creds)
    return client.open("GestionDiaria")

@st.cache_data(ttl=60)
def cargar_datos_completos():
    try:
        doc = conectar_google()
        # Carga pestaña Estructura
        ws_est = doc.worksheet("Estructura")
        data_est = ws_est.get_all_values()
        df_est = pd.DataFrame(data_est[1:], columns=data_est[0])
        
        # Limpieza de columnas vacías y DNI (Inmune a espacios o símbolos)
        df_est = df_est.loc[:, ~df_est.columns.str.contains('^$|^Unnamed')]
        df_est['DNI'] = df_est['DNI'].astype(str).str.replace(r'[^0-9]', '', regex=True).str.zfill(8)
        
        # Carga pestaña Sheet1 (Gestiones)
        ws_gest = doc.sheet1
        df_gest = pd.DataFrame(ws_gest.get_all_records())
        return df_est, df_gest
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return pd.DataFrame(), pd.DataFrame()

# --- 3. LÓGICA DE IDENTIFICACIÓN ---
if "form_key" not in st.session_state: st.session_state.form_key = 0
df_maestro, df_gestiones = cargar_datos_completos()

st.sidebar.title("👤 Identificación")
dni_input = st.sidebar.text_input("INGRESE SU DNI VENDEDOR", max_chars=8)
dni_limpio = "".join(filter(str.isdigit, dni_input)).zfill(8)

vendedor_info = df_maestro[df_maestro['DNI'] == dni_limpio] if not df_maestro.empty else pd.DataFrame()

if not vendedor_info.empty and len(dni_input) == 8:
    supervisor_fijo = vendedor_info.iloc[0]['SUPERVISOR']
    zonal_fija = vendedor_info.iloc[0]['ZONAL']
    nombre_vend = vendedor_info.iloc[0]['NOMBRE VENDEDOR']
    st.sidebar.success(f"✅ Hola {nombre_vend}")
    st.sidebar.info(f"📍 Zonal: {zonal_fija}\n\n👤 Sup: {supervisor_fijo}")
else:
    supervisor_fijo = "N/A"; zonal_fija = "SELECCIONA"; nombre_vend = "N/A"
    if len(dni_input) == 8:
        st.sidebar.warning("⚠️ DNI no encontrado en Estructura.")

# --- 4. DISEÑO POR PESTAÑAS (TABS) ---
tab_reg, tab_dash = st.tabs(["📝 REGISTRO DE GESTIÓN", "📊 DASHBOARD COMERCIAL"])

with tab_reg:
    st.title("📝 Registro de Gestión Diaria")
    detalle = st.selectbox("DETALLE DE GESTIÓN *", ["SELECCIONA", "VENTA FIJA", "NO-VENTA", "CLIENTE AGENDADO", "REFERIDO", "PRE-VENTA"])

    with st.form(key=f"main_f_{st.session_state.form_key}"):
        # Variables para las 22 columnas
        mot_nv = nom = d_cl = t_op = prod = mail = dire = c1 = c2 = fe = n_ref = c_ref = "N/A"
        ped = "0"; pil = "NO"

        if detalle == "NO-VENTA":
            mot_nv = st.selectbox("MOTIVO *", ["SELECCIONA", "COMPETENCIA", "MALA EXPERIENCIA", "CARGO ALTO", "SIN COBERTURA"])
        elif detalle == "REFERIDO":
            n_ref = st.text_input("NOMBRE REFERIDO").upper()
            c_ref = st.text_input("CONTACTO REFERIDO", max_chars=9)
        elif detalle != "SELECCIONA":
            c_l1, c_l2 = st.columns(2)
            with c_l1:
                nom = st.text_input("CLIENTE").upper()
                d_cl = st.text_input("DNI CLIENTE", max_chars=8)
                t_op = st.selectbox("OPERACIÓN", ["SELECCIONA", "CAPTACIÓN", "MIGRACIÓN", "ALTA"])
            with c_l2:
                prod = st.selectbox("PRODUCTO", ["SELECCIONA", "BA", "DUO", "TRIO"])
                fe = st.text_input("CÓDIGO FE")
                ped = st.text_input("PEDIDO", max_chars=10)
                c1 = st.text_input("CELULAR", max_chars=9)
                pil = st.radio("¿PILOTO?", ["SI", "NO"], index=1, horizontal=True)

        enviar = st.form_submit_button("🚀 REGISTRAR GESTIÓN", use_container_width=True)

    if enviar:
        if supervisor_fijo == "N/A":
            st.error("❌ DNI no validado. Revisa el panel izquierdo.")
        elif detalle == "SELECCIONA":
            st.error("⚠️ Elige un detalle.")
        else:
            tz = pytz.timezone('America/Lima')
            marca = datetime.now(tz)
            # El vendedor no debe reescribir su dni y zonal; si es NO-VENTA solo llena el motivo.
            fila = [
                marca.strftime("%d/%m/%Y %H:%M:%S"), zonal_fija, f"'{dni_limpio}",
                nombre_vend, supervisor_fijo, detalle, t_op, nom, f"'{d_cl}", 
                dire, mail, f"'{c1}", f"'{c2}", prod, fe, f"'{ped}", 
                pil, mot_nv, n_ref, f"'{c_ref}", 
                marca.strftime("%d/%m/%Y"), marca.strftime("%H:%M:%S")
            ]
            try:
                conectar_google().sheet1.append_row(fila, value_input_option='USER_ENTERED')
                st.success(f"✅ ¡Guardado!")
                st.balloons()
                time.sleep(2)
                st.session_state.form_key += 1
                st.rerun()
            except Exception as e:
                st.error(f"Error al guardar: {e}")

with tab_dash:
    st.title("📊 Dashboard de Rendimiento")
    if not PLOTLY_AVAILABLE:
        st.error("❌ Librería Plotly no instalada en el servidor.")
    
    if df_gestiones.empty:
        st.info("No hay datos registrados.")
    else:
        # Filtros básicos
        s_f = st.multiselect("Supervisor", options=df_gestiones['SUPERVISOR'].unique())
        df_f = df_gestiones.copy()
        if s_f: df_f = df_f[df_f['SUPERVISOR'].isin(s_f)]

        if PLOTLY_AVAILABLE:
            df_v = df_f[df_f['DETALLE GESTIÓN'] == 'VENTA FIJA']
            if not df_v.empty:
                fig = px.bar(df_v.groupby('SUPERVISOR').size().reset_index(name='V'), x='SUPERVISOR', y='V', title="Ventas")
                st.plotly_chart(fig, use_container_width=True)
        
        st.dataframe(df_f, use_container_width=True)
