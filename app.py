import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz
import time

# --- 1. CONFIGURACIÓN DE PÁGINA (Debe ser lo primero) ---
st.set_page_config(page_title="Sistema de Ventas Pro", layout="wide")

# --- 2. FUNCIONES DE CONEXIÓN Y CARGA ---
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

@st.cache_data(ttl=300)
def cargar_todo():
    try:
        doc = conectar_google()
        # Cargar Estructura (Vendedores/Supervisores)
        ws_est = doc.worksheet("Estructura")
        data_est = ws_est.get_all_values()
        df_est = pd.DataFrame(data_est[1:], columns=data_est[0])
        df_est = df_est.loc[:, ~df_est.columns.str.contains('^$|^Unnamed')]
        df_est['DNI'] = df_est['DNI'].astype(str).str.strip().str.zfill(8)

        # Cargar Gestiones (Ventas realizadas)
        ws_gest = doc.sheet1
        df_gest = pd.DataFrame(ws_gest.get_all_records())
        return df_est, df_gest
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return pd.DataFrame(), pd.DataFrame()

# --- 3. LÓGICA DE IDENTIFICACIÓN (Sidebar) ---
if "form_key" not in st.session_state: st.session_state.form_key = 0
if "dni_fijo" not in st.session_state: st.session_state.dni_fijo = ""

df_maestro, df_gestiones = cargar_todo()

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
    supervisor_fijo = "N/A"
    zonal_fija = "SELECCIONA"
    nombre_vend = "N/A"
    if len(dni_input) == 8:
        st.sidebar.warning("⚠️ DNI no encontrado en Estructura.")

# --- 4. DEFINICIÓN DE PESTAÑAS ---
tab1, tab2 = st.tabs(["📝 REGISTRO DE GESTIÓN", "📊 DASHBOARD DE CONTROL"])

# --- CONTENIDO PESTAÑA 1: FORMULARIO ---
with tab1:
    st.title("📝 Registro de Gestión Diaria")
    detalle = st.selectbox("DETALLE DE GESTIÓN *", ["SELECCIONA", "VENTA FIJA", "NO-VENTA", "CLIENTE AGENDADO", "REFERIDO", "PRE-VENTA"])

    with st.form(key=f"main_f_{st.session_state.form_key}"):
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

    if enviar:
        if supervisor_fijo == "N/A":
            st.error("❌ DNI no validado. Revisa el panel izquierdo.")
        elif detalle == "SELECCIONA":
            st.error("⚠️ Elige un detalle de gestión.")
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
                st.success(f"✅ ¡Guardado! Supervisor: {supervisor_fijo}")
                st.balloons()
                time.sleep(2)
                st.session_state.form_key += 1
                st.rerun()

# --- CONTENIDO PESTAÑA 2: DASHBOARD ---
with tab2:
    st.title("📊 Análisis de Rendimiento")
    
    if df_gestiones.empty:
        st.info("Aún no hay gestiones registradas hoy.")
    else:
        # Filtros rápidos
        st.markdown("### 🔍 Filtros de Supervisor")
        c_f1, c_f2 = st.columns(2)
        with c_f1:
            z_sel = st.multiselect("Zonal", options=df_gestiones['ZONAL'].unique())
        with c_f2:
            s_sel = st.multiselect("Supervisor", options=df_gestiones['SUPERVISOR'].unique())

        df_f = df_gestiones.copy()
        if z_sel: df_f = df_f[df_f['ZONAL'].isin(z_sel)]
        if s_sel: df_f = df_f[df_f['SUPERVISOR'].isin(s_sel)]

        # KPI Cards
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total Gestiones", len(df_f))
        k2.metric("Ventas Fijas", len(df_f[df_f['DETALLE GESTIÓN'] == 'VENTA FIJA']))
        k3.metric("No-Ventas", len(df_f[df_f['DETALLE GESTIÓN'] == 'NO-VENTA']))
        k4.metric("Referidos", len(df_f[df_f['DETALLE GESTIÓN'] == 'REFERIDO']))

        st.markdown("---")
        
        # Gráficos
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.subheader("Ventas por Supervisor")
            df_v = df_f[df_f['DETALLE GESTIÓN'] == 'VENTA FIJA']
            if not df_v.empty:
                fig_sup = px.bar(df_v.groupby('SUPERVISOR').size().reset_index(name='Cant'), 
                                 x='SUPERVISOR', y='Cant', color='SUPERVISOR', text_auto=True)
                st.plotly_chart(fig_sup, use_container_width=True)
            else: st.write("No hay ventas fijas con estos filtros.")

        with col_g2:
            st.subheader("Horas con mayor actividad")
            df_f['Hora_H'] = df_f['HORA'].str.split(':').str[0]
            fig_h = px.line(df_f.groupby('Hora_H').size().reset_index(name='Cant'), 
                            x='Hora_H', y='Cant', markers=True, title="Gestiones por hora")
            st.plotly_chart(fig_h, use_container_width=True)

        st.subheader("🥇 Ranking Vendedores")
        ranking = df_f[df_f['DETALLE GESTIÓN'] == 'VENTA FIJA'].groupby(['NOMBRE VENDEDOR', 'SUPERVISOR']).size().reset_index(name='Ventas').sort_values('Ventas', ascending=False)
        st.dataframe(ranking, use_container_width=True, hide_index=True)
