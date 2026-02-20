# Conector Streamlit Cloud, el puente entre un movil y nuestro motor

import streamlit as st
import pandas as pd
import dropbox==11.36.0
from dropbox import Dropbox
from datetime import datetime
import io

# --- 1. CONFIGURACIÓN DE CONEXIÓN ---
# Reemplaza el token si generas uno nuevo, de lo contrario deja el actual.
DROPBOX_TOKEN = "TU_TOKEN_AQUÍ" 

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
        dni_vendedor = st.text_input("N° DOCUMENTO VENDEDOR")
        nombre_cliente = st.text_input("NOMBRE DE CLIENTE")
        dni_cliente = st.text_input("N° DE DOCUMENTO (CLIENTE)")
        email_cliente = st.text_input("EMAIL DE CLIENTE")
        tipo_op = st.text_input("Tipo de Operación")
        producto = st.text_input("PRODUCTO")
        cod_fe = st.text_input("Código FE")
        pedido = st.text_input("N° de Pedido")

    with col2:
        detalle = st.text_area("DETALLE")
        direccion = st.text_input("DIRECCION DE INSTALACION")
        contacto1 = st.text_input("N° DE CONTACTO DE CLIENTE 1")
        contacto2 = st.text_input("N° DE CONTACTO DE CLIENTE 2")
        venta_piloto = st.radio("¿Venta Piloto?", ["SI", "NO"], horizontal=True)
        motivo_no_venta = st.text_input("INDICAR MOTIVO DE NO VENTA")
        nom_referido = st.text_input("NOMBRE Y APELLIDO DE REFERIDO")
        cont_referido = st.text_input("N° DE CONTACTO REFERIDO")

    # Botón de envío
    enviado = st.form_submit_button("Enviar Registro")

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
