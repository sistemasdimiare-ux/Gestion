import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz
import time
import plotly.express as px

# --- 1. CONEXIÓN Y CARGA DE DATOS ---
def conectar_google():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
        return gspread.authorize(creds).open("GestionDiaria")
    except:
        return None

@st.cache_data(ttl=60)
def cargar_todo():
    doc = conectar_google()
    if not doc: return pd.DataFrame(), pd.DataFrame()
    
    # Carga Estructura
    ws_est = doc.worksheet("Estructura")
    df_est = pd.DataFrame(ws_est.get_all_values()[1:], columns=ws_est.get_all_values()[0])
    df_est['DNI'] = df_est['DNI'].astype(str).str.replace(r'[^0-9]', '', regex=True).str.zfill(8)
    
    # Carga Gestiones (Sheet1)
    ws_gest = doc.sheet1
    data_gest = ws_gest.get_all_records()
    df_gest = pd.DataFrame(data_gest)
    
    return df_est, df_gest

# --- 2. CONFIGURACIÓN ---
st.set_page_config(page_title="Sistema Comercial Robusto", layout="wide")
df_maestro, df_gestiones = cargar_todo()

# --- 3. SIDEBAR (Vlookup) ---
st.sidebar.title("👤 Panel de Usuario")
dni_input = st.sidebar.text_input("DNI VENDEDOR", max_chars=8)
dni_clean = "".join(filter(str.isdigit, dni_input)).zfill(8)

vendedor = df_maestro[df_maestro['DNI'] == dni_clean] if not df_maestro.empty else pd.DataFrame()

if not vendedor.empty and len(dni_input) == 8:
    sup_fijo = vendedor.iloc[0]['SUPERVISOR']
    zon_fija = vendedor.iloc[0]['ZONAL']
    nom_v = vendedor.iloc[0]['NOMBRE VENDEDOR']
    st.sidebar.success(f"✅ Bienvenido, {nom_v}")
else:
    sup_fijo = "N/A"; zon_fija = "SELECCIONA"; nom_v = "N/A"

# --- 4. CUERPO PRINCIPAL (TABS) ---
tab1, tab2 = st.tabs(["📝 REGISTRO DE GESTIÓN", "📊 DASHBOARD ANALÍTICO"])

with tab1:
    st.title("Registro de Actividad Diaria")
    detalle = st.selectbox("DETALLE DE GESTIÓN *", ["SELECCIONA", "VENTA FIJA", "NO-VENTA", "CLIENTE AGENDADO", "REFERIDO"])
    
    with st.form(key="form_registro"):
        m_nv = n_cl = d_cl = t_op = prod = dire = c1 = c2 = mail = fe = n_ref = c_ref = "N/A"
        ped = "0"; pil = "NO"

        if detalle == "NO-VENTA":
            m_nv = st.selectbox("MOTIVO *", ["SELECCIONA", "COMPETENCIA", "MALA EXPERIENCIA", "CARGO ALTO", "SIN COBERTURA"])
        elif detalle == "REFERIDO":
            r_c1, r_c2 = st.columns(2)
            n_ref = r_c1.text_input("NOMBRE REFERIDO")
            c_ref = r_c2.text_input("TELÉFONO REFERIDO")
        elif detalle != "SELECCIONA":
            c_a, c_b = st.columns(2)
            with c_a:
                n_cl = st.text_input("CLIENTE *").upper()
                d_cl = st.text_input("DNI CLIENTE *", max_chars=8)
                t_op = st.selectbox("OPERACIÓN *", ["SELECCIONA", "CAPTACIÓN", "MIGRACIÓN", "ALTA"])
                prod = st.selectbox("PRODUCTO *", ["SELECCIONA", "BA", "DUO", "TRIO"])
            with c_b:
                dire = st.text_input("DIRECCIÓN *").upper()
                ped = st.text_input("PEDIDO *", max_chars=10)
                c1 = st.text_input("CELULAR 1 *", max_chars=9)
                c2 = st.text_input("CELULAR 2", max_chars=9)
        
        btn_guardar = st.form_submit_button("🚀 GUARDAR GESTIÓN", use_container_width=True)

    if btn_guardar:
        # (Aquí va la misma lógica de validación que ya probamos...)
        if sup_fijo != "N/A" and detalle != "SELECCIONA":
            try:
                tz = pytz.timezone('America/Lima')
                ahora = datetime.now(tz)
                fila = [ahora.strftime("%d/%m/%Y %H:%M:%S"), zon_fija, f"'{dni_clean}", nom_v, sup_fijo, detalle, t_op, n_cl, f"'{d_cl}", dire, mail, f"'{c1}", f"'{c2}", prod, fe, f"'{ped}", pil, m_nv, n_ref, f"'{c_ref}", ahora.strftime("%d/%m/%Y"), ahora.strftime("%H:%M:%S")]
                conectar_google().sheet1.append_row(fila, value_input_option='USER_ENTERED')
                st.success("¡Guardado!")
                st.balloons()
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

with tab2:
    st.title("Análisis de Resultados")
    if df_gestiones.empty:
        st.warning("No hay datos suficientes para mostrar el Dashboard.")
    else:
        # Filtros superiores
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            filtro_sup = st.multiselect("Filtrar por Supervisor", options=df_gestiones['SUPERVISOR'].unique())
        with f_col2:
            filtro_det = st.multiselect("Filtrar por Gestión", options=df_gestiones['DETALLE GESTIÓN'].unique())

        df_f = df_gestiones.copy()
        if filtro_sup: df_f = df_f[df_f['SUPERVISOR'].isin(filtro_sup)]
        if filtro_det: df_f = df_f[df_f['DETALLE GESTIÓN'].isin(filtro_det)]

        # KPIs
        kpi1, kpi2, kpi3 = st.columns(3)
        total_g = len(df_f)
        ventas = len(df_f[df_f['DETALLE GESTIÓN'] == 'VENTA FIJA'])
        efectividad = (ventas/total_g)*100 if total_g > 0 else 0
        
        kpi1.metric("Total Gestiones", total_g)
        kpi2.metric("Ventas Cerradas", ventas, delta=f"{ventas} fijas")
        kpi3.metric("Efectividad", f"{efectividad:.1f}%")

        # Gráficos
        g1, g2 = st.columns(2)
        
        with g1:
            fig_prod = px.pie(df_f, names='DETALLE GESTIÓN', title="Distribución de Gestiones", hole=0.4)
            st.plotly_chart(fig_prod, use_container_width=True)
            
        with g2:
            df_v_sup = df_f[df_f['DETALLE GESTIÓN'] == 'VENTA FIJA'].groupby('SUPERVISOR').size().reset_index(name='Ventas')
            fig_sup = px.bar(df_v_sup, x='SUPERVISOR', y='Ventas', title="Ventas por Supervisor", color='Ventas')
            st.plotly_chart(fig_sup, use_container_width=True)

        st.subheader("Detalle de la Data")
        st.dataframe(df_f, use_container_width=True)
