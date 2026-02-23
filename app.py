import streamlit as st
import pandas as pd
from datetime import datetime
import time
import dropbox
import io
import pytz
import re

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Sistema Gestión de Ventas", layout="wide")

def save_to_dropbox(df_nuevo):
    # Token (Asegúrate de que no haya expirado)
    TOKEN = "sl.u.AGViaoJq8zsl_vm7zPGDlrcrOm-iHq45Yvwg-b9L2UBSa9UnIy-sl6DX80g8_Jczf-GJDystCn3_gexHdAmzcZIjWUgFNzVNt1UJJgToW60YXYB4DqKZqtDCU7SqW4MFDPC-flj6eqL1XqL4Q1eusfHV-2TjEOq2yJxMVMfz2PTHYPMTl8kMn1QWO7_IoJON1SzPGlE0HScXG6YP2bCzh5y6elz-ujkCF5qCnxR89u1i8C000X2zt-XqswO5Diqq8TZ2cqxmAs31vrRz54yW5LL3H5Vjtu_Go0eHw8WeXjaClUpZanKCDtH0OE4uJvDkzyktl24csNsPWA8sx_AsSuayTzmXzp3Rb4_xcJ2p-O2VYZmYd9wsvQUec4y6KAXSUiqz7t0LfMsRpCer8j6DhXSKW7amIKlsPPeRlQBs5G77viNyaQTxjgon8z0kU5LPbcheNHL3Ktfkny_9yT4_ahEGPKkvhu14NKAbq0Pc3pQH19exz9QCWirB-vA54t-g9oAgjas2aijQ1X73pFWAhGaCRci41zqOSR2sgQ3Iw_I1HMIpSQL3yxMuvUz4Bmk8TvWk6Ahytun2OrKDUgXHcFUgo4Pmf_88zElwAMcehoLdI56mdMZmVD9TFsJ5gO9TS-Wr_-u4lfNl8t3zgRX4tyBeR9Fz0ablP_JKc3QYpwjxr6JHLH_TPT9xUutd5o3ojd-UN-eGjEjiS71hRl3zfTFOyrWSTNpou-a8_cVZeH1OrxEEftvWwtKGJPWwlSHGxfrwqps3kSx07dMU1vG3vEy0z_QqWsNEYo1d7XnwPdB20sfqsrW0aIu-uCVf8GDUPCD1rlUf-DoaSKDdMaqnpYiDClHiIyVtSUSHoYaPlEFjSN_jw0OfelvxUe6McmJttJ-fvQtS17Pphderxlhkz-i5r8o1qGBSLMbqv0APMUIEvxJjowCpbkLE1hAZkCAtnN7bi-byrzPp5aZ0tc0CVfPGzZgTk3pcOD7Xw0gfqhlT_shiTHabiaU9Q9owFD1sLVgbYnI6grObz_qhG_qAqOu0Ie6fxpYmBaKn-7q3ywfqeLjPMAw2Yq-tCgrIKURGGzNZxi55GeOpfkf6t9H-_bngRCwba7w0Zg_h7HYvRaG2Qbn7FA8HY9RqKHXOKP45hnDv9cEM8jpVS8l-1IY83CaFgpwEDvP5eDxDA_3rxmnieAqBPpWK88ExraKOLdsjCFgVUiumpoUq4P5jKtGfKQgKFu-Ld5swNv-doSZ42FIP8frQ5cC6ygLyGcc3K344ZD8Gq8y2PuTII1dImgjse0DUIJAlQdU_oHMc_ikQqrUojfWMHwDAxGmrDwGuTe-kQig"
    PATH = "/Gestion Analitica/Alvaro/GestionDiaria.xlsx"
    dbx = dropbox.Dropbox(TOKEN)
    try:
        _, res = dbx.files_download(PATH)
        df_actual = pd.read_excel(io.BytesIO(res.content))
        df_final = pd.concat([df_actual, df_nuevo], ignore_index=True)
    except:
        df_final = df_nuevo
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_final.to_excel(writer, index=False)
    dbx.files_upload(output.getvalue(), PATH, mode=dropbox.files.WriteMode.overwrite)

# --- 2. LÓGICA DE REINICIO ---
if "form_key" not in st.session_state:
    st.session_state.form_key = 0

def clean_and_reset():
    st.session_state.form_key += 1
    st.rerun()

# --- 3. PANEL SUPERIOR Y LATERAL ---
st.title("📝 Formulario de Gestión Diaria")
st.sidebar.header("Datos Vendedor")
zonal = st.sidebar.selectbox("ZONAL", ["SELECCIONA", "TRUJILLO", "LIMA NORTE", "LIMA SUR - FIJA", "LIMA ESTE", "HUANCAYO", "CAJAMARCA", "TARAPOTO"])
dni_vendedor = st.sidebar.text_input("N° DOCUMENTO VENDEDOR (8)", max_chars=8)

# --- 4. FORMULARIO ---
with st.form(key=f"form_gestion_{st.session_state.form_key}"):
    c1, c2 = st.columns(2)
    
    with c1:
        detalle = st.selectbox("DETALLE *", ["SELECCIONA", "VENTA FIJA", "NO-VENTA", "CLIENTE AGENDADO", "REFERIDO", "PRE-VENTA"])
        nombre_cliente = st.text_input("NOMBRE DE CLIENTE").upper()
        dni_cliente = st.text_input("N° DE DOCUMENTO CLIENTE (8)", max_chars=8)
        tipo_op = st.selectbox("Tipo de Operación", ["SELECCIONA", "CAPTACIÓN", "MIGRACIÓN", "COMPLETA TV", "COMPLETA MT", "COMPLETA BA"])
        producto = st.selectbox("PRODUCTO", ["SELECCIONA", "NAKED", "DUO INT + TV", "DUO TV", "DUO BA", "TRIO"])
        pedido = st.text_input("N° de Pedido (10)", max_chars=10)
        email = st.text_input("EMAIL DE CLIENTE")

    with c2:
        motivo_no_venta = st.selectbox("INDICAR MOTIVO DE NO VENTA", ["", "COMPETENCIA", "CLIENTE MOVISTAR", "MALA EXPERIENCIA", "CARGO FIJO ALTO"])
        direccion = st.text_input("DIRECCION DE INSTALACION").upper()
        contacto1 = st.text_input("N° DE CONTACTO 1 (9)", max_chars=9)
        contacto2 = st.text_input("N° DE CONTACTO 2 (9)", max_chars=9)
        cod_fe = st.text_input("Código FE")
        venta_piloto = st.radio("¿Venta Piloto?", ["SI", "NO"], horizontal=True)

    st.markdown("---")
    st.subheader("Datos de Referido (Opcional)")
    nom_referido = st.text_input("NOMBRE Y APELLIDO DE REFERIDO").upper()
    cont_referido = st.text_input("N° DE CONTACTO REFERIDO (9)", max_chars=9)

    enviar = st.form_submit_button("🚀 REGISTRAR GESTIÓN", use_container_width=True)

# --- 5. LÓGICA DE VALIDACIÓN ESTRICTA ---
if enviar:
    errores = []
    
    # Validación DNI Vendedor (Siempre)
    if len(dni_vendedor) != 8: errores.append("DNI Vendedor debe tener 8 dígitos.")
    if zonal == "SELECCIONA": errores.append("Seleccione una ZONAL.")

    # CASO: NO-VENTA (Ignora casi todo, solo exige el motivo)
    if detalle == "NO-VENTA":
        if not motivo_no_venta:
            errores.append("Para NO-VENTA, el motivo es obligatorio.")
    
    # CASO: RESTO DE GESTIONES (Venta, Agendado, etc.)
    elif detalle == "SELECCIONA":
        errores.append("Debe elegir un tipo de DETALLE.")
    else:
        # Validaciones de longitud exacta
        if not nombre_cliente: errores.append("Nombre de cliente es obligatorio.")
        if len(dni_cliente) != 8: errores.append("DNI Cliente debe tener 8 dígitos.")
        if len(pedido) != 10: errores.append("N° de Pedido debe tener 10 dígitos.")
        if len(contacto1) != 9: errores.append("Contacto 1 debe tener 9 dígitos.")
        if tipo_op == "SELECCIONA": errores.append("Seleccione Tipo de Operación.")

    # MOSTRAR ERRORES O PROCESAR
    if errores:
        for err in errores: st.error(err)
    else:
        # GENERACIÓN DE MARCA TEMPORAL (HORA PERÚ)
        peru_tz = pytz.timezone('America/Lima')
        dt_ahora = datetime.now(peru_tz)
        
        datos = {
            "Marca temporal": dt_ahora.strftime("%d/%m/%Y %H:%M:%S"),
            "ZONAL": zonal,
            "N° DOCUMENTO VENDEDOR": dni_vendedor,
            "DETALLE": detalle,
            "Tipo de Operación": tipo_op if detalle != "NO-VENTA" else "N/A",
            "NOMBRE DE CLIENTE": nombre_cliente if nombre_cliente else "N/A",
            "N° DE DOCUMENTO": dni_cliente if dni_cliente else "N/A",
            "DIRECCION DE INSTALACION": direccion,
            "EMAIL DE CLIENTE": email,
            "N° DE CONTACTO DE CLIENTE 1": contacto1,
            "N° DE CONTACTO DE CLIENTE 2": contacto2,
            "PRODUCTO": producto if detalle != "NO-VENTA" else "N/A",
            "Código FE": cod_fe,
            "N° de Pedido": pedido if detalle != "NO-VENTA" else "0",
            "¿Venta Piloto?": venta_piloto if detalle != "NO-VENTA" else "NO",
            "INDICAR MOTIVO DE NO VENTA": motivo_no_venta if detalle == "NO-VENTA" else "N/A",
            "NOMBRE Y APELLIDO DE REFERIDO": nom_referido,
            "N° DE CONTACTO REFERIDO": cont_referido,
            "Fecha": dt_ahora.strftime("%d/%m/%Y"),
            "Hora": dt_ahora.strftime("%H:%M:%S")
        }

        try:
            save_to_dropbox(pd.DataFrame([datos]))
            st.success("✅ Gestión guardada con éxito.")
            st.balloons()
            time.sleep(2)
            clean_and_reset()
        except Exception as e:
            st.error(f"Error al conectar con Dropbox: {e}")
