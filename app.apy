import streamlit as st

st.set_page_config(layout="centered")
st.title("🏋️ Nutrición - SOLUCIÓN DEFINITIVA")

# Estado inicial CON template_weight FIJO
if "user" not in st.session_state:
    st.session_state.user = {
        "peso": 92.1,
        "template_weight": 92.1,  # ← VALOR FIJO que NO cambia
        "grasa_pct": 37.9,
        "template_fat": 37.9,     # ← VALOR FIJO que NO cambia
        "objetivo": "Recomposición"
    }

st.write("**ESTADO ACTUAL:**")
st.json(st.session_state.user)

# Inputs para modificar SOLO peso y grasa actual
nuevo_peso = st.number_input("PESO ACTUAL (kg)", 
                            value=st.session_state.user["peso"], 
                            step=0.1,
                            key="input_peso")

nueva_grasa = st.number_input("GRASA ACTUAL (%)", 
                             value=st.session_state.user["grasa_pct"], 
                             step=0.1,
                             key="input_grasa")

# BOTÓN CORREGIDO: Solo actualiza peso y grasa, NO los templates
if st.button("💾 ACTUALIZAR PESO ACTUAL", type="primary"):
    st.session_state.user["peso"] = float(nuevo_peso)
    st.session_state.user["grasa_pct"] = float(nueva_grasa)
    # NO actualizar template_weight y template_fat
    st.success("✅ ¡Peso actualizado! Las cantidades DEBEN cambiar ahora.")
    st.rerun()

# CÁLCULO Y RESULTADOS
st.header("🧪 RESULTADOS")

peso_actual = st.session_state.user["peso"]
template_peso = st.session_state.user["template_weight"]
weight_ratio = peso_actual / template_peso

st.write(f"**CÁLCULO:** {peso_actual} / {template_peso} = {weight_ratio}")

if weight_ratio == 1.0:
    st.error("❌ PROBLEMA: weight_ratio = 1.0 (NO hay cambio)")
else:
    st.success(f"✅ FUNCIONA: weight_ratio = {weight_ratio} (SÍ hay cambio)")

# EJEMPLO PRÁCTICO
pollo_original = 160
pollo_escalado = int(pollo_original * weight_ratio)

arroz_original = 40  
arroz_escalado = int(arroz_original * weight_ratio)

st.write("**CANTIDADES DE COMIDA:**")
st.write(f"- Pollo: {pollo_original}g → {pollo_escalado}g")
st.write(f"- Arroz: {arroz_original}g → {arroz_escalado}g")

# BOTÓN PARA RESET TEMPLATE
if st.button("🔄 Establecer peso actual como nueva referencia"):
    st.session_state.user["template_weight"] = st.session_state.user["peso"]
    st.session_state.user["template_fat"] = st.session_state.user["grasa_pct"]
    st.success("✅ Nuevo peso establecido como referencia")
    st.rerun()
