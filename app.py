import streamlit as st

st.set_page_config(page_title="DEBUG", layout="centered")
st.title("🔍 DEBUG - Porciones")

# Estado inicial
if "user" not in st.session_state:
    st.session_state.user = {
        "peso": 92.1,
        "template_weight": 92.1,
        "grasa_pct": 37.9,
        "template_fat": 37.9
    }

# Mostrar estado ACTUAL
st.header("📊 ESTADO ACTUAL")
st.write("**Usuario:**", st.session_state.user)

# Modificar datos
st.header("✏️ CAMBIAR DATOS")
nuevo_peso = st.number_input("NUEVO PESO", value=st.session_state.user["peso"], step=0.1)
nueva_grasa = st.number_input("NUEVA GRASA", value=st.session_state.user["grasa_pct"], step=0.1)

if st.button("💾 GUARDAR"):
    st.session_state.user.update({
        "peso": nuevo_peso,
        "grasa_pct": nueva_grasa,
        "template_weight": nuevo_peso,  # ¡IMPORTANTE!
        "template_fat": nueva_grasa     # ¡IMPORTANTE!
    })
    st.success("✅ Guardado!")
    st.rerun()

# TEST DIRECTO
st.header("🧪 TEST DIRECTO")

# Receta de prueba
receta = {"protein_food_g": 160, "carb_crudo_g": 40, "kcal": 620}

# Cálculo manual
st.subheader("CÁLCULO MANUAL:")
st.write(f"Peso actual: {st.session_state.user['peso']}")
st.write(f"Template weight: {st.session_state.user['template_weight']}")

weight_ratio = st.session_state.user["peso"] / st.session_state.user["template_weight"]
st.write(f"**weight_ratio = {weight_ratio}**")

if weight_ratio == 1.0:
    st.error("❌ PROBLEMA: weight_ratio = 1.0 (NO cambia)")
else:
    st.success(f"✅ OK: weight_ratio = {weight_ratio} (SÍ cambia)")

# Aplicar escalado
escala = max(0.5, min(2.0, weight_ratio))
proteina_original = receta["protein_food_g"]
proteina_escalada = int(proteina_original * escala)

carbos_original = receta["carb_crudo_g"] 
carbos_escalados = int(carbos_original * escala)

st.subheader("RESULTADOS:")
st.write(f"Proteína: {proteina_original}g → {proteina_escalada}g")
st.write(f"Carbos: {carbos_original}g → {carbos_escalados}g")

if proteina_original == proteina_escalada:
    st.error("❌ LAS CANTIDADES NO CAMBIAN")
else:
    st.success("✅ LAS CANTIDADES SÍ CAMBIAN")

# Debug extra
st.header("🔧 DEBUG EXTRA")
st.write("**Session state completo:**", st.session_state)
