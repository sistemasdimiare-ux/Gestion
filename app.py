import streamlit as st
import pandas as pd
from datetime import datetime
import time
# Nota: Asegúrate de tener importada tu función save_to_dropbox y la librería de Dropbox

import dropbox # Asegúrate de tener esta línea al inicio
import io

# --- ESTA ES LA FUNCIÓN QUE FALTA ---
def save_to_dropbox(df_nuevo):
    # Reemplaza con tu Token real
    DROPBOX_ACCESS_TOKEN = "sl.u.AGW0oa1DJ2do6TMwxIDdwCnbQbshA5kP7eTXTdecKhGvPh6ayjw99J4NpejDTR68Og34WqHiLLq63SKdik9f1RcJbgYuunkUIf0zvRwMelIvvfLbxavtGGn_Hqdv7NXq9suQmIYlivKOpWXXjJ4qP9RD98VmLT6uc8UrQGG77cbQ66LzWZLKK8Uzp-BvjT2dOAC-yGv862dBKI5I0QrmJoK2rt4PXv9uJDLXn996P_Q9pLHUs2BWSnipRUBOrP-1SbTdU7CDFPkPC62FA9SUy8L1cBwhn6jFXqdrspiI2wWLQHwaIxEtRxw7StXi3n875mRc9xvL8tzjx-gMm43lgYkFKhp6Jy2x2rpCP2ut89XZjqUUzAxV7D2ZwZ-n_2C9mccbImiUujFnnSRI-VF6SPB4VovVaLVGwH9iAGyO8n7mFU_tfLdbuw0D2H824pYrF9VrQ8huKTP9bW_v0Fod45FkWhB5LM6p4rPrJQkANpiA94LA5EypxonEWczlbtrUZ3keb_Sy5fmTNzdgfFumbXffwcI4nCgEr5idXh-C9zkOQ-OontU0P2Z0QF6RAMKlfmaNCE1-I3_IECLNR05lDgf3r_gNIv4CIaHnfta7RFZSVdD34mHI1IlWYPCJSHUprczRe7tAiF-vhBejIvfFIrruXuUYZkuOz8tJC2fJkPcr0CkMzuvAQYZEYIC-VcAaKGYPFOK7SFPZumztWvJLWrP77XYZ0Dy97MmUrcOi2rnxpsfYe2m8Hk4L9OxZsxW8eSDEHjbaslj5e-mRVcRjK2CKxkC1YKCcgBFsAY0e8ya81bfqHmLYDZDmCf_slVh7YSJHkSvVoSM73zr4gY6TPf74QWU44GSdq7qlQpOIHzae9C4tx1s_p5IxqfJRKvAgA6YCelhSzwiFEs5W8sOnXAavuGfO8FcNjEb5Dk0GfmMEReRqyPid-eh7iHnRJ19yrTKNqm27Qc05qXQTsyzMQUma2uTDF3YdeKjS5gsypZEsJRtDPgkqq2ngst4usUidNa_Zel811DZebSnQ8JA8gNoM6TMsSss7C-tPQbY-amxyyPPNy7rQNpqow5dY9eOnROuOAyu50rB3pCH5vo-2-GSzULlsruHfiCqNu0LNjDWTkrK0xz1ywOFFNDROJ8K_fZM3jCkpc6BHOtp373yH38gA5CKGh8zylFMeK7NaOaeBFBO503US47E9Zjh155qCgpPqs-fLmKPRuT6G6-wLyZ1vMZLVEbCV2dr6ZyWUf0jcIILXWA-TXPZksGaZf03O-u8Cuq2JMXyDDhWHhO5B1rA3NRTkXSl-UmAbWZMYztdc9ps9GwCAKIvCoNxMvq-okJc" 
    DROPBOX_FILE_PATH = "/Gestion Analitica/Alvaro/GestionDiaria.xlsx" # Tu ruta de archivo
    
    dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
    
    try:
        # 1. Intentar descargar el archivo actual
        _, res = dbx.files_download(DROPBOX_FILE_PATH)
        df_actual = pd.read_excel(io.BytesIO(res.content))
        # 2. Unir los datos nuevos
        df_final = pd.concat([df_actual, df_nuevo], ignore_index=True)
    except:
        # Si el archivo no existe, el nuevo es el primero
        df_final = df_nuevo

    # 3. Guardar y subir
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
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
        ahora = datetime.now()
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
