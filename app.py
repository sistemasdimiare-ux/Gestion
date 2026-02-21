import streamlit as st
import pandas as pd
from datetime import datetime
import time
import dropbox
import io
import pytz

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Gestión de Ventas", layout="wide")

# --- 2. FUNCIÓN DE GUARDADO ---
def save_to_dropbox(df_nuevo):
    DROPBOX_ACCESS_TOKEN = "sl.u.AGU1roA833OnwoBa7BMsz0uAzxHVKm7ycNn_IDJQW-WuvTixlpz5273T91nGHfPFh1l9RO_2AhmnmMPnwh2EOkYpRZTX8uf9k_hn1l_Ht-RD0nlFAVhxCryYtbkKZf5z4WH4acwlAUZ-jOecOUQdV2j6q8yROMhHKRVX_T8wg8cSn9GAcZqPacnF5QbY6JkKXoRMDWiZRHbAeF3kY-Yd55hKcf3AeML5LHULY7F7zTTjqzgvOKVGT-fcl01d5Vj6FkfuMJy67G_ivJmuKOY2Od_msX95w7VLSTBobcIMs7PkAIF1k-ic2Q-jym4ApIbR_a5wzfLMuKtf45xjqH9TyBf9shYoPGe-87MNGm3uwyxMegjAuJ8d-9LAvyg6Zo2HBVvYpDpAH9A7xtVQjm-aYiKdVjUskQpLUdSx5BkUX_4qGc1BFLv2_eRgJvxxozCFL5kQmg3xslQ4nA5grUcQqw9JnYv5gaoi8F6zQ6E2fr_MmMvawaNCvM-LjVs3pMqduD3vB145rvh41rei1rToF_bN44KYJB-HWc4AZG1zMac3OtFWlyb_WRLGZTxK7FjLRoMlPkOKPk_0lxq4s3xeZbi-1ZnPTCyp5vMo42Ny3I8_1LG9YLVBErUZAKJ4XCLnPDckWsQTbGGEeOCdpDOe3Z10rK-el1A_rI4YpDa1Pcf5BLPSsparVXF2pueOvXE7_lorSNKGw7rVlRrCGkig4cNvqp11mKd4uANYcBw4jC6q_uV16jb0C96b07R_A5IKgXLi2tOJpuNWaQgAZxxFyA2dk904CpDyizjkwNsbQ3xdJmYYDiRTaRXGvfMts45kJGJwOj8HvJCUlp2Z8ksHoGJwcREZGr5kktNl4FvKnsdO56sOnoLmPOcGK0DTGeEt24lAmYnf5az_CTtANi2WHTCSlsRRu5Sof-9ehIZ5SOFhKXyjkkpHr7FXA2fJwk3Oa5ayFfhJDH3vOS2EFxAqyV2vS0Rkzc_M_1iJKBY6iCqqnqRqhCP0CTUCjvRDbxn99ya4tC4FZVL1UqNeXnyYo9QQXjW8iPJCS3ZLlJLPlpII1JkYsfGpC1zZ4Esf55ZU7s5SKZNves8ad8HSewOg9p6iGhnItFPXpyb6i2ET1jZpsbK7uZErqDf6Uzw1RwMNzsq79f19t7jad69qwtCsiKtBeJYk8Xg8ZdC5kthylWZnbA2CikruJQURCIaHbyZn0pYiShqjkIfEF3nBp1KrXfFAs1ZvAHFD7iBd83w0ZJkXLDQy3He0AxoQUS-Em9qrrtrAZkf8cI_wGOkfBVqZHmLKP_p67HALzK5QUyJWl8VjOz6X38E7HJxURKkfDcGUONw"
    DROPBOX_FILE_PATH = "/Gestion Analitica/Alvaro/GestionDiaria.xlsx"
    dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
    try:
        _, res = dbx.files_download(DROPBOX_FILE_PATH)
        df_actual = pd.read_excel(io.BytesIO(res.content))
        df_final = pd.concat([df_actual, df_nuevo], ignore_index=True)
    except:
        df_final = df_nuevo
    output = io.BytesIO()
    with pd.ExcelWriter(output) as writer:
        df_final.to_excel(writer, index=False)
    dbx.files_upload(output.getvalue(), DROPBOX_FILE_PATH, mode=dropbox.files.WriteMode.overwrite)

# --- 3. FUNCIÓN PARA LIMPIAR (CALLBACK) ---
def borrar_estado():
    for key in list(st.session_state.keys()):
        if key.startswith("k_"):
            # Reseteamos los valores en el diccionario de estado
            if key in ["k_tipo", "k_prod", "k_det"]:
                st.session_state[key] = "SELECCIONA"
            elif key == "k_pilo":
                st.session_state[key] = None
            else:
                st.session_state[key] = ""

# --- 4. BARRA LATERAL ---
st.sidebar.title("👤 Datos del Vendedor")
zonal = st.sidebar.selectbox("ZONAL", ["TRUJILLO", "LIMA NORTE", "LIMA SUR - FIJA", "LIMA ESTE", "HUANCAYO", "CAJAMARCA", "TARAPOTO"])
dni_vendedor = st.sidebar.text_input("N° DOCUMENTO VENDEDOR", max_chars=11)

# --- 5. PANEL PRINCIPAL ---
st.title("📝 Registro de Gestión de Ventas")
col1, col2 = st.columns(2)

with col1:
    nombre_cliente = st.text_input("NOMBRE DE CLIENTE *", key="k_nom").upper()
    dni_cliente = st.text_input("N° DE DOCUMENTO (CLIENTE) *", max_chars=11, key="k_dni_c")
    email_cliente = st.text_input("EMAIL DE CLIENTE", key="k_mail").lower()
    tipo_op = st.selectbox("Tipo de Operación", ["SELECCIONA","CAPTACIÓN", "MIGRACIÓN", "COMPLETA TV", "COMPLETA MT", "COMPLETA BA"], key="k_tipo")
    producto = st.selectbox("PRODUCTO", ["SELECCIONA", "NAKED", "DUO INT + TV", "DUO TV", "DUO BA", "TRIO"], key="k_prod")
    cod_fe = st.text_input("Código FE", key="k_fe").upper()
    pedido = st.text_input("N° de Pedido *", max_chars=10, key="k_ped")

with col2:
    detalle = st.selectbox("DETALLE", ["SELECCIONA", "VENTA FIJA", "NO-VENTA", "CLIENTE AGENDADO", "REFERIDO", "PRE-VENTA"], key="k_det")
    direccion = st.text_input("DIRECCION DE INSTALACION", key="k_dir").upper()
    contacto1 = st.text_input("N° DE CONTACTO 1 *", max_chars=9, key="k_cont1")
    contacto2 = st.text_input("N° DE CONTACTO 2", max_chars=9, key="k_cont2")
    venta_piloto = st.radio("¿Venta Piloto? *", ["SI", "NO"], index=None, horizontal=True, key="k_pilo")
    
    motivo_no_venta = ""
    if detalle == "NO-VENTA":
        motivo_no_venta = st.selectbox("MOTIVO NO VENTA *", ["", "COMPETENCIA", "CLIENTE MOVISTAR", "MALA EXPERIENCIA"], key="k_mot")
            
    nom_referido = st.text_input("NOMBRE REFERIDO", key="k_ref_n").upper()
    cont_referido = st.text_input("N° CONTACTO REFERIDO", max_chars=9, key="k_ref_c")

# --- 6. BOTÓN CON LÓGICA DE GUARDADO ---
if st.button("🚀 Enviar Registro", use_container_width=True):
    # Validaciones rápidas
    if not nombre_cliente or not dni_cliente or not pedido or venta_piloto is None or tipo_op == "SELECCIONA":
        st.error("❌ Por favor, llena todos los campos obligatorios (*)")
    else:
        # HORA PERÚ
        zona_horaria = pytz.timezone('America/Lima')
        ahora = datetime.now(zona_horaria)

        NuevosDatos = {
            "Marca temporal": ahora.strftime("%d/%m/%Y %H:%M:%S"),
            "ZONAL": zonal, "N° DOCUMENTO VENDEDOR": dni_vendedor,
            "DETALLE": detalle, "Tipo de Operación": tipo_op,
            "NOMBRE DE CLIENTE": nombre_cliente, "N° DE DOCUMENTO": dni_cliente,
            "DIRECCION DE INSTALACION": direccion, "EMAIL DE CLIENTE": email_cliente,
            "N° DE CONTACTO DE CLIENTE 1": contacto1, "N° DE CONTACTO DE CLIENTE 2": contacto2,
            "PRODUCTO": producto, "Código FE": cod_fe, "N° de Pedido": pedido,
            "¿Venta Piloto?": venta_piloto, "INDICAR MOTIVO DE NO VENTA": motivo_no_venta,
            "NOMBRE Y APELLIDO DE REFERIDO": nom_referido, "N° DE CONTACTO REFERIDO": cont_referido,
            "Fecha": ahora.strftime("%d/%m/%Y"), "Hora": ahora.strftime("%H:%M:%S")
        }

        try:
            save_to_dropbox(pd.DataFrame([NuevosDatos]))
            st.success("✅ ¡Guardado con éxito!")
            st.balloons()
            
            # --- AQUÍ ESTÁ EL CAMBIO ---
            # En lugar de modificar el state aquí, llamamos a la función y luego reiniciamos
            borrar_estado()
            time.sleep(1)
            st.rerun() 
            
        except Exception as e:
            st.error(f"❌ Error al guardar: {e}")
