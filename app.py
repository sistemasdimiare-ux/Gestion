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
    TOKEN = "sl.u.AGU1roA833OnwoBa7BMsz0uAzxHVKm7ycNn_IDJQW-WuvTixlpz5273T91nGHfPFh1l9RO_2AhmnmMPnwh2EOkYpRZTX8uf9k_hn1l_Ht-RD0nlFAVhxCryYtbkKZf5z4WH4acwlAUZ-jOecOUQdV2j6q8yROMhHKRVX_T8wg8cSn9GAcZqPacnF5QbY6JkKXoRMDWiZRHbAeF3kY-Yd55hKcf3AeML5LHULY7F7zTTjqzgvOKVGT-fcl01d5Vj6FkfuMJy67G_ivJmuKOY2Od_msX95w7VLSTBobcIMs7PkAIF1k-ic2Q-jym4ApIbR_a5wzfLMuKtf45xjqH9TyBf9shYoPGe-87MNGm3uwyxMegjAuJ8d-9LAvyg6Zo2HBVvYpDpAH9A7xtVQjm-aYiKdVjUskQpLUdSx5BkUX_4qGc1BFLv2_eRgJvxxozCFL5kQmg3xslQ4nA5grUcQqw9JnYv5gaoi8F6zQ6E2fr_MmMvawaNCvM-LjVs3pMqduD3vB145rvh41rei1rToF_bN44KYJB-HWc4AZG1zMac3OtFWlyb_WRLGZTxK7FjLRoMlPkOKPk_0lxq4s3xeZbi-1ZnPTCyp5vMo42Ny3I8_1LG9YLVBErUZAKJ4XCLnPDckWsQTbGGEeOCdpDOe3Z10rK-el1A_rI4YpDa1Pcf5BLPSsparVXF2pueOvXE7_lorSNKGw7rVlRrCGkig4cNvqp11mKd4uANYcBw4jC6q_uV16jb0C96b07R_A5IKgXLi2tOJpuNWaQgAZxxFyA2dk904CpDyizjkwNsbQ3xdJmYYDiRTaRXGvfMts45kJGJwOj8HvJCUlp2Z8ksHoGJwcREZGr5kktNl4FvKnsdO56sOnoLmPOcGK0DTGeEt24lAmYnf5az_CTtANi2WHTCSlsRRu5Sof-9ehIZ5SOFhKXyjkkpHr7FXA2fJwk3Oa5ayFfhJDH3vOS2EFxAqyV2vS0Rkzc_M_1iJKBY6iCqqnqRqhCP0CTUCjvRDbxn99ya4tC4FZVL1UqNeXnyYo9QQXjW8iPJCS3ZLlJLPlpII1JkYsfGpC1zZ4Esf55ZU7s5SKZNves8ad8HSewOg9p6iGhnItFPXpyb6i2ET1jZpsbK7uZErqDf6Uzw1RwMNzsq79f19t7jad69qwtCsiKtBeJYk8Xg8ZdC5kthylWZnbA2CikruJQURCIaHbyZn0pYiShqjkIfEF3nBp1KrXfFAs1ZvAHFD7iBd83w0ZJkXLDQy3He0AxoQUS-Em9qrrtrAZkf8cI_wGOkfBVqZHmLKP_p67HALzK5QUyJWl8VjOz6X38E7HJxURKkfDcGUONw"
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
