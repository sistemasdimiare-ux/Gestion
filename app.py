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
    DROPBOX_ACCESS_TOKEN ="sl.u.AGWYthgomNUOSbV15uZ057cb4HSoEX3LaqH7j8IC-3gs-rgkWhj4Q5MZiH7TxvRk5eTpcGUmFNuID4SUnTZxz0bcHTpskJS2LEQC-gdzJzhU-IJQQwwvIhiXbk91Gd-TU-wByERoXTqb-mcyn-UMDRdqIaBr7RUGBdqxHMlyNQCeSc8-Cgagki_3cUmz9JqirDkPA0KJVOfr_erZgptSd7tLQOrQi4ppZR8rUgy6sLsEv5yjNWcvY51kUFVGsFZxUZ8BteJJXciK5ng8QfpfrUU2TLaVk2KNlrHq5rFmQVJ9OBrp0D2HgVWiREMuUhRQDirv-0B7cP_VNntnG2zm68ZBo9-n_CaJU3IYWnZfkZUxSjU_RLWEMFd24Iw8lTK82BzFPEPPzq6yrjYQ9g937Ng3KFnk6I0AjHLbY_LQsFlNl6i3T5YZZI8hLwGxnPa5Je9WpWcC143tklYpfYMK_R6CIQnQU0r_8xvJgYkYYmvQB46XdxJ_fYjNktC-kMDEXd1AIsxgrEsdRhJf7QS0DVpXBefxDQZI1ToNZBegzufJ1oiQ7DgfSlDegUPeclk_M6FkXuNkmhQjgQ9WlvErtxDB52a_PTDUug_Votx7nSG9k0tYbVfMWljG3EXONloC11bF-pIuusnzti9Sj0woKUdORIrJYFZOhs8vlpxzMIWnx7C8XuofdmKEur_-L1xOkffbj0epMUNyTG2KVYNZMt-QSDQSjVlDTWTNQnxBaZ86D32JTbt-y0eWmTApwjOiU5Ja0U1Cb_SU0CLbjiJL9bjPllRWrFhUaQ8rWEEkmIM4nve1Axq7EPAjUSdNyNy97loznUdBgTiF6xyjl7WtLAfMGuX4nTyqoNrF7eax4ufdOBGfyWUFY40K-LL_XaG4BMCOTe3SfWl9YyQZxKZCG9J8KeQeKv0e6tP6gFQ4pJ_7QQr2_gB2iMY2xF1u1oEuGFW_AwaB34RZqaJrXZlYtPdv2LAdCmwlXZ8z8jJrha8nYcQNauLtHwMMxpt9p58VCCvtcZSMWxialCYAuIUZDs0NcsYBOQaA-T5m0u0b-kEvL1K1xCGuB7UnIqAurFXvScAFGeBczLIRe-_Oa6hMq8MhmWAwzXs8EfehE09FbFAM_FzYRWCbxTJNPaF4BZ8Wdd3LFX5tkawe_xzMwsidOEEfq0TLzQ28KgFtizqG9FEX0keqC3h-P4oauEhac1-SxtbXmDfBMykEWm7yJa0ArJQSnqLd1BGjsCp-J-4D0wqvOGQzw5jDd-8NenNwQ1XNPe85GVZ2VNYI4qgAuPX65nrDB8_JvLfG4oFcsIz0cib812SHYW3ecQ2CEVewCgVJAAU"
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

# --- 2. LÓGICA DE REINICIO ---
if "count" not in st.session_state:
    st.session_state.count = 0

def clean_and_refresh():
    st.session_state.count += 1
    st.rerun()

# --- 3. BARRA LATERAL ---
st.sidebar.title("👤 Datos del Vendedor")
zonal = st.sidebar.selectbox("ZONAL", ["TRUJILLO", "LIMA NORTE", "LIMA SUR - FIJA", "LIMA ESTE", "HUANCAYO", "CAJAMARCA", "TARAPOTO"])
dni_vendedor = st.sidebar.text_input("N° DOCUMENTO VENDEDOR", max_chars=11)

# --- 4. FORMULARIO ---
st.title("📝 Registro de Gestión de Ventas")

with st.form(key=f"form_{st.session_state.count}"):
    col1, col2 = st.columns(2)

    with col1:
        nombre_cliente = st.text_input("NOMBRE DE CLIENTE").upper()
        dni_cliente = st.text_input("N° DE DOCUMENTO (CLIENTE)", max_chars=11)
        tipo_op = st.selectbox("Tipo de Operación", ["SELECCIONA","CAPTACIÓN", "MIGRACIÓN", "COMPLETA TV", "COMPLETA MT", "COMPLETA BA"])
        producto = st.selectbox("PRODUCTO", ["SELECCIONA", "NAKED", "DUO INT + TV", "DUO TV", "DUO BA", "TRIO"])
        pedido = st.text_input("N° de Pedido", max_chars=10)

    with col2:
        detalle = st.selectbox("DETALLE *", ["SELECCIONA", "VENTA FIJA", "NO-VENTA", "CLIENTE AGENDADO", "REFERIDO", "PRE-VENTA"])
        motivo_no_venta = st.selectbox("INDICAR MOTIVO DE NO VENTA", ["", "COMPETENCIA", "CLIENTE MOVISTAR", "MALA EXPERIENCIA", "CARGO FIJO INSUFICIENTE"])
        direccion = st.text_input("DIRECCION DE INSTALACION").upper()
        contacto1 = st.text_input("N° DE CONTACTO 1", max_chars=9)
        venta_piloto = st.radio("¿Venta Piloto?", ["SI", "NO"], horizontal=True)

    enviado = st.form_submit_button("🚀 ENVIAR REGISTRO", use_container_width=True)

# --- 5. LÓGICA DE VALIDACIÓN (LA CLAVE) ---
if enviado:
    errores = []
    
    # Única validación que SIEMPRE corre
    if detalle == "SELECCIONA": 
        errores.append("Debe elegir un DETALLE")

    # SI ES NO-VENTA: Solo pedimos el motivo. Ignoramos Nombre, DNI y lo demás.
    if detalle == "NO-VENTA":
        if not motivo_no_venta:
            errores.append("Para NO-VENTA, el Motivo es obligatorio")
    
    # SI NO ES NO-VENTA: Pedimos todo lo obligatorio de siempre
    else:
        if not nombre_cliente: errores.append("Nombre de Cliente")
        if not dni_cliente: errores.append("DNI Cliente")
        if tipo_op == "SELECCIONA": errores.append("Tipo de Operación")
        if not pedido: errores.append("N° de Pedido")

    if errores:
        st.error("⚠️ Error de validación:")
        for e in errores: st.write(f"- {e}")
    else:
        # GUARDAR
        zona_pe = pytz.timezone('America/Lima')
        ahora = datetime.now(zona_pe)
        
        datos = {
            "Marca temporal": ahora.strftime("%d/%m/%Y %H:%M:%S"),
            "ZONAL": zonal,
            "N° DOCUMENTO VENDEDOR": dni_vendedor,
            "DETALLE": detalle,
            "NOMBRE DE CLIENTE": nombre_cliente if nombre_cliente else "N/A",
            "N° DE DOCUMENTO": dni_cliente if dni_cliente else "N/A",
            "INDICAR MOTIVO DE NO VENTA": motivo_no_venta if detalle == "NO-VENTA" else "N/A",
            "Tipo de Operación": tipo_op if detalle != "NO-VENTA" else "N/A",
            "N° de Pedido": pedido if detalle != "NO-VENTA" else "0",
            "¿Venta Piloto?": venta_piloto if detalle != "NO-VENTA" else "NO",
            "Fecha": ahora.strftime("%d/%m/%Y"),
            "Hora": ahora.strftime("%H:%M:%S")
        }

        try:
            save_to_dropbox(pd.DataFrame([datos]))
            st.success("✅ ¡Guardado!")
            st.balloons()
            time.sleep(1.5)
            clean_and_refresh()
        except Exception as e:
            st.error(f"❌ Error: {e}")
