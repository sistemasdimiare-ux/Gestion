import streamlit as st
import pandas as pd
from datetime import datetime
import time
import dropbox
import io
import pytz

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Gestión de Ventas", layout="wide")

def save_to_dropbox(df_nuevo):
    DROPBOX_ACCESS_TOKEN = "sl.u.AGU1roA833OnwoBa7BMsz0uAzxHVKm7ycNn_IDJQW-WuvTixlpz5273T91nGHfPFh1l9RO_2AhmnmMPnwh2EOkYpRZTX8uf9k_hn1l_Ht-RD0nlFAVhxCryYtbkKZf5z4WH4acwlAUZ-jOecOUQdV2j6q8yROMhHKRVX_T8wg8cSn9GAcZqPacnF5QbY6JkKXoRMDWiZRHbAeF3kY-Yd55hKcf3AeML5LHULY7F7zTTjqzgvOKVGT-fcl01d5Vj6FkfuMJy67G_ivJmuKOY2Od_msX95w7VLSTBobcIMs7PkAIF1k-ic2Q-jym4ApIbR_a5wzfLMuKtf45xjqH9TyBf9shYoPGe-87MNGm3uwyxMegjAuJ8d-9LAvyg6Zo2HBVvYpDpAH9A7xtVQjm-aYiKdVjUskQpLUdSx5BkUX_4qGc1BFLv2_eRgJvxxozCFL5kQmg3xslQ4nA5grUcQqw9JnYv5gaoi8F6zQ6E2fr_MmMvawaNCvM-LjVs3pMqduD3vB145rvh41rei1rToF_bN44KYJB-HWc4AZG1zMac3OtFWlyb_WRLGZTxK7FjLRoMlPkOKPk_0lxq4s3xeZbi-1ZnPTCyp5vMo42Ny3I8_1LG9YLVBErUZAKJ4XCLnPDckWsQTbGGEeOCdpDOe3Z10rK-el1A_rI4YpDa1Pcf5BLPSsparVXF2pueOvXE7_lorSNKGw7rVlRrCGkig4cNvqp11mKd4uANYcBw4jC6q_uV16jb0C96b07R_A5IKgXLi2tOJpuNWaQgAZxxFyA2dk904CpDyizjkwNsbQ3xdJmYYDiRTaRXGvfMts45kJGJwOj8HvJCUlp2Z8ksHoGJwcREZGr5kktNl4FvKnsdO56sOnoLmPOcGK0DTGeEt24lAmYnf5az_CTtANi2WHTCSlsRRu5Sof-9ehIZ5SOFhKXyjkkpHr7FXA2fJwk3Oa5ayFfhJDH3vOS2EFxAqyV2vS0Rkzc_M_1iJKBY6iCqqnqRqhCP0CTUCjvRDbxn99ya4tC4FZVL1UqNeXnyYo9QQXjW8iPJCS3ZLlJLPlpII1JkYsfGpC1zZ4Esf55ZU7s5SKZNves8ad8HSewOg9p6iGhnItFPXpyb6i2ET1jZpsbK7uZErqDf6Uzw1RwMNzsq79f19t7jad69qwtCsiKtBeJYk8Xg8ZdC5kthylWZnbA2CikruJQURCIaHbyZn0pYiShqjkIfEF3nBp1KrXfFAs1ZvAHFD7iBd83w0ZJkXLDQy3He0AxoQUS-Em9qrrtrAZkf8cI_wGOkfBVqZHmLKP_p67HALzK5QUyJWl8VjOz6X38E7HJxURKkfDcGUONw" # Reemplaza con tu token real
    DROPBOX_FILE_PATH = "/Gestion Analitica/Alvaro/GestionDiaria.xlsx"
    dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
    
    try:
        _, res = dbx.files_download(DROPBOX_FILE_PATH)
        df_actual = pd.read_excel(io.BytesIO(res.content))
        df_final = pd.concat([df_actual, df_nuevo], ignore_index=True)
    except:
        df_final = df_nuevo
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_final.to_excel(writer, index=False)
    dbx.files_upload(output.getvalue(), DROPBOX_FILE_PATH, mode=dropbox.files.WriteMode.overwrite)

# --- 2. BARRA LATERAL ---
st.sidebar.title("👤 Datos del Vendedor")
zonal = st.sidebar.selectbox("ZONAL", ["TRUJILLO", "LIMA NORTE", "LIMA SUR - FIJA", "LIMA ESTE", "HUANCAYO", "CAJAMARCA", "TARAPOTO"])
dni_vendedor = st.sidebar.text_input("N° DOCUMENTO VENDEDOR", max_chars=11)

# --- 3. LÓGICA DE REINICIO ---
if "form_iter" not in st.session_state:
    st.session_state.form_iter = 0

def reiniciar_formulario():
    st.session_state.form_iter += 1
    st.rerun()

# --- 4. PANEL PRINCIPAL ---
st.title("📝 Registro de Gestión de Ventas")

with st.container():
    with st.form(key=f"form_{st.session_state.form_iter}"):
        col1, col2 = st.columns(2)

        with col1:
            nombre_cliente = st.text_input("NOMBRE DE CLIENTE *").upper()
            dni_cliente = st.text_input("N° DE DOCUMENTO (CLIENTE) *", max_chars=11)
            detalle = st.selectbox("DETALLE *", ["SELECCIONA", "VENTA FIJA", "NO-VENTA", "CLIENTE AGENDADO", "REFERIDO", "PRE-VENTA"])
            
            # Lógica condicional: Si es NO-VENTA, mostramos el motivo inmediatamente debajo
            if detalle == "NO-VENTA":
                motivo_no_venta = st.selectbox("INDICAR MOTIVO DE NO VENTA *", ["", "CUENTA CON SERVICIO DE COMPETENCIA", "CLIENTE MOVISTAR", "MALA EXPERIENCIA", "CARGO FIJO INSUFICIENTE"])
            else:
                motivo_no_venta = ""

        with col2:
            # Solo mostramos estos campos si NO es una "NO-VENTA"
            if detalle != "NO-VENTA":
                tipo_op = st.selectbox("Tipo de Operación *", ["SELECCIONA","CAPTACIÓN", "MIGRACIÓN", "COMPLETA TV", "COMPLETA MT", "COMPLETA BA"])
                producto = st.selectbox("PRODUCTO", ["SELECCIONA", "NAKED", "DUO INT + TV", "DUO TV", "DUO BA", "TRIO"])
                pedido = st.text_input("N° de Pedido *", max_chars=10)
                contacto1 = st.text_input("N° DE CONTACTO 1 *", max_chars=9)
                venta_piloto = st.radio("¿Venta Piloto? *", ["SI", "NO"], index=None, horizontal=True)
            else:
                # Valores por defecto para la base de datos si es NO-VENTA
                tipo_op = "N/A"
                producto = "N/A"
                pedido = "0"
                contacto1 = "0"
                venta_piloto = "NO"

        # Campos opcionales (se muestran siempre o puedes meterlos en el IF anterior)
        with st.expander("Ver más campos (Opcionales)"):
            c1, c2 = st.columns(2)
            email_cliente = c1.text_input("EMAIL DE CLIENTE").lower()
            direccion = c1.text_input("DIRECCION DE INSTALACION").upper()
            cod_fe = c2.text_input("Código FE").upper()
            nom_referido = c2.text_input("NOMBRE Y APELLIDO DE REFERIDO").upper()
            cont_referido = c2.text_input("N° DE CONTACTO REFERIDO", max_chars=9)

        enviado = st.form_submit_button("🚀 Enviar Registro", use_container_width=True)

# --- 5. VALIDACIONES DINÁMICAS ---
if enviado:
    errores = []
    
    # Validaciones comunes
    if not dni_vendedor: errores.append("DNI Vendedor (Barra Lateral)")
    if not nombre_cliente: errores.append("Nombre de Cliente")
    if not dni_cliente: errores.append("DNI Cliente")
    if detalle == "SELECCIONA": errores.append("Debe seleccionar el DETALLE")

    # Validaciones específicas para NO-VENTA
    if detalle == "NO-VENTA":
        if not motivo_no_venta: errores.append("Debe indicar el Motivo de No Venta")
    
    # Validaciones específicas para VENTAS o gestiones positivas
    else:
        if tipo_op == "SELECCIONA": errores.append("Tipo de Operación")
        if not pedido or not pedido.isdigit(): errores.append("N° de Pedido (solo números)")
        if not contacto1 or len(contacto1) != 9: errores.append("Contacto 1 (9 dígitos)")
        if venta_piloto is None: errores.append("Seleccione SI o NO en Venta Piloto")

    if errores:
        st.error("⚠️ Faltan datos:")
        for e in errores: st.write(f"- {e}")
    else:
        zona_peru = pytz.timezone('America/Lima')
        ahora = datetime.now(zona_peru)
        
        NuevosDatos = {
            "Marca temporal": ahora.strftime("%d/%m/%Y %H:%M:%S"),
            "ZONAL": zonal, "N° DOCUMENTO VENDEDOR": dni_vendedor,
            "DETALLE": detalle, "Tipo de Operación": tipo_op,
            "NOMBRE DE CLIENTE": nombre_cliente, "N° DE DOCUMENTO": dni_cliente,
            "DIRECCION DE INSTALACION": direccion if 'direccion' in locals() else "",
            "EMAIL DE CLIENTE": email_cliente if 'email_cliente' in locals() else "",
            "N° DE CONTACTO DE CLIENTE 1": contacto1,
            "PRODUCTO": producto, "N° de Pedido": pedido,
            "¿Venta Piloto?": venta_piloto, "INDICAR MOTIVO DE NO VENTA": motivo_no_venta,
            "NOMBRE Y APELLIDO DE REFERIDO": nom_referido if 'nom_referido' in locals() else "",
            "Fecha": ahora.strftime("%d/%m/%Y"), "Hora": ahora.strftime("%H:%M:%S")
        }

        try:
            save_to_dropbox(pd.DataFrame([NuevosDatos]))
            st.success("✅ ¡No-Venta registrada con éxito!")
            st.balloons()
            time.sleep(2)
            reiniciar_formulario()
        except Exception as e:
            st.error(f"❌ Error: {e}")
