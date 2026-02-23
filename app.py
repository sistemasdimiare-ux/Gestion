import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz
import time

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Sistema de Ventas Pro", layout="wide")

# --- 2. CONEXIÓN A GOOGLE SHEETS ---
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

@st.cache_data(ttl=60)
def cargar_datos_completos():
    try:
        doc = conectar_google()
        # Cargar Estructura (Vendedores y Supervisores)
        ws_est = doc.worksheet("Estructura")
        data_est = ws_est.get_all_values()
        df_est = pd.DataFrame(data_est[1:], columns=data_est[0])
        # Limpiamos columnas fantasmas y DNI (solo números y 8 dígitos)
        df_est = df_est.loc[:, ~df_est.columns.str.contains('^$|^Unnamed')]
        df_est['DNI'] = df_est['DNI'].astype(str).str.replace(r'\D', '', regex=True).str.zfill(8)

        # Cargar Gestiones ya realizadas
        ws_gest = doc.sheet1
        df_gest = pd.DataFrame(ws_gest.get_all_records())
        return df_est, df_gest
    except Exception as e:
        st.error(f"Error al cargar datos de Google Sheets: {e}")
        return pd.DataFrame(), pd.DataFrame()

# --- 3. LÓGICA DE IDENTIFICACIÓN ---
if "form_key" not in st.session_state: st.session_state.form_key = 0
df_maestro, df_gestiones = cargar_datos_completos()

# Sidebar para el DNI (Disponible en ambas pestañas)
st.sidebar.title("👤 Identificación")
dni_input = st.sidebar.text_input("INGRESE SU DNI VENDEDOR", max_chars=8)
dni_limpio = "".join(filter(str.isdigit, dni_input)).zfill(8)

vendedor_info = df_maestro[df_maestro['DNI'] == dni_limpio] if not df_maestro.empty else pd.DataFrame()

if not vendedor_info.empty and len(dni_input) == 8:
    supervisor_fijo = vendedor_info.iloc[0]['SUPERVISOR']
    zonal_fija = vendedor_info.iloc[0]['ZONAL']
    nombre_vend = vendedor_info.iloc[0]['NOMBRE VENDEDOR']
    st.sidebar.success(f"✅ Hola {nombre_vend}")
    st.sidebar.info(f"📍 Zonal: {zonal_fija}\n👤 Sup: {supervisor_fijo}")
else:
    supervisor_fijo = "N/A"
    zonal_fija = "SELECCIONA"
    nombre_vend = "N/A"
    if len(dni_input) == 8:
        st.sidebar.warning("⚠️ DNI no encontrado en la base.")

# --- 4. DISEÑO DE PESTAÑAS ---
tab_registro, tab_dashboard = st.tabs(["📝 REGISTRO DE GESTIÓN", "📊 DASHBOARD COMERCIAL"])

# --- PESTAÑA 1: FORMULARIO ---
with tab_registro:
    st.title("📝 Registro de Gestión Diaria")
    detalle = st.selectbox("DETALLE DE GESTIÓN *", ["SELECCIONA", "VENTA FIJA", "NO-VENTA", "CLIENTE AGENDADO", "REFERIDO", "PRE-VENTA"])

    with st.form(key=f"main_form_{st.session_state.form_key}"):
        # Variables por defecto
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
                t_op = st.selectbox("OPERACIÓN", ["SELECCIONA", "CAPTACIÓN", "MIGRACIÓN", "ALTA"])
                prod = st.selectbox("PRODUCTO", ["SELECCIONA", "BA", "DUO", "TRIO"])
                pedido = st.text_input("PEDIDO (10)", max_chars=10)
            with col2:
                fe = st.text_input("CÓDIGO FE")
                dire = st.text_input("DIRECCIÓN").upper()
                c1 = st.text_input("CONTACTO 1 (9)", max_chars=9)
                mail = st.text_input("EMAIL")
                piloto = st.radio("¿PILOTO?", ["SI", "NO"], index=1, horizontal=True)

        enviar = st.form_submit_button("🚀 REGISTRAR GESTIÓN", use_container_width=True)

    if enviar:
        if supervisor_fijo == "N/A":
            st.error("❌ No puedes registrar sin un DNI válido.")
        elif detalle == "SELECCIONA":
            st.error("⚠️ Selecciona un detalle de gestión.")
        elif detalle == "NO-VENTA" and motivo_nv == "SELECCIONA":
            st.error("⚠️ Selecciona el motivo de no venta.")
        else:
            tz = pytz.timezone('America/Lima')
            marca = datetime.now(tz)
            
            # Recordatorio: El DNI y Zonal del vendedor no se reescriben manualmente
            fila = [
                marca.strftime("%d/%m/%Y %H:%M:%S"), zonal_fija, f"'{dni_limpio}",
                nombre_vend, supervisor_fijo, detalle, t_op, nombre, f"'{dni_c}", 
                dire, mail, f"'{c1}", f"'{c2}", prod, fe, f"'{pedido}", 
                piloto, motivo_nv, n_ref, f"'{c_ref}", 
                marca.strftime("%d/%m/%Y"), marca.strftime("%H:%M:%S")
            ]
            
            if save_to_google_sheets(fila):
                st.success(f"✅ Registrado con éxito para el Supervisor {supervisor_fijo}")
                st.balloons()
                time.sleep(2)
                st.session_state.form_key += 1
                st.rerun()

# --- PESTAÑA 2: DASHBOARD ---
with tab_dashboard:
    st.title("📊 Dashboard de Rendimiento")
    
    if df_gestiones.empty:
        st.info("No hay datos registrados todavía.")
    else:
        # Filtros de Dashboard
        f1, f2 = st.columns(2)
        with f1:
            z_filtro = st.multiselect("Filtrar por Zonal", options=df_gestiones['ZONAL'].unique())
        with f2:
            s_filtro = st.multiselect("Filtrar por Supervisor", options=df_gestiones['SUPERVISOR'].unique())

        df_f = df_gestiones.copy()
        if z_filtro: df_f = df_f[df_f['ZONAL'].isin(z_filtro)]
        if s_filtro: df_f = df_f[df_f['SUPERVISOR'].isin(s_filtro)]

        # KPIs
        m1, m2, m3 = st.columns(3)
        ventas_fijas = len(df_f[df_f['DETALLE GESTIÓN'] == 'VENTA FIJA'])
        m1.metric("Total Gestiones", len(df_f))
        m2.metric("Ventas Fijas", ventas_fijas)
        m3.metric("% Efectividad", f"{round(ventas_fijas/len(df_f)*100, 1) if len(df_f)>0 else 0}%")

        # Gráficos
        g1, g2 = st.columns(2)
        with g1:
            st.subheader("Ventas por Supervisor")
            df_v = df_f[df_f['DETALLE GESTIÓN'] == 'VENTA FIJA']
            if not df_v.empty:
                fig_sup = px.bar(df_v.groupby('SUPERVISOR').size().reset_index(name='Ventas'), 
                                 x='SUPERVISOR', y='Ventas', color='SUPERVISOR', text_auto=True)
                st.plotly_chart(fig_sup, use_container_width=True)
        
        with g2:
            st.subheader("Motivos de No-Venta")
            df_nv = df_f[df_f['DETALLE GESTIÓN'] == 'NO-VENTA']
            if not df_nv.empty:
                fig_nv = px.pie(df_nv.groupby('MOTIVO NO-VENTA').size().reset_index(name='Total'), 
                                names='MOTIVO NO-VENTA', values='Total', hole=0.4)
                st.plotly_chart(fig_nv, use_container_width=True)

        st.subheader("🥇 Top Vendedores")
        ranking = df_f[df_f['DETALLE GESTIÓN'] == 'VENTA FIJA'].groupby(['NOMBRE VENDEDOR', 'SUPERVISOR']).size().reset_index(name='VENTAS').sort_values('VENTAS', ascending=False)
        st.dataframe(ranking, use_container_width=True, hide_index=True)
