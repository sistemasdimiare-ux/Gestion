import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz
import time

# --- 1. CONEXIÓN ---
def conectar_google():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
        return gspread.authorize(creds).open("GestionDiaria")
    except Exception as e:
        st.error(f"Error de credenciales: {e}")
        return None

@st.cache_data(ttl=60)
def cargar_maestro():
    doc = conectar_google()
    if doc:
        try:
            ws = doc.worksheet("Estructura")
            data = ws.get_all_values()
            df = pd.DataFrame(data[1:], columns=data[0])
            # Limpieza de DNI para asegurar el match
            df['DNI'] = df['DNI'].astype(str).str.replace(r'[^0-9]', '', regex=True).str.zfill(8)
            return df[['DNI', 'NOMBRE VENDEDOR', 'SUPERVISOR', 'ZONAL']]
        except:
            return pd.DataFrame()
    return pd.DataFrame()

# --- 2. CONFIGURACIÓN ---
st.set_page_config(page_title="Registro Ventas", layout="centered")

if "form_key" not in st.session_state: st.session_state.form_key = 0
df_maestro = cargar_maestro()

# --- 3. SIDEBAR ---
st.sidebar.title("👤 Identificación")
dni_input = st.sidebar.text_input("DNI VENDEDOR", max_chars=8)
dni_clean = "".join(filter(str.isdigit, dni_input)).zfill(8)

vendedor = df_maestro[df_maestro['DNI'] == dni_clean] if not df_maestro.empty else pd.DataFrame()

if not vendedor.empty and len(dni_input) == 8:
    sup_fijo = vendedor.iloc[0]['SUPERVISOR']
    zon_fija = vendedor.iloc[0]['ZONAL']
    nom_v = vendedor.iloc[0]['NOMBRE VENDEDOR']
    st.sidebar.success(f"✅ {nom_v}")
else:
    sup_fijo = "N/A"; zon_fija = "SELECCIONA"; nom_v = "N/A"

# --- 4. FORMULARIO ---
st.title("📝 Registro de Gestión")
detalle = st.selectbox("DETALLE DE GESTIÓN *", ["SELECCIONA", "VENTA FIJA", "NO-VENTA", "CLIENTE AGENDADO", "REFERIDO"])

with st.form(key=f"f_{st.session_state.form_key}"):
    # Variables iniciales (22 columnas)
    m_nv = n_cl = d_cl = t_op = prod = dire = c1 = c2 = mail = fe = n_ref = c_ref = "N/A"
    ped = "0"; pil = "NO"

    if detalle == "NO-VENTA":
        m_nv = st.selectbox("MOTIVO *", ["SELECCIONA", "COMPETENCIA", "MALA EXPERIENCIA", "CARGO ALTO", "SIN COBERTURA"])
    
    elif detalle == "REFERIDO":
        n_ref = st.text_input("NOMBRE REFERIDO").upper()
        c_ref = st.text_input("CONTACTO REFERIDO", max_chars=9)
        
    elif detalle != "SELECCIONA":
        c_a, c_b = st.columns(2)
        with c_a:
            n_cl = st.text_input("NOMBRE CLIENTE *").upper()
            d_cl = st.text_input("DNI CLIENTE (8) *", max_chars=8)
            t_op = st.selectbox("OPERACIÓN *", ["SELECCIONA", "CAPTACIÓN", "MIGRACIÓN", "ALTA"])
            prod = st.selectbox("PRODUCTO *", ["SELECCIONA", "BA", "DUO", "TRIO"])
        with c_b:
            dire = st.text_input("DIRECCIÓN *").upper()
            ped = st.text_input("N° PEDIDO (10) *", max_chars=10)
            c1 = st.text_input("CELULAR (9) *", max_chars=9)
            fe = st.text_input("CÓDIGO FE")
            pil = st.radio("¿PILOTO?", ["SI", "NO"], index=1, horizontal=True)

    enviar = st.form_submit_button("🚀 GUARDAR REGISTRO", use_container_width=True)

# --- 5. VALIDACIÓN Y GUARDADO ---
if enviar:
    errores = []
    
    if sup_fijo == "N/A": errores.append("Vendedor no identificado.")
    if detalle == "SELECCIONA": errores.append("Seleccione Detalle de Gestión.")
    
    if detalle == "VENTA FIJA":
        if not n_cl or n_cl == "N/A": errores.append("Nombre del cliente es obligatorio.")
        if len(d_cl) < 8: errores.append("DNI del cliente inválido.")
        if t_op == "SELECCIONA": errores.append("Seleccione Tipo de Operación.")
        if prod == "SELECCIONA": errores.append("Seleccione Producto.")
        if not dire or dire == "N/A": errores.append("La Dirección es obligatoria.")
        if len(ped) < 5: errores.append("Número de pedido incompleto.")
        if len(c1) < 9: errores.append("Celular debe tener 9 dígitos.")
    
    if detalle == "NO-VENTA" and m_nv == "SELECCIONA":
        errores.append("Seleccione un Motivo de No-Venta.")

    if errores:
        for err in errores:
            st.error(err)
    else:
        try:
            tz = pytz.timezone('America/Lima')
            ahora = datetime.now(tz)
            fila = [
                ahora.strftime("%d/%m/%Y %H:%M:%S"), zon_fija, f"'{dni_clean}", 
                nom_v, sup_fijo, detalle, t_op, n_cl, f"'{d_cl}", 
                dire, mail, f"'{c1}", f"'{c2}", prod, fe, f"'{ped}", 
                pil, m_nv, n_ref, f"'{c_ref}", ahora.strftime("%d/%m/%Y"), 
                ahora.strftime("%H:%M:%S")
            ]
            
            conectar_google().sheet1.append_row(fila, value_input_option='USER_ENTERED')
            st.success("✅ Registro guardado.")
            st.balloons()
            time.sleep(1)
            st.session_state.form_key += 1
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")
