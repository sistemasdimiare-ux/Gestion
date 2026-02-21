import streamlit as st
import pandas as pd
from datetime import datetime
import time
import dropbox # Asegúrate de tener esta línea al inicio
import io
import pytz # Importante para manejar zonas horarias

def save_to_dropbox(df_nuevo):
    # Reemplaza con tu Token real
    DROPBOX_ACCESS_TOKEN = "sl.u.AGU1roA833OnwoBa7BMsz0uAzxHVKm7ycNn_IDJQW-WuvTixlpz5273T91nGHfPFh1l9RO_2AhmnmMPnwh2EOkYpRZTX8uf9k_hn1l_Ht-RD0nlFAVhxCryYtbkKZf5z4WH4acwlAUZ-jOecOUQdV2j6q8yROMhHKRVX_T8wg8cSn9GAcZqPacnF5QbY6JkKXoRMDWiZRHbAeF3kY-Yd55hKcf3AeML5LHULY7F7zTTjqzgvOKVGT-fcl01d5Vj6FkfuMJy67G_ivJmuKOY2Od_msX95w7VLSTBobcIMs7PkAIF1k-ic2Q-jym4ApIbR_a5wzfLMuKtf45xjqH9TyBf9shYoPGe-87MNGm3uwyxMegjAuJ8d-9LAvyg6Zo2HBVvYpDpAH9A7xtVQjm-aYiKdVjUskQpLUdSx5BkUX_4qGc1BFLv2_eRgJvxxozCFL5kQmg3xslQ4nA5grUcQqw9JnYv5gaoi8F6zQ6E2fr_MmMvawaNCvM-LjVs3pMqduD3vB145rvh41rei1rToF_bN44KYJB-HWc4AZG1zMac3OtFWlyb_WRLGZTxK7FjLRoMlPkOKPk_0lxq4s3xeZbi-1ZnPTCyp5vMo42Ny3I8_1LG9YLVBErUZAKJ4XCLnPDckWsQTbGGEeOCdpDOe3Z10rK-el1A_rI4YpDa1Pcf5BLPSsparVXF2pueOvXE7_lorSNKGw7rVlRrCGkig4cNvqp11mKd4uANYcBw4jC6q_uV16jb0C96b07R_A5IKgXLi2tOJpuNWaQgAZxxFyA2dk904CpDyizjkwNsbQ3xdJmYYDiRTaRXGvfMts45kJGJwOj8HvJCUlp2Z8ksHoGJwcREZGr5kktNl4FvKnsdO56sOnoLmPOcGK0DTGeEt24lAmYnf5az_CTtANi2WHTCSlsRRu5Sof-9ehIZ5SOFhKXyjkkpHr7FXA2fJwk3Oa5ayFfhJDH3vOS2EFxAqyV2vS0Rkzc_M_1iJKBY6iCqqnqRqhCP0CTUCjvRDbxn99ya4tC4FZVL1UqNeXnyYo9QQXjW8iPJCS3ZLlJLPlpII1JkYsfGpC1zZ4Esf55ZU7s5SKZNves8ad8HSewOg9p6iGhnItFPXpyb6i2ET1jZpsbK7uZErqDf6Uzw1RwMNzsq79f19t7jad69qwtCsiKtBeJYk8Xg8ZdC5kthylWZnbA2CikruJQURCIaHbyZn0pYiShqjkIfEF3nBp1KrXfFAs1ZvAHFD7iBd83w0ZJkXLDQy3He0AxoQUS-Em9qrrtrAZkf8cI_wGOkfBVqZHmLKP_p67HALzK5QUyJWl8VjOz6X38E7HJxURKkfDcGUONw" 
    DROPBOX_FILE_PATH = "/Gestion Analitica/Alvaro/GestionDiaria.xlsx" # Tu ruta de archivo
    
    dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
    
    try:
        # 1. Intentar descargar el archivo actual
        _, res = dbx.files_download(DROPBOX_FILE_PATH)
        df_actual = pd.read_excel(io.BytesIO(res.content))
        # 2. Unir los datos nuevos
        df_final = pd.concat([df_actual, df_nuevo], ignore_index=True)
    except:
        # Si el archivo no existe o hay error, el nuevo es el inicio
        df_final = df_nuevo

    # 3. Guardar y subir (USANDO EL MOTOR ESTÁNDAR)
    output = io.BytesIO()
    # Hemos quitado engine='xlsxwriter' para evitar el error de "No module named"
    with pd.ExcelWriter(output) as writer:
        df_final.to_excel(writer, index=False)
    
    dbx.files_upload(output.getvalue(), DROPBOX_FILE_PATH, mode=dropbox.files.WriteMode.overwrite)

# ------------------------------------

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Gestión de Ventas", layout="wide")

# --- 2. TÍTULO E INTERFAZ ---
st.title("📝 Registro de Ventas")
st.markdown("Los campos marcados con **(*)** son obligatorios.")

# --- 3. DISEÑO DE COLUMNAS ---
col1, col2 = st.columns(2)

with col1:
    zonal = st.selectbox("ZONAL", ["TRUJILLO", "LIMA NORTE", "LIMA SUR - FIJA", "LIMA ESTE", "HUANCAYO", "CAJAMARCA", "TARAPOTO"])
    
    dni_vendedor = st.text_input("N° DOCUMENTO VENDEDOR *", max_chars=11)
    if dni_vendedor and not dni_vendedor.isdigit():
        st.error("⚠️ Solo números en DNI Vendedor")

    nombre_cliente = st.text_input("NOMBRE DE CLIENTE *").upper()
    
    dni_cliente = st.text_input("N° DE DOCUMENTO (CLIENTE) *", max_chars=11)
    if dni_cliente and not dni_cliente.isdigit():
        st.error("⚠️ Solo números en DNI Cliente")
        
    email_cliente = st.text_input("EMAIL DE CLIENTE").lower()
    
    tipo_op = st.selectbox("Tipo de Operación", ["CAPTACIÓN", "MIGRACIÓN", "COMPLETA TV", "COMPLETA MT", "COMPLETA BA"])
    
    producto = st.selectbox("PRODUCTO", ["NAKED", "DUO INT + TV", "DUO TV", "DUO BA", "TRIO"])
    
    cod_fe = st.text_input("Código FE").upper()
    
    pedido = st.text_input("N° de Pedido *", max_chars=10)
    if pedido and not pedido.isdigit():
        st.error("⚠️ El N° de Pedido debe ser solo números")

with col2:
    detalle = st.selectbox("DETALLE", ["VENTA FIJA", "NO-VENTA", "CLIENTE AGENDADO", "REFERIDO", "PRE-VENTA"])
    
    direccion = st.text_input("DIRECCION DE INSTALACION").upper()
    
    contacto1 = st.text_input("N° DE CONTACTO DE CLIENTE 1 *", max_chars=9)
    if contacto1:
        if not contacto1.isdigit():
            st.error("⚠️ El contacto debe ser solo números")
        elif len(contacto1) != 9:
            st.warning("⚠️ El número debe tener 9 dígitos")
            
    contacto2 = st.text_input("N° DE CONTACTO DE CLIENTE 2", max_chars=9)
    if contacto2 and not contacto2.isdigit():
        st.error("⚠️ Solo números en contacto 2")
        
    venta_piloto = st.radio("¿Venta Piloto?", ["SI", "NO"], horizontal=True)
    
    # Lógica dinámica para Motivo de No Venta
    motivo_no_venta = ""
    if detalle == "NO-VENTA":
        motivo_no_venta = st.selectbox("INDICAR MOTIVO DE NO VENTA *", ["", "CUENTA CON SERVICIO DE COMPETENCIA", "CLIENTE MOVISTAR", "MALA EXPERIENCIA", "CARGO FIJO INSUFICIENTE"])
        if motivo_no_venta == "":
            st.warning("⚠️ Debe seleccionar un motivo")
            
    nom_referido = st.text_input("NOMBRE Y APELLIDO DE REFERIDO").upper()
    
    cont_referido = st.text_input("N° DE CONTACTO REFERIDO", max_chars=9)
    if cont_referido and not cont_referido.isdigit():
        st.error("⚠️ Solo números en contacto referido")

# --- 4. BOTÓN DE ENVÍO Y LÓGICA FINAL ---
st.markdown("---")
enviado = st.button("🚀 Enviar Registro", use_container_width=True)

if enviado:
    # RECOLECCIÓN DE ERRORES
    errores = []
    
    # Validar Obligatorios
    if not dni_vendedor: errores.append("DNI Vendedor")
    if not nombre_cliente: errores.append("Nombre de Cliente")
    if not dni_cliente: errores.append("DNI Cliente")
    if not pedido: errores.append("N° de Pedido")
    if not contacto1 or len(contacto1) != 9: errores.append("Contacto 1 (debe ser de 9 dígitos)")
    
    # Validar Formatos Numéricos
    if dni_vendedor and not dni_vendedor.isdigit(): errores.append("DNI Vendedor (formato incorrecto)")
    if dni_cliente and not dni_cliente.isdigit(): errores.append("DNI Cliente (formato incorrecto)")
    if pedido and not pedido.isdigit(): errores.append("Pedido (formato incorrecto)")
    
    # Validar Condicional
    if detalle == "NO-VENTA" and not motivo_no_venta:
        errores.append("Motivo de No Venta")

    if errores:
        st.error("❌ No se puede guardar. Corrija los siguientes puntos:")
        for err in errores:
            st.write(f"- {err}")
    else:
        # PROCESO DE GUARDADO
        zona_horaria = pytz.timezone('America/Lima')
        # Capturar la hora actual en esa zona específica
        ahora = datetime.now(zona_horaria)
        NuevosDatos = {
            "Marca temporal": ahora.strftime("%d/%m/%Y %H:%M:%S"),
            "ZONAL": zonal,
            "N° DOCUMENTO VENDEDOR": dni_vendedor,
            "DETALLE": detalle,
            "Tipo de Operación": tipo_op,
            "NOMBRE DE CLIENTE": nombre_cliente,
            "N° DE DOCUMENTO": dni_cliente,
            "DIRECCION DE INSTALACION": direccion,
            "EMAIL DE CLIENTE": email_cliente,
            "N° DE CONTACTO DE CLIENTE 1": contacto1,
            "N° DE CONTACTO DE CLIENTE 2": contacto2,
            "PRODUCTO": producto,
            "Código FE": cod_fe,
            "N° de Pedido": pedido,
            "¿Venta Piloto?": venta_piloto,
            "INDICAR MOTIVO DE NO VENTA": motivo_no_venta,
            "NOMBRE Y APELLIDO DE REFERIDO": nom_referido,
            "N° DE CONTACTO REFERIDO": cont_referido,
            "Fecha": ahora.strftime("%d/%m/%Y"),
            "Hora": ahora.strftime("%H:%M:%S")
        }

        try:
            # Convertir a DataFrame y subir
            df_final = pd.DataFrame([NuevosDatos])
            save_to_dropbox(df_final) # Asumiendo que tu función ya está definida arriba
            
            st.success("✅ ¡Registro guardado exitosamente en Dropbox!")
            st.balloons()
            
            # Limpiar formulario reiniciando la app tras una breve pausa
            time.sleep(2)
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error al guardar: {e}")
