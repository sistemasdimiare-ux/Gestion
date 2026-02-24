import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz
import time
import plotly.express as px

# --- 1. CONEXIÓN ---
def conectar_google():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
        return gspread.authorize(creds).open("GestionDiaria")
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None

@st.cache_data(ttl=60)
def cargar_datos():
    doc = conectar_google()
    if not doc: return pd.DataFrame(), pd.DataFrame()
    
    # Carga Estructura
    try:
        ws_est = doc.worksheet("Estructura")
        df_est = pd.DataFrame(ws_est.get_all_values()[1:], columns=ws_est.get_all_values()[0])
        df_est['DNI'] = df_est['DNI'].astype(str).str.replace(r'[^0-9]', '', regex=True).str.zfill(8)
    except:
        df_est = pd.DataFrame(columns=['DNI', 'NOMBRE VENDEDOR', 'SUPERVISOR', 'ZONAL'])
    
    # Carga Registros
    try:
        ws_reg = doc.sheet1
        df_reg = pd.DataFrame(ws_reg.get_all_records())
        df_reg.columns = [c.strip() for c in df_reg.columns] # Limpia espacios en nombres
    except:
        df_reg = pd.DataFrame()
        
    return df_est, df_reg

# --- 2. CONFIGURACIÓN INICIAL ---
st.set_page_config(page_title="Sistema de Gestión Comercial", layout="wide")
df_maestro, df_registros = cargar_datos()

if "form_key" not in st.session_state: st.session_state.form_key = 0

# --- 3. SIDEBAR (IDENTIFICACIÓN) ---
st.sidebar.title("👤 Acceso Vendedor")
dni_input = st.sidebar.text_input("INGRESE DNI VENDEDOR", max_chars=8)
dni_clean = "".join(filter(str.isdigit, dni_input)).zfill(8)

vendedor_info = df_maestro[df_maestro['DNI'] == dni_clean] if not df_maestro.empty else pd.DataFrame()

if not vendedor_info.empty and len(dni_input) == 8:
    sup_fijo = vendedor_info.iloc[0]['SUPERVISOR']
    zon_fija = vendedor_info.iloc[0]['ZONAL']
    nom_v = vendedor_info.iloc[0]['NOMBRE VENDEDOR']
    st.sidebar.success(f"✅ {nom_v}")
    st.sidebar.info(f"Sup: {sup_fijo} | Zonal: {zon_fija}")
else:
    sup_fijo = "N/A"; zon_fija = "SELECCIONA"; nom_v = "N/A"

# --- 4. TABS PRINCIPALES ---
tab1, tab2 = st.tabs(["📝 REGISTRO DE GESTIÓN", "📊 DASHBOARD INTERACTIVO"])

with tab1:
    st.title("Formulario de Registro")
    detalle = st.selectbox("DETALLE DE GESTIÓN *", ["SELECCIONA", "VENTA FIJA", "NO-VENTA", "CLIENTE AGENDADO", "REFERIDO"])

    with st.form(key=f"main_f_{st.session_state.form_key}"):
        # Variables para 22 columnas
        motivo_nv = n_cli = d_cli = t_op = prod = dire = c1 = c2 = mail = fe = n_ref = c_ref = "N/A"
        pedido = "0"; piloto = "NO"

        if detalle == "NO-VENTA":
            motivo_nv = st.selectbox("MOTIVO NO VENTA *", ["SELECCIONA", "COMPETENCIA", "MALA EXPERIENCIA", "CARGO ALTO", "SIN COBERTURA"])
        
        elif detalle == "REFERIDO":
            n_ref = st.text_input("NOMBRE REFERIDO").upper()
            c_ref = st.text_input("CONTACTO REFERIDO", max_chars=9)
            
        elif detalle != "SELECCIONA":
            c_a, c_b = st.columns(2)
            with c_a:
                n_cli = st.text_input("NOMBRE CLIENTE *").upper()
                d_cli = st.text_input("DNI/RUC CLIENTE *", max_chars=11)
                t_op = st.selectbox("OPERACIÓN *", ["SELECCIONA", "CAPTACIÓN", "MIGRACIÓN", "ALTA"])
                prod = st.selectbox("PRODUCTO *", ["SELECCIONA", "BA", "DUO", "TRIO"])
                mail = st.text_input("EMAIL CLIENTE")
            with c_b:
                dire = st.text_input("DIRECCIÓN INSTALACIÓN *").upper()
                pedido = st.text_input("N° PEDIDO (10) *", max_chars=10)
                c1 = st.text_input("CONTACTO 1 *", max_chars=9)
                c2 = st.text_input("CONTACTO 2 (OPCIONAL)", max_chars=9)
                fe = st.text_input("CÓDIGO FE")
                piloto = st.radio("¿PILOTO?", ["SI", "NO"], index=1, horizontal=True)

        enviar = st.form_submit_button("🚀 GUARDAR REGISTRO", use_container_width=True)

    if enviar:
        errores = []
        if sup_fijo == "N/A": errores.append("DNI Vendedor no reconocido.")
        if detalle == "SELECCIONA": errores.append("Elija Detalle de Gestión.")
        if detalle == "VENTA FIJA":
            if not n_cli or n_cli == "N/A": errores.append("Nombre cliente obligatorio.")
            if len(d_cli) < 8: errores.append("Documento cliente inválido.")
            if t_op == "SELECCIONA": errores.append("Seleccione Operación.")
            if prod == "SELECCIONA": errores.append("Seleccione Producto.")
            if not dire or dire == "N/A": errores.append("Dirección obligatoria.")
            if len(pedido) < 5: errores.append("N° Pedido inválido.")
            if len(c1) < 9: errores.append("Contacto 1 obligatorio (9 dígitos).")
        if detalle == "NO-VENTA" and motivo_nv == "SELECCIONA":
            errores.append("Seleccione Motivo de No Venta.")

        if errores:
            for e in errores: st.error(f"⚠️ {e}")
        else:
            try:
                tz = pytz.timezone('America/Lima')
                ahora = datetime.now(tz)
                fila = [
                    ahora.strftime("%d/%m/%Y %H:%M:%S"), zon_fija, f"'{dni_clean}", 
                    nom_v, sup_fijo, detalle, t_op, n_cli, f"'{d_cli}", 
                    dire, mail, f"'{c1}", f"'{c2}", prod, fe, f"'{pedido}", 
                    piloto, motivo_nv, n_ref, f"'{c_ref}", ahora.strftime("%d/%m/%Y"), 
                    ahora.strftime("%H:%M:%S")
                ]
                conectar_google().sheet1.append_row(fila, value_input_option='USER_ENTERED')
                st.success("✅ ¡Guardado Correctamente!")
                st.balloons()
                time.sleep(1)
                st.session_state.form_key += 1
                st.rerun()
            except Exception as e:
                st.error(f"Error al guardar: {e}")

with tab2:
    st.title("Panel Analítico")
    if df_registros.empty:
        st.info("Aún no hay gestiones registradas hoy.")
    else:
        # Mapeo de columnas según tu Excel
        c_sup = "SUPERVISOR"
        c_det = "DETALLE"
        
        # Filtros
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            f_sup = st.multiselect("Filtrar Supervisor", options=df_registros[c_sup].unique())
        with col_f2:
            f_det = st.multiselect("Filtrar Gestión", options=df_registros[c_det].unique())
        
        df_f = df_registros.copy()
        if f_sup: df_f = df_f[df_f[c_sup].isin(f_sup)]
        if f_det: df_f = df_f[df_f[c_det].isin(f_det)]

        # KPIs
        m1, m2, m3 = st.columns(3)
        total = len(df_f)
        ventas = len(df_f[df_f[c_det].astype(str).str.contains("VENTA FIJA", na=False)])
        m1.metric("Total Gestiones", total)
        m2.metric("Ventas Fijas", ventas)
        m3.metric("Efectividad", f"{(ventas/total*100 if total>0 else 0):.1f}%")

        # Gráficos
        g1, g2 = st.columns(2)
        with g1:
            fig1 = px.pie(df_f, names=c_det, title="Mix de Gestiones", hole=0.4)
            st.plotly_chart(fig1, use_container_width=True)
        with g2:
            df_v = df_f[df_f[c_det] == "VENTA FIJA"]
            if not df_v.empty:
                fig2 = px.bar(df_v.groupby(c_sup).size().reset_index(name='Cant'), 
                              x=c_sup, y='Cant', title="Ventas por Supervisor", color_discrete_sequence=['#00CC96'])
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("Sin ventas para graficar.")

        st.subheader("Últimos Registros")
        st.dataframe(df_f.tail(20), use_container_width=True)
