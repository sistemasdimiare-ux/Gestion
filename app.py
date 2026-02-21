# Conector Streamlit Cloud, el puente entre un movil y nuestro motor

import streamlit as st
import pandas as pd
import dropbox
from dropbox import Dropbox
from datetime import datetime
import io

# --- 1. CONFIGURACIÓN DE CONEXIÓN ---
# Reemplaza el token si generas uno nuevo, de lo contrario deja el actual.
DROPBOX_TOKEN = "sl.u.AGW0oa1DJ2do6TMwxIDdwCnbQbshA5kP7eTXTdecKhGvPh6ayjw99J4NpejDTR68Og34WqHiLLq63SKdik9f1RcJbgYuunkUIf0zvRwMelIvvfLbxavtGGn_Hqdv7NXq9suQmIYlivKOpWXXjJ4qP9RD98VmLT6uc8UrQGG77cbQ66LzWZLKK8Uzp-BvjT2dOAC-yGv862dBKI5I0QrmJoK2rt4PXv9uJDLXn996P_Q9pLHUs2BWSnipRUBOrP-1SbTdU7CDFPkPC62FA9SUy8L1cBwhn6jFXqdrspiI2wWLQHwaIxEtRxw7StXi3n875mRc9xvL8tzjx-gMm43lgYkFKhp6Jy2x2rpCP2ut89XZjqUUzAxV7D2ZwZ-n_2C9mccbImiUujFnnSRI-VF6SPB4VovVaLVGwH9iAGyO8n7mFU_tfLdbuw0D2H824pYrF9VrQ8huKTP9bW_v0Fod45FkWhB5LM6p4rPrJQkANpiA94LA5EypxonEWczlbtrUZ3keb_Sy5fmTNzdgfFumbXffwcI4nCgEr5idXh-C9zkOQ-OontU0P2Z0QF6RAMKlfmaNCE1-I3_IECLNR05lDgf3r_gNIv4CIaHnfta7RFZSVdD34mHI1IlWYPCJSHUprczRe7tAiF-vhBejIvfFIrruXuUYZkuOz8tJC2fJkPcr0CkMzuvAQYZEYIC-VcAaKGYPFOK7SFPZumztWvJLWrP77XYZ0Dy97MmUrcOi2rnxpsfYe2m8Hk4L9OxZsxW8eSDEHjbaslj5e-mRVcRjK2CKxkC1YKCcgBFsAY0e8ya81bfqHmLYDZDmCf_slVh7YSJHkSvVoSM73zr4gY6TPf74QWU44GSdq7qlQpOIHzae9C4tx1s_p5IxqfJRKvAgA6YCelhSzwiFEs5W8sOnXAavuGfO8FcNjEb5Dk0GfmMEReRqyPid-eh7iHnRJ19yrTKNqm27Qc05qXQTsyzMQUma2uTDF3YdeKjS5gsypZEsJRtDPgkqq2ngst4usUidNa_Zel811DZebSnQ8JA8gNoM6TMsSss7C-tPQbY-amxyyPPNy7rQNpqow5dY9eOnROuOAyu50rB3pCH5vo-2-GSzULlsruHfiCqNu0LNjDWTkrK0xz1ywOFFNDROJ8K_fZM3jCkpc6BHOtp373yH38gA5CKGh8zylFMeK7NaOaeBFBO503US47E9Zjh155qCgpPqs-fLmKPRuT6G6-wLyZ1vMZLVEbCV2dr6ZyWUf0jcIILXWA-TXPZksGaZf03O-u8Cuq2JMXyDDhWHhO5B1rA3NRTkXSl-UmAbWZMYztdc9ps9GwCAKIvCoNxMvq-okJc" 

# Ruta adaptada a tu estructura de carpetas en Dropbox
EXCEL_FILE_PATH = "/Gestion Analitica/Alvaro/GestionDiaria.xlsx"

# --- 2. FUNCIÓN PARA GUARDAR (Debe ir antes del formulario) ---
def save_to_dropbox(df_new):
    dbx = Dropbox(DROPBOX_TOKEN)
    try:
        # Intentar descargar el archivo existente
        metadata, res = dbx.files_download(EXCEL_FILE_PATH)
        df_existing = pd.read_excel(io.BytesIO(res.content))
        # Unir datos nuevos debajo de los anteriores
        df_final = pd.concat([df_existing, df_new], ignore_index=True)
    except Exception:
        # Si el archivo no existe o hay error, el nuevo será el inicial
        df_final = df_new

    # Preparar el archivo Excel en memoria
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_final.to_excel(writer, index=False)
    
    # Subir y sobrescribir en Dropbox
    dbx.files_upload(
        output.getvalue(), 
        EXCEL_FILE_PATH, 
        mode=dropbox.files.WriteMode.overwrite
    )

# --- 3. INTERFAZ DEL FORMULARIO ---
st.set_page_config(page_title="Gestión de Ventas", layout="wide")
st.title("📝 Registro de Gestión de Ventas")
st.markdown("Complete los datos del cliente y la operación:")

with st.form("main_form", clear_on_submit=True):
    col1, col2 = st.columns(2)

    
    with col1:
        zonal = st.selectbox("ZONAL", ["TRUJILLO", "LIMA NORTE", "LIMA SUR - FIJA", "LIMA ESTE", "HUANCAYO", "CAJAMARCA", "TARAPOTO"])
         # Validación de solo números para DNI Vendedor
        dni_vendedor = st.text_input("N° DOCUMENTO VENDEDOR", max_chars=11)
        
        # Formateo automático a MAYÚSCULAS para el nombre
        nombre_cliente = st.text_input("NOMBRE DE CLIENTE").upper()
        
        dni_cliente = st.text_input("N° DE DOCUMENTO (CLIENTE)", max_chars=11)
        email_cliente = st.text_input("EMAIL DE CLIENTE").lower()
        tipo_op = st.selectbox("Tipo de Operación", ["CAPTACIÓN", "MIGRACIÓN", "COMPLETA TV", "COMPLETA MT", "COMPLETA BA"])
        producto = st.selectbox("PRODUCTO", ["NAKED", "DUO INT + TV", "DUO TV", "DUO BA", "TRIO"])
        cod_fe = st.text_input("Código FE").upper()
        pedido = st.text_input("N° de Pedido", max_chars=10)


    with col2:
        detalle = st.selectbox("DETALLE", ["VENTA FIJA", "NO-VENTA", "CLIENTE AGENDADO", "REFERIDO", "PRE-VENTA"])
        direccion = st.text_input("DIRECCION DE INSTALACION").upper()
        contacto1 = st.text_input("N° DE CONTACTO DE CLIENTE 1", max_chars=9)
        contacto2 = st.text_input("N° DE CONTACTO DE CLIENTE 2", max_chars=9)
        venta_piloto = st.radio("¿Venta Piloto?", ["SI", "NO"], horizontal=True)
      # Lógica: Solo pedir motivo si es NO-VENTA (se puede hacer fuera del form para que sea dinámico, 
        # pero dentro del form lo manejamos como validación al enviar)
        motivo_no_venta = st.selectbox("INDICAR MOTIVO DE NO VENTA", ["CUENTA CON SERVICIO DE COMPETENCIA", "CLIENTE MOVISTAR", "MALA EXPERIENCIA", "CARGO FIJO INSUFICIENTE"])        
        nom_referido = st.text_input("NOMBRE Y APELLIDO DE REFERIDO").upper()
        cont_referido = st.text_input("N° DE CONTACTO REFERIDO", max_chars=9)

    # Botón de envío
    enviado = st.form_submit_button("Enviar Registro")

# --- LÓGICA DE VALIDACIÓN ANTES DE GUARDAR ---
if enviado:
    # 1. Validar que los campos de números sean realmente números
    if not dni_vendedor.isdigit() or not dni_cliente.isdigit():
        st.error("❌ Los campos de Documento (Vendedor/Cliente) deben contener solo números.")
    
    # 2. Validar longitud mínima de DNI (por ejemplo 8 dígitos)
    elif len(dni_cliente) < 8:
        st.error("❌ El N° de Documento del cliente debe tener al menos 8 dígitos.")
        
    # 3. Validar campos obligatorios
    elif not nombre_cliente or not pedido:
        st.error("❌ El Nombre del Cliente y el N° de Pedido son obligatorios.")
    
    # 4. Validar si es NO-VENTA que indique el motivo
   elif detalle == "NO-VENTA" and motivo_no_venta == "":
        st.error("❌ Por favor, selecciona un motivo de la lista para la NO-VENTA.")
    else:
        # Si pasa todas las validaciones, procede a guardar (aquí iría tu lógica de guardado)
        ahora = datetime.now()
        # ... (resto de tu código de guardado) ...
        st.success("✅ ¡Registro validado y guardado!")
        
# --- 4. LÓGICA AL PRESIONAR ENVIAR ---
if enviado:
    if not dni_vendedor or not nombre_cliente:
        st.warning("⚠️ El DNI del Vendedor y el Nombre del Cliente son obligatorios.")
    else:
        ahora = datetime.now()
        
        # Diccionario con las 20 columnas exactas
        nuevos_datos = {
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

        df_para_subir = pd.DataFrame([nuevos_datos])
        
        try:
            # Aquí llamamos a la función que definimos arriba
            save_to_dropbox(df_para_subir)
            st.success("✅ ¡Registro guardado exitosamente en Dropbox!")
            st.balloons()
        except Exception as e:
            st.error(f"❌ Error al conectar con Dropbox: {e}")
