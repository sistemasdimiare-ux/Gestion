import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz
import time

# Intento de importación segura de Plotly
try:
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Sistema Ventas Pro", layout="wide")

# --- 2. CONEXIÓN ---
def conectar_google():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
    return gspread.authorize(creds).open("GestionDiaria")

@st.cache_data(ttl=60)
def cargar_todo_seguro():
    try:
        doc = conectar_google()
        # Estructura (Vendedores)
        ws_est = doc.worksheet("Estructura")
        data_est = ws_est.get_all_values()
        df_e = pd.DataFrame(data_est[1:], columns=data_est[0])
        # Limpieza radical de DNI: elimina cualquier cosa que no sea número
        df_e['DNI'] = df_e['DNI'].astype(str).str.replace(r'\D', '', regex=True).str.zfill(8)
        
        # Gestiones (Sheet1)
        ws_gest = doc.sheet1
        df_g = pd.DataFrame(ws_gest.get_all_records())
        return df_e, df_g
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return pd.DataFrame(), pd.DataFrame()

# --- 3. LÓGICA DE IDENTIFICACIÓN ---
if "form_key" not in st.session_state: st.session_state.form_key = 0

df_maestro, df_gestiones = cargar_todo_seguro()

st.sidebar.title("👤 Identificación")
dni_raw = st.sidebar.text_input("INGRESE SU DNI VENDEDOR", max_chars=8)
# Limpiamos lo que el usuario escribe para comparar peras con peras
dni_limpio = "".join(filter(str.isdigit, dni_raw)).zfill(8)

vendedor_info = df_maestro[df_maestro['DNI'] == dni_limpio] if not df_maestro.empty else pd.DataFrame()

if not vendedor_info.empty and len(dni_raw) == 8:
    supervisor_fijo = vendedor_info.iloc[0]['SUPERVISOR']
    zonal_fija = vendedor_info.iloc[0]['ZONAL']
    nombre_vend = vendedor_info.iloc[0]['NOMBRE VENDEDOR']
    st.sidebar.success(f"✅ Hola {nombre_vend}")
    st.sidebar.info(f"📍 {zonal_fija} | 👤 {supervisor_fijo}")
else:
    supervisor_fijo = "N/A"
    zonal_fija = "SELECCIONA"
    nombre_vend = "N/A"
    if len(dni_raw) == 8:
        st.sidebar.warning("⚠️ DNI no hallado. Revisa que esté en la pestaña 'Estructura'.")

# --- 4. PESTAÑAS ---
tab1, tab2 = st.tabs(["📝 REGISTRO", "📊 DASHBOARD"])

with tab1:
    st.title("Registro de Gestión")
    detalle = st.selectbox("DETALLE DE GESTIÓN *", ["SELECCIONA", "VENTA FIJA", "NO-VENTA", "CLIENTE AGENDADO", "REFERIDO"])

    with st.form(key=f"form_{st.session_state.form_key}"):
        # Campos inicializados
        m_nv = n_cl = d_cl = t_op = prod = dir_cl = c_fe = n_ref = c_ref = "N/A"
        ped = "0"; mail = "N/A"; c1 = c2 = "N/A"; pil = "NO"

        if detalle == "NO-VENTA":
            m_nv = st.selectbox("MOTIVO *", ["SELECCIONA", "COMPETENCIA", "MALA EXPERIENCIA", "CARGO ALTO", "SIN COBERTURA"])
        elif detalle == "REFERIDO":
            n_ref = st.text_input("NOMBRE REFERIDO").upper()
            c_ref = st.text_input("CONTACTO REFERIDO", max_chars=9)
        elif detalle != "SELECCIONA":
            c_a, c_b = st.columns(2)
            n_cl = c_a.text_input("CLIENTE").upper()
            d_cl = c_a.text_input("DNI CLIENTE", max_chars=8)
            t_op = c_a.selectbox("OPERACIÓN", ["CAPTACIÓN", "MIGRACIÓN", "ALTA"])
            ped = c_b.text_input("PEDIDO", max_chars=10)
            c_fe = c_b.text_input("CÓDIGO FE")
            c1 = c_b.text_input("CELULAR", max_chars=9)

        enviar = st.form_submit_button("🚀 GUARDAR GESTIÓN", use_container_width=True)

    if enviar:
        if supervisor_fijo == "N/A":
            st.error("❌ El DNI debe ser válido para guardar.")
        elif detalle == "SELECCIONA":
            st.error("⚠️ Elige un detalle.")
        else:
            tz = pytz.timezone('America/Lima')
            ahora = datetime.now(tz)
            # Registro según las 22 columnas configuradas
            fila = [
                ahora.strftime("%d/%m/%Y %H:%M:%S"), zonal_fija, f"'{dni_limpio}",
                nombre_vend, supervisor_fijo, detalle, t_op, n_cl, f"'{d_cl}", 
                dir_cl, mail, f"'{c1}", f"'{c2}", prod, c_fe, f"'{ped}", 
                pil, m_nv, n_ref, f"'{c_ref}", ahora.strftime("%d/%m/%Y"), 
                ahora.strftime("%H:%M:%S")
            ]
            
            # Guardado directo
            try:
                conectar_google().sheet1.append_row(fila, value_input_option='USER_ENTERED')
                st.success(f"✅ ¡Guardado! Supervisor: {supervisor_fijo}")
                st.balloons()
                time.sleep(2)
                st.session_state.form_key += 1
                st.rerun()
            except Exception as e:
                st.error(f"Error al guardar: {e}")

with tab2:
    st.title("Dashboard de Control")
    if not PLOTLY_AVAILABLE:
        st.error("❌ La librería Plotly no está instalada. El Dashboard no puede mostrar gráficos.")
        st.info("Asegúrate de haber hecho REBOOT en Streamlit Cloud después de subir el requirements.txt")
    
    if df_gestiones.empty:
        st.info("No hay datos para mostrar.")
    else:
        st.subheader("Resumen de Gestiones")
        st.dataframe(df_gestiones, use_container_width=True)
        
        if PLOTLY_AVAILABLE:
            df_v = df_gestiones[df_gestiones['DETALLE GESTIÓN'] == 'VENTA FIJA']
            if not df_v.empty:
                fig = px.bar(df_v.groupby('SUPERVISOR').size().reset_index(name='Ventas'), 
                             x='SUPERVISOR', y='Ventas', title="Ventas por Supervisor")
                st.plotly_chart(fig, use_container_width=True)
