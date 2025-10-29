import streamlit as st
st.set_page_config(layout="centered")
st.title("🐛 DEBUG ULTRA-CORTO")

# Estado
if "user" not in st.session_state:
    st.session_state.user = {"peso": 92.1, "template": 92.1}

# Mostrar estado
st.write("**ACTUAL:**", st.session_state.user)

# Cambiar datos  
nuevo_peso = st.number_input("NUEVO PESO", value=st.session_state.user["peso"])
if st.button("💾 GUARDAR"):
    st.session_state.user = {"peso": nuevo_peso, "template": nuevo_peso}
    st.rerun()

# Test simple
peso_actual = st.session_state.user["peso"]
template = st.session_state.user["template"]
ratio = peso_actual / template

st.write(f"**Ratio:** {peso_actual} / {template} = {ratio}")

# Resultado
if ratio == 1.0:
    st.error("❌ NO CAMBIA - ratio = 1.0")
else:
    st.success(f"✅ SI CAMBIA - ratio = {ratio}")
    st.write(f"160g pollo → {int(160 * ratio)}g pollo")
