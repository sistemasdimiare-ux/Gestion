import streamlit as st
import pandas as pd
from datetime import datetime
import time
# Nota: Asegúrate de tener importada tu función save_to_dropbox y la librería de Dropbox

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
